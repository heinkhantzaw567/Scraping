"""
Step 1: Intercept network requests on the BK nutrition page to find the API endpoint.
Run: python Scraping/BurgerKing/find_api.py
"""

import json
from playwright.sync_api import sync_playwright

URL = "https://www.burgerking.ca/nutrition-explorer"

captured = []

def handle_request(request):
    url = request.url
    if any(k in url.lower() for k in ["api", "menu", "nutrition", "product", "graphql", "ecomm", "rbictg", "rbi"]):
        captured.append({
            "url": url,
            "method": request.method,
            "headers": dict(request.headers),
            "post_data": request.post_data,
        })
        print(f"[REQ] {request.method} {url}")

def handle_response(response):
    url = response.url
    if any(k in url.lower() for k in ["api", "menu", "nutrition", "product", "graphql", "ecomm", "rbictg", "rbi"]):
        try:
            ct = response.headers.get("content-type", "")
            if "json" in ct:
                body = response.json()
                print(f"[RES] {response.status} {url}")
                print(f"      Keys: {list(body.keys()) if isinstance(body, dict) else type(body).__name__}")
                with open(f"Scraping/BurgerKing/response_{len(captured)}.json", "w", encoding="utf-8") as f:
                    json.dump(body, f, indent=2, ensure_ascii=False)
                print(f"      Saved to response_{len(captured)}.json")
        except Exception as e:
            print(f"[RES] {response.status} {url} (non-JSON: {e})")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        locale="en-CA",
    )
    page = context.new_page()
    page.on("request", handle_request)
    page.on("response", handle_response)

    print(f"Loading {URL} ...")
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(3000)

    browser.close()

print(f"\nTotal matching requests captured: {len(captured)}")
with open("Scraping/BurgerKing/captured_requests.json", "w", encoding="utf-8") as f:
    json.dump(captured, f, indent=2, ensure_ascii=False)
print("Saved to Scraping/BurgerKing/captured_requests.json")
