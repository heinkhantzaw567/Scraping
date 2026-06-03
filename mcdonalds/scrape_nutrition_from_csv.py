"""
McDonald's Canada Nutrition Scraper  (requests + BeautifulSoup + DNA API)
=========================================================================
Strategy:
  1. Fetch each product page (HTML) and extract data-product-id
  2. Call the McDonald's internal DNA API to get full nutrition facts
  3. Write all results to mcdonalds_full_nutrition.csv

Run:   python scrape_nutrition_from_csv.py
Test:  python scrape_nutrition_from_csv.py --test   (first 5 items)
"""

import csv, sys, time, random, json, re, logging
from pathlib import Path
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

INPUT_CSV  = "mcdonalds_scraped_nutrition.csv"
OUTPUT_CSV = "mcdonalds_full_nutrition.csv"
TEST_MODE  = "--test" in sys.argv
TEST_LIMIT = 5

DNA_API        = "https://www.mcdonalds.com/dnaapp/itemDetails"
DNA_PARAMS     = {"country": "CA", "language": "en"}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-CA,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

API_HEADERS = {
    **HEADERS,
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
}

# Canonical column → API nutrient name variants to look up in the raw dict.
# Names ending in "% DV" are looked up under "NutrientName % DV" in the raw dict.
NUTRITION_FIELDS = {
    "Serving Size":       ["Serving Size"],
    "Calories":           ["Calories", "Energy"],
    "Total Fat (g)":      ["Fat", "Total Fat"],
    "Saturated Fat (g)":  ["Saturated Fat", "Saturated"],
    "Trans Fat (g)":      ["Trans Fat", "Trans"],
    "Cholesterol (mg)":   ["Cholesterol"],
    "Sodium (mg)":        ["Sodium"],
    "Carbohydrates (g)":  ["Carbohydrates", "Total Carbohydrate", "Carbohydrate"],
    "Fibre (g)":          ["Fibre", "Dietary Fibre", "Fiber", "Dietary Fiber"],
    "Sugars (g)":         ["Sugars", "Sugar", "Total Sugars"],
    "Protein (g)":        ["Protein"],
    "Potassium (mg)":     ["Potassium"],
    # % DV columns — look up under "NutrientName % DV" key set by the parser
    "Calcium (% DV)":     ["Calcium % DV"],
    "Iron (% DV)":        ["Iron % DV"],
    "Vitamin A (% DV)":   ["Vitamin A % DV"],
    "Vitamin C (% DV)":   ["Vitamin C % DV"],
    "Vitamin D (% DV)":   ["Vitamin D % DV"],
}

FIELDNAMES = (
    ["Item Name", "Source URL"]
    + list(NUTRITION_FIELDS.keys())
    + ["Contains Allergens", "May Contain Allergens"]
)


def fetch_page(url: str, session: requests.Session) -> str:
    """Return HTML for a URL, or empty string on failure."""
    try:
        resp = session.get(url, headers=HEADERS, timeout=20)
        if resp.status_code == 200:
            return resp.text
        log.warning("HTTP %d for %s", resp.status_code, url)
    except requests.RequestException as e:
        log.warning("Page fetch error %s: %s", url, e)
    return ""


def get_product_id(html: str) -> str | None:
    """Extract data-product-id from page HTML."""
    soup = BeautifulSoup(html, "html.parser")
    el = soup.find(attrs={"data-product-id": True})
    if el:
        return el["data-product-id"]
    m = re.search(r'data-product-id="(\d+)"', html)
    return m.group(1) if m else None


def get_meal_component_ids(html: str) -> list[str]:
    """
    For /meal/ pages: extract the default item IDs from the data-meal-items
    JSON attribute. Returns a list of item_id strings.
    """
    import html as html_module
    m = re.search(r'data-meal-items="([^"]+)"', html)
    if not m:
        return []
    try:
        decoded = html_module.unescape(m.group(1))
        data = json.loads(decoded)
        items = data.get("items", {}).get("item", [])
        return [str(it["item_id"]) for it in items if "item_id" in it]
    except Exception as e:
        log.warning("Could not parse data-meal-items: %s", e)
        return []


