import requests, re, json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-CA,en;q=0.9",
}

url = "https://www.mcdonalds.com/ca/en-ca/meal/hm-cheeseburger.html"
resp = requests.get(url, headers=HEADERS, timeout=20)
html = resp.text

# Save HTML
with open("meal_page.html", "w", encoding="utf-8") as f:
    f.write(html)

# Find all data-* attributes on the pdp/nutrition components
idx = html.find('data-component="pdp"')
chunk = html[idx:idx+2000]
print("PDP component block:")
print(chunk[:1500])
print()

# Find itemCollectionDetails call if any
for m in re.finditer(r'itemCollection[^\s"\'<>]{0,200}', html, re.IGNORECASE):
    print("itemCollection:", m.group(0))

print()
# Check all data-meal* attributes
for m in re.finditer(r'data-meal[a-z\-]*="([^"]{0,120})"', html):
    print(f"  {m.group(0)}")

print()
# Look for collection IDs
for m in re.finditer(r'data-collection[a-z\-]*="([^"]{0,60})"', html):
    print(f"  {m.group(0)}")

# Check the component ids in the API response
data = json.load(open("meal_api_response.json"))
components = data["item"].get("components", {}).get("component", [])
print(f"\nAll {len(components)} component IDs:")
for c in components:
    print(f"  id={c.get('id')} name={c.get('product_name')!r} type={c.get('product_type_name')!r} default={c.get('is_default')}")
