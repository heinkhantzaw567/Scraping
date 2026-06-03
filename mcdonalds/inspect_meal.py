import requests, re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-CA,en;q=0.9",
}

url = "https://www.mcdonalds.com/ca/en-ca/meal/hm-cheeseburger.html"
resp = requests.get(url, headers=HEADERS, timeout=20)
html = resp.text

print("Status:", resp.status_code)
print("HTML length:", len(html))
print()

# Check what data-* attributes exist
attrs = re.findall(r'(data-[a-z\-]+)="([^"]{1,80})"', html)
seen = {}
for k, v in attrs:
    if k not in seen:
        seen[k] = v

print("Unique data-* attributes:")
for k, v in sorted(seen.items()):
    print(f"  {k} = {v[:80]}")

print()
# Check for product IDs
for pattern in [r'data-product-id="(\d+)"', r'"item":\s*(\d+)', r'item=(\d+)', r'itemId["\s:=]+(\d+)']:
    m = re.search(pattern, html)
    print(f"Pattern {pattern!r}: {m.group(0) if m else 'NOT FOUND'}")

print()
# Look for dnaapp references
for m in re.finditer(r'dnaapp[^\s"\'<>]{0,100}', html):
    print("dnaapp:", m.group(0))