def fetch_api_item(product_id: str, session: requests.Session) -> dict:
    """Call itemDetails API and return the parsed JSON response, or {}."""
    try:
        resp = session.get(
            DNA_API,
            params={**DNA_PARAMS, "item": product_id},
            headers=API_HEADERS,
            timeout=20,
        )
        if resp.status_code == 200:
            return resp.json()
        log.warning("API HTTP %d for product %s", resp.status_code, product_id)
    except Exception as e:
        log.warning("API error for product %s: %s", product_id, e)
    return {}


def parse_nutrient_list(nutrients: list) -> dict:
    """
    Convert a list of API nutrient dicts into a flat result dict.
    Stores plain values and also 'Name % DV' keys for DV percentages.
    """
    result = {}
    for n in nutrients:
        name = str(n.get("name", "")).strip()
        value = str(n.get("value", "")).strip()
        raw_uom = n.get("uom", "")
        uom = str(raw_uom).strip() if not isinstance(raw_uom, dict) else ""
        raw_dv = n.get("adult_dv", "")
        dv = str(raw_dv).strip() if not isinstance(raw_dv, dict) else ""
        if not name:
            continue
        result[name] = f"{value} {uom}".strip() if uom else value
        if dv:
            result[f"{name} % DV"] = dv
    return result


def parse_allergens(item: dict) -> tuple[str, str]:
    """
    Return (contains, may_contain) allergen strings from an API item dict.
    Cleans the leading 'Contains ' / 'May Contain ' prefix and trailing period.
    """
    contains = item.get("item_allergen", "")
    if isinstance(contains, dict):
        contains = ""
    contains = re.sub(r"^Contains\s*", "", contains, flags=re.IGNORECASE).rstrip(".").strip()

    may = item.get("item_additional_allergen", "")
    if isinstance(may, dict):
        may = ""
    may = re.sub(r"^May Contain\s*", "", may, flags=re.IGNORECASE).rstrip(".").strip()

    return contains, may


def merge_allergen_pairs(pairs: list[tuple[str, str]]) -> tuple[str, str]:
    """Deduplicate and sort allergens collected from multiple components.
    Normalises to Title Case so 'MILK' and 'Milk' become one entry.
    """
    contains_all: set[str] = set()
    may_all: set[str] = set()
    for c, m in pairs:
        if c:
            contains_all.update(x.strip().title() for x in c.split(",") if x.strip())
        if m:
            may_all.update(x.strip().title() for x in m.split(",") if x.strip())
    return ", ".join(sorted(contains_all)), ", ".join(sorted(may_all))


def sum_nutrient_lists(component_ids: list[str],
                       session: requests.Session) -> tuple[dict, str, str]:
    """
    Fetch itemDetails for each component.
    Returns (summed_nutrition_dict, contains_allergens_str, may_contain_allergens_str).
    """
    totals: dict[str, float] = {}
    units: dict[str, str] = {}
    allergen_pairs: list[tuple[str, str]] = []

    for cid in component_ids:
        data = fetch_api_item(cid, session)
        item = data.get("item", {})
        nutrients = item.get("nutrient_facts", {}).get("nutrient", [])
        for n in nutrients:
            name = str(n.get("name", "")).strip()
            value = str(n.get("value", "0")).strip()
            raw_uom = n.get("uom", "")
            uom = str(raw_uom).strip() if not isinstance(raw_uom, dict) else ""
            if not name:
                continue
            try:
                totals[name] = round(totals.get(name, 0.0) + float(value), 2)
                if name not in units:
                    units[name] = uom
            except ValueError:
                pass
        allergen_pairs.append(parse_allergens(item))
        time.sleep(0.3)

    result = {}
    for name, total in totals.items():
        uom = units.get(name, "")
        display = str(int(total)) if total == int(total) else str(total)
        result[name] = f"{display} {uom}".strip() if uom else display

    contains, may = merge_allergen_pairs(allergen_pairs)
    return result, contains, may


