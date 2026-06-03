"""
Harvey's Canada Nutrition Scraper  (BeautifulSoup, local HTML)
==============================================================
Reads Harvey/debug_page.html and writes harveys_nutrition.csv

HTML structure:
  div.nutritional-heading            → category name
  div.nutrition-product-heading      → item name
  div.nutrition-product-content      → allergens + ul.nutrition-info
    small > i                        → allergen text
    ul.nutrition-info > li           → label in text node, value in span.pull-right

Run:  python harveys_nutrition_scraper.py
"""

import csv
import logging
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

INPUT_HTML = Path("Harvey/debug_page.html")
OUTPUT_CSV = Path("Harvey/harveys_nutrition.csv")

ALLERGEN_LIST = ["Barley", "Egg", "Milk", "Mustard", "Oats", "Soy", "Sulphites", "Tree Nuts", "Wheat"]

NUTRITION_FIELDS = {
    "Serving Size":      ["Serving Size"],
    "Calories":          ["Calories", "Energy"],
    "Total Fat (g)":     ["Fat", "Total Fat"],
    "Saturated Fat (g)": ["Saturated Fat", "Saturated"],
    "Trans Fat (g)":     ["Trans Fat", "Trans"],
    "Cholesterol (mg)":  ["Cholesterol"],
    "Sodium (mg)":       ["Sodium"],
    "Carbohydrates (g)": ["Carbohydrates", "Total Carbohydrate", "Carbohydrate"],
    "Fibre (g)":         ["Fiber", "Fibre", "Dietary Fibre", "Dietary Fiber"],
    "Sugars (g)":        ["Sugars", "Sugar"],
    "Protein (g)":       ["Protein"],
    "Calcium (mg)":      ["Calcium"],
    "Potassium (mg)":    ["Potassium"],
    "Iron (mg)":         ["Iron"],
}

FIELDNAMES = (
    ["Category", "Item Name"]
    + list(NUTRITION_FIELDS.keys())
    + ["Allergens"]
    + [f"Contains {a}" for a in ALLERGEN_LIST]
)


def parse_nutrition_ul(ul_tag) -> dict[str, str]:
    """Extract label→value from ul.nutrition-info."""
    raw: dict[str, str] = {}
    if ul_tag is None:
        return raw
    for li in ul_tag.find_all("li"):
        span = li.find("span", class_="pull-right")
        if span is None:
            continue
        value = span.get_text(strip=True)
        # Strip trailing 'Cals' unit (calories are already unitless in our columns)
        value = re.sub(r"\s*Cals?\s*$", "", value, flags=re.IGNORECASE).strip()
        label = li.get_text(separator=" ", strip=True)
        label = label.replace(span.get_text(strip=True), "").strip()
        if label:
            raw[label] = value
    return raw


def map_nutrition(raw: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for canonical, variants in NUTRITION_FIELDS.items():
        matched = ""
        for v in variants:
            for k, val in raw.items():
                if k.strip().lower() == v.lower():
                    matched = val
                    break
            if matched:
                break
        out[canonical] = matched
    return out


def parse_allergens(content_div) -> tuple[str, dict[str, str]]:
    """Return (allergen_text, {Contains X: Yes/No, ...}) for all allergens in ALLERGEN_LIST."""
    small = content_div.find("small")
    text = ""
    if small is not None:
        text = small.get_text(" ", strip=True)
        text = re.sub(r"^ALLERGENS\s*:\s*", "", text, flags=re.IGNORECASE).strip()

    # Build boolean flags — case-insensitive substring match
    text_lower = text.lower()
    flags = {
        f"Contains {a}": ("Yes" if a.lower() in text_lower else "No")
        for a in ALLERGEN_LIST
    }
    return text, flags


DRINK_CATEGORIES = {"soft drinks", "shakes", "frozen drink", "frozen red bull"}


def is_drink_category(name: str) -> bool:
    name_lower = name.lower()
    return any(keyword in name_lower for keyword in DRINK_CATEGORIES)


def scrape(soup: BeautifulSoup) -> list[dict]:
    records: list[dict] = []
    current_category = "Unknown"

    # Category sections: div.nutrition-category-section
    for section in soup.find_all("div", class_="nutrition-category-section"):
        # Category heading
        heading = section.find("div", class_="nutritional-heading")
        if heading:
            current_category = heading.get_text(strip=True).title()

        if is_drink_category(current_category):
            continue

        # All product headings inside this section
        for product_heading in section.find_all("div", class_="nutrition-product-heading"):
            item_name = product_heading.get_text(strip=True)
            if not item_name:
                continue

            # The product content div immediately follows the heading
            # It's a sibling with class nutrition-product-content
            content_div = product_heading.find_next_sibling("div", class_="nutrition-product-content")
            if content_div is None:
                continue

            allergen_text, allergen_flags = parse_allergens(content_div)
            ul = content_div.find("ul", class_="nutrition-info")
            raw = parse_nutrition_ul(ul)
            row = {"Category": current_category, "Item Name": item_name}
            row.update(map_nutrition(raw))
            row["Allergens"] = allergen_text
            row.update(allergen_flags)
            records.append(row)

    return records


def main():
    if not INPUT_HTML.exists():
        log.error("HTML file not found: %s", INPUT_HTML)
        sys.exit(1)

    log.info("Reading %s …", INPUT_HTML)
    html = INPUT_HTML.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    records = scrape(soup)
    log.info("Parsed %d items", len(records))

    if not records:
        log.error("No items found — check the HTML structure.")
        sys.exit(1)

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    print(f"\nSaved {len(records)} items to '{OUTPUT_CSV}'")
    print(f"\n{'Category':<28} {'Item Name':<40} {'Cal':>6} {'Fat':>6} {'Na':>7} {'Pro':>6}")
    print("-" * 98)
    for r in records[:25]:
        print(
            f"{r['Category']:<28} "
            f"{r['Item Name']:<40} "
            f"{r.get('Calories', ''):>6} "
            f"{r.get('Total Fat (g)', ''):>6} "
            f"{r.get('Sodium (mg)', ''):>7} "
            f"{r.get('Protein (g)', ''):>6}"
        )
    if len(records) > 25:
        print(f"  … {len(records) - 25} more rows in '{OUTPUT_CSV}'")


if __name__ == "__main__":
    main()
