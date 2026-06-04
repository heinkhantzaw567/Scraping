"""
Capture all Sanity GraphQL responses from the BK nutrition page.
"""

import json
from playwright.sync_api import sync_playwright

URL = "https://www.burgerking.ca/nutrition-explorer"
GRAPHQL_HOST = "kjfd81ul.apicdn.sanity.io"

responses_saved = []

def handle_response(response):
    if GRAPHQL_HOST not in response.url:
        return
    try:
        body = response.json()
        idx = len(responses_saved)
        fname = f"Scraping/BurgerKing/sanity_{idx}.json"
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(body, f, indent=2, ensure_ascii=False)
        url_short = response.url[50:130]
        print(f"[{idx}] saved {len(json.dumps(body))} bytes | ...{url_short}")
        responses_saved.append(fname)
    except Exception as e:
        print(f"skip {response.url[:80]}: {e}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        locale="en-CA",
    )
    page = context.new_page()
    page.on("response", handle_response)

    print("Loading page (domcontentloaded)...")
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    print("Waiting 15s for all API calls...")
    page.wait_for_timeout(15000)
    browser.close()

print(f"\nTotal Sanity responses: {len(responses_saved)}")
