import csv
import time
import requests
from bs4 import BeautifulSoup

# Global configurations
BASE_URL = "https://www.mcdonalds.com"
START_URL = "https://www.mcdonalds.com/ca/en-ca/full-menu.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

# URL substrings that identify drink products
DRINK_URL_KEYWORDS = [
    "coffee", "latte", "cappuccino", "mocha", "espresso", "americano",
    "smoothie", "frappe", "frapp", "refresher", "-tea", "tea-",
    "coca-cola", "diet-coke", "sprite", "barq", "fruitopia",
    "orange-dream", "berry-bliss", "strawberry-coke",
    "-juice", "milkshake", "triple-thick",
    "dasani-water", "hot-chocolate",
    "partly-skimmed-milk", "chocolate-milk",
]

def is_drink(item):
    url_lower = item["url"].lower()
    return any(kw in url_lower for kw in DRINK_URL_KEYWORDS)

def get_menu_item_links():
    """Scrapes the main menu page to collect all product links and their categories."""
    print(f"Fetching main menu from: {START_URL}")
    response = requests.get(START_URL, headers=HEADERS)
    if response.status_code != 200:
        print(f"Error accessing main page: Code {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    item_links = []

    # McDonald's structured class targeting catalog menu grid blocks
    # Note: If the class shifts, check elements matching standard <li> or <a> containing products
    products = soup.find_all('li', class_='cmp-category__item')
    
    for idx, product in enumerate(products, 1):
        link_tag = product.find('a', class_='cmp-category__item-link')
        name_tag = product.find('div', class_='cmp-category__item-name')
        
        if link_tag and name_tag:
            item_name = name_tag.text.strip()
            relative_url = link_tag.get('href', '')
            
            # Construct absolute URL out of relative paths
            full_url = relative_url if relative_url.startswith('http') else f"{BASE_URL}{relative_url}"
            
            # Try to infer category from the parent element context or tracking parameters
            item_links.append({
                "name": item_name,
                "url": full_url
            })
            
    print(f"Found {len(item_links)} product links to scrape.")
    return item_links

def scrape_nutrition_details(item_url):
    """Navigates to an item's specific page and parses its nutrition information table."""
    nutrition_data = {}
    try:
        response = requests.get(item_url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return nutrition_data
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for standard nutrition wrapper elements
        # McDonald's templates typically list items under 'metric-value' or 'cmp-nutrition__item' classes
        nutrition_items = soup.find_all('li', class_='cmp-nutrition__item') or soup.find_all('div', class_='nutrition-attributes')
        
        for element in nutrition_items:
            # Safely navigate primary metric names vs numerical data values
            label_node = element.find(class_='metric-name') or element.find(class_='label')
            value_node = element.find(class_='metric-value') or element.find(class_='value')
            
            if label_node and value_node:
                clean_label = label_node.text.strip().replace(':', '')
                clean_value = value_node.text.strip()
                nutrition_data[clean_label] = clean_value
                
    except Exception as e:
        print(f"Error processing link {item_url}: {e}")
        
    return nutrition_data

def main():
    # 1. Gather all individual target endpoints
    product_targets = get_menu_item_links()
    if not product_targets:
        print("No products identified. Exiting.")
        return
        
    # Remove drinks and deduplicate by URL
    seen_urls = set()
    meal_targets = []
    for p in product_targets:
        if not is_drink(p) and p["url"] not in seen_urls:
            seen_urls.add(p["url"])
            meal_targets.append(p)
    print(f"After filtering drinks and duplicates: {len(meal_targets)} meal items.")
    product_targets = meal_targets

    compiled_dataset = []

    # 2. Iteratively explore item metrics
    for idx, product in enumerate(product_targets, 1):
        print(f"[{idx}/{len(product_targets)}] Pulling data for: {product['name']}")
        
        nutrition_metrics = scrape_nutrition_details(product['url'])
        
        # Base row composition
        row = {"Item Name": product['name'], "Source URL": product['url']}
        row.update(nutrition_metrics) # dynamically append all pulled nutrients
        
        compiled_dataset.append(row)
        
        # Polite crawling pause to avoid triggering site defense blocks
        time.sleep(1.5)
        
    # 3. Save output down to CSV file structure
    if compiled_dataset:
        # Determine all unique headers discovered during dynamic parsing
        all_headers = set()
        for item in compiled_dataset:
            all_headers.update(item.keys())
            
        # Prioritize primary metadata tracking columns manually
        ordered_headers = ["Item Name", "Source URL"] + sorted(list(all_headers - {"Item Name", "Source URL"}))
        
        csv_filename = "mcdonalds_scraped_nutrition.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as output_file:
            writer = csv.DictWriter(output_file, fieldnames=ordered_headers)
            writer.writeheader()
            writer.writerows(compiled_dataset)
            
        print(f"\nSuccess! File written securely to disk: '{csv_filename}'")

if __name__ == "__main__":
    main()