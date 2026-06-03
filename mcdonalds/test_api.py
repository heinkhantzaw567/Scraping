import requests, json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-CA,en;q=0.9",
    "Referer": "https://www.mcdonalds.com/ca/en-ca/product/hamburger.html",
    "X-Requested-With": "XMLHttpRequest",
}

# Try various API URL formats
product_id = "200154"
base = "https://www.mcdonalds.com"

urls_to_try = [
    f"{base}/dnaapp/itemDetails?country=CA&language=en&item={product_id}",
    f"{base}/dnaapp/itemDetails?country=CA&language=en&id={product_id}",
    f"{base}/dnaapp/itemDetails?country=CA&language=en&itemId={product_id}",
    f"{base}/dnaapp/itemDetails/{product_id}?country=CA&language=en",
    f"{base}/ca/en-ca/dnaapp/itemDetails?country=CA&language=en&item={product_id}",
    f"https://www.mcdonalds.com/dnaapp/itemDetails?country=CA&language=en&item={product_id}&nutrientsItem=2",
]

session = requests.Session()
for url in urls_to_try:
    try:
        resp = session.get(url, headers=HEADERS, timeout=15)
        print(f"[{resp.status_code}] {url}")
        if resp.status_code == 200:
            ct = resp.headers.get("Content-Type", "")
            print(f"  Content-Type: {ct}")
            print(f"  Body (first 500): {resp.text[:500]}")
            print()
            if "json" in ct or resp.text.strip().startswith("{"):
                with open("api_response.json", "w") as f:
                    f.write(resp.text)
                print("  -> Saved to api_response.json")
                break
    except Exception as e:
        print(f"  ERROR: {e}")
