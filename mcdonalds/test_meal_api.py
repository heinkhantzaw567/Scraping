import requests, json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-CA,en;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
}

product_id = "200925"  # Cheeseburger Happy Meal

urls = [
    f"https://www.mcdonalds.com/dnaapp/itemCollectionDetails?country=CA&language=en&item={product_id}",
    f"https://www.mcdonalds.com/dnaapp/itemCollectionDetails?country=CA&language=en&id={product_id}",
    f"https://www.mcdonalds.com/dnaapp/itemCollectionDetails?country=CA&language=en&collection={product_id}",
    f"https://www.mcdonalds.com/dnaapp/itemDetails?country=CA&language=en&item={product_id}",
]

session = requests.Session()
for url in urls:
    resp = session.get(url, headers=HEADERS, timeout=20)
    print(f"[{resp.status_code}] {url.split('?')[0].split('/')[-1]}?{url.split('?')[1][:60]}")
    if resp.status_code == 200:
        data = resp.json()
        with open("meal_api_response.json", "w") as f:
            json.dump(data, f, indent=2)
        print("  Saved to meal_api_response.json")
        # Print top-level keys
        print("  Top keys:", list(data.keys())[:10])
        break
    else:
        print("  Body:", resp.text[:200])
