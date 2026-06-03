import requests, re, json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-CA,en;q=0.9",
}
url = "https://www.mcdonalds.com/ca/en-ca/product/hamburger.html"
resp = requests.get(url, headers=HEADERS, timeout=20)
html = resp.text

print("Status:", resp.status_code)
print("HTML length:", len(html))
print()

keywords = ["Calories", "calories", "Total Fat", "totalFat", "Sodium", "sodium",
            "nutrition", "Nutrition", "cmp-nutrition", "servingSize"]
for kw in keywords:
    idx = html.find(kw)
    if idx >= 0:
        snippet = html[max(0, idx-40):idx+120].replace("\n", " ")
        print(f'FOUND "{kw}" at {idx}:\n  ...{snippet}...\n')
    else:
        print(f'NOT FOUND: "{kw}"')

# Save full HTML for manual inspection
with open("debug_page.html", "w", encoding="utf-8") as f:
    f.write(html)
print("\nFull HTML saved to debug_page.html")

# Look for script tags with JSON data
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
print(f"\nFound {len(scripts)} <script> blocks")
for i, s in enumerate(scripts):
    if any(k in s for k in ["calories", "Calories", "nutrition", "totalFat"]):
        print(f"\nScript #{i} (first 500 chars):\n{s[:500]}")
