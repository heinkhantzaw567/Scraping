import requests, json, html as html_module

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-CA,en;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.mcdonalds.com/ca/en-ca/meal/hm-cheeseburger.html",
}

# Default item IDs from data-meal-items for Cheeseburger Happy Meal
item_ids = ["200140", "200170", "200001", "200107", "200164"]
ids_str = ",".join(item_ids)

session = requests.Session()

# Try various param combos for itemCollectionDetails
urls = [
    f"https://www.mcdonalds.com/dnaapp/itemCollectionDetails?country=CA&language=en&items={ids_str}",
    f"https://www.mcdonalds.com/dnaapp/itemCollectionDetails?country=CA&language=en&item={ids_str}",
    f"https://www.mcdonalds.com/dnaapp/itemCollectionDetails?country=CA&language=en&itemIds={ids_str}",
    f"https://www.mcdonalds.com/dnaapp/itemCollectionDetails?country=CA&language=en&collection=200925&items={ids_str}",
    f"https://www.mcdonalds.com/dnaapp/itemCollectionDetails?country=CA&language=en&item=200140&item=200170&item=200001&item=200107&item=200164",
]

for url in urls:
    resp = session.get(url, headers=HEADERS, timeout=15)
    short = url.split("itemCollectionDetails?")[1][:80]
    print(f"[{resp.status_code}] ...{short}")
    if resp.status_code == 200:
        print("  SUCCESS:", resp.text[:300])
        break
    else:
        print("  ", resp.text[:100])

print()
print("--- Fallback: sum individual itemDetails ---")
total = {}
for iid in item_ids:
    url = f"https://www.mcdonalds.com/dnaapp/itemDetails?country=CA&language=en&item={iid}"
    resp = session.get(url, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        print(f"  Failed {iid}")
        continue
    data = resp.json()
    name = data["item"].get("item_name", iid)
    nutrients = data["item"].get("nutrient_facts", {}).get("nutrient", [])
    print(f"  {name}: {len(nutrients)} nutrients")
    for n in nutrients:
        key = n.get("name", "")
        val = n.get("value", "0")
        uom = n.get("uom", "")
        if isinstance(uom, dict):
            uom = ""
        try:
            v = float(val)
            total[key] = round(total.get(key, 0.0) + v, 2)
        except ValueError:
            pass

print("\nSummed totals:")
for k, v in sorted(total.items()):
    print(f"  {k}: {v}")
