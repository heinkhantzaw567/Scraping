import requests, json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-CA,en;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
}

# Test a few products with expected allergens
test_items = {
    "Hamburger":    "200154",
    "Egg McMuffin": "200049",  # egg, milk, wheat
    "Filet-O-Fish": "200151",  # fish, wheat, milk
    "Big Mac":      "200156",
}

session = requests.Session()
for name, pid in test_items.items():
    resp = session.get(
        "https://www.mcdonalds.com/dnaapp/itemDetails",
        params={"country": "CA", "language": "en", "item": pid},
        headers=HEADERS, timeout=15
    )
    item = resp.json()["item"]

    # Summary strings
    contains_str  = item.get("item_allergen", "")
    may_str       = item.get("item_additional_allergen", "")
    if isinstance(may_str, dict):
        may_str = ""

    # Detailed list
    allergens = item.get("allergens", {}).get("allergen", [])
    contains_y  = [a["name"].replace("Allergen ", "") for a in allergens
                   if a["value"] == "Y" and not a["name"].startswith("May")]
    may_y       = [a["name"].replace("May Contain Allergen ", "") for a in allergens
                   if a["value"] == "Y" and a["name"].startswith("May")]

    print(f"\n{'='*50}")
    print(f"  {name}  (id={pid})")
    print(f"  item_allergen string   : {contains_str!r}")
    print(f"  additional_allergen    : {may_str!r}")
    print(f"  allergen list Y/contains : {contains_y}")
    print(f"  allergen list Y/may      : {may_y}")
