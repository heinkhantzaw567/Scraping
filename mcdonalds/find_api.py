import re

html = open("debug_page.html", encoding="utf-8").read()

patterns = {
    "API/nutrition URLs": r'["\']([^"\']{0,80}(?:api|nutrition|product)[^"\']{0,80}\.json[^"\']*)["\']',
    "data-product-*": r'data-product[a-z\-]*="([^"]{0,60})"',
    "productId": r'productI[dD]["\s:=]+([A-Za-z0-9_\-]{3,30})',
    "itemId": r'itemI[dD]["\s:=]+([A-Za-z0-9_\-]{3,30})',
    "data-id": r'data-id="([^"]{1,40})"',
    "/ca/en-ca/*.json": r'"(/ca/en-ca/[^"]{1,80}\.json[^"]*)"',
    "data-context": r'data-context="([^"]{0,100})"',
    "data-component-id": r'data-component[a-z\-]*="([^"]{0,60})"',
}

for name, pat in patterns.items():
    matches = re.findall(pat, html, re.IGNORECASE)
    unique = list(dict.fromkeys(matches))[:5]
    if unique:
        print(f"\n{name}:")
        for m in unique:
            print(f"  {m}")
    else:
        print(f"\n{name}: (none)")

# Look for any JSON object with actual numeric values near the nutrition section
idx = html.find("cmp-nutrition-summary")
chunk = html[idx:idx+8000]

# Look for data attributes with numeric values
num_attrs = re.findall(r'data-[a-z\-]+="(\d[^"]{0,20})"', chunk)
print("\nNumeric data-* values near nutrition:")
for v in list(dict.fromkeys(num_attrs))[:20]:
    print(f"  {v}")

# Check for any embedded JSON with actual numbers
json_blobs = re.findall(r'\{[^{}]{20,500}\}', chunk)
for blob in json_blobs[:5]:
    if re.search(r':\s*\d+', blob):
        print(f"\nJSON blob: {blob[:200]}")