def get_item_data(product_id: str, page_html: str,
                  session: requests.Session) -> tuple[dict, str, str]:
    """
    Returns (nutrition_dict, contains_allergens, may_contain_allergens).
    Handles both regular products and Happy Meal collections.
    """
    data = fetch_api_item(product_id, session)
    item = data.get("item", {})
    nutrients = item.get("nutrient_facts", {}).get("nutrient", [])

    if nutrients:
        contains, may = parse_allergens(item)
        return parse_nutrient_list(nutrients), contains, may

    # Item Collection — sum components and aggregate allergens
    component_ids = get_meal_component_ids(page_html)
    if component_ids:
        log.info("  meal collection — summing %d components: %s",
                 len(component_ids), component_ids)
        nutrition, contains, may = sum_nutrient_lists(component_ids, session)
        return nutrition, contains, may

    return {}, "", ""


def map_nutrition(raw: dict) -> dict:
    """Map API nutrient names → canonical CSV column names."""
    out = {}
    for canonical, variants in NUTRITION_FIELDS.items():
        for v in variants:
            if v in raw:
                out[canonical] = raw[v]
                break
        else:
            out[canonical] = ""
    return out


def scrape_item(item_name: str, url: str, session: requests.Session) -> dict:
    row = {"Item Name": item_name, "Source URL": url}

    html = fetch_page(url, session)
    if not html:
        log.warning("  No HTML for %s", item_name)
        row.update({f: "" for f in NUTRITION_FIELDS})
        row.update({"Contains Allergens": "", "May Contain Allergens": ""})
        return row

    product_id = get_product_id(html)
    if not product_id:
        log.warning("  No product ID for %s", item_name)
        row.update({f: "" for f in NUTRITION_FIELDS})
        row.update({"Contains Allergens": "", "May Contain Allergens": ""})
        return row

    log.info("  product_id=%s", product_id)
    raw, contains, may = get_item_data(product_id, html, session)
    row.update(map_nutrition(raw))
    row["Contains Allergens"]   = contains
    row["May Contain Allergens"] = may

    log.info("  %-40s  Cal:%-6s  Allergens: %s",
             item_name[:40],
             row.get("Calories", "?"),
             contains[:60] if contains else "(none)")
    return row


def main():
    input_path = Path(INPUT_CSV)
    if not input_path.exists():
        log.error("Input file not found: %s", INPUT_CSV)
        sys.exit(1)

    with open(input_path, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r.get("Source URL")]

    if TEST_MODE:
        rows = rows[:TEST_LIMIT]

    log.info("%s — %d items", "TEST MODE" if TEST_MODE else "FULL SCRAPE", len(rows))

    session = requests.Session()
    results = []

    for idx, row in enumerate(rows, 1):
        item_name = row.get("Item Name", "").strip()
        url = row.get("Source URL", "").strip()
        log.info("[%d/%d] %s", idx, len(rows), item_name)
        result = scrape_item(item_name, url, session)
        results.append(result)
        time.sleep(random.uniform(0.8, 1.5))

    out_path = Path("mcdonalds_test_nutrition.csv" if TEST_MODE else OUTPUT_CSV)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    total = len(results)
    filled = sum(1 for r in results if r.get("Calories"))
    print(f"\nSaved {total} items to '{out_path}'  ({filled}/{total} have Calories)")

    print(f"\n{'Item Name':<44} {'Cal':>7} {'Fat':>7} {'Carbs':>8} {'Pro':>7} {'Na':>9}")
    print("-" * 88)
    for r in results[:15]:
        print(f"{r['Item Name']:<44} "
              f"{r.get('Calories',''):>7} "
              f"{r.get('Total Fat (g)',''):>7} "
              f"{r.get('Carbohydrates (g)',''):>8} "
              f"{r.get('Protein (g)',''):>7} "
              f"{r.get('Sodium (mg)',''):>9}")
    if total > 15:
        print(f"  ... {total - 15} more rows in '{out_path}'")


if __name__ == "__main__":
    main()
