"""
Scrape Burger King Canada nutrition data from the captured Sanity API response.
Reads: Scraping/BurgerKing/sanity_7.json
Writes: NutritionalInfo/BK_NutritionalInfo_new.csv

Allergen values: 0 = No, 1 = May Contain, 2/3 = Contains
"""

import json
import csv
from pathlib import Path

INPUT = Path("Scraping/BurgerKing/sanity_7.json")
OUTPUT = Path("NutritionalInfo/BK_NutritionalInfo_new.csv")

ALLERGEN_FIELDS = [
    "milk", "eggs", "fish", "peanuts", "shellfish",
    "treeNuts", "soy", "wheat", "mustard", "sesame",
    "celery", "lupin", "gluten", "sulphurDioxide",
]

FIELDNAMES = [
    "Category", "Item", "Serving Weight (g)", "Calories",
    "Fat (g)", "Saturated Fat (g)", "Trans Fat (g)",
    "Cholesterol (mg)", "Sodium (mg)", "Carbohydrates (g)",
    "Fiber (g)", "Sugar (g)", "Protein (g)",
    # Allergens
    "Contains Milk", "Contains Eggs", "Contains Fish", "Contains Peanuts",
    "Contains Shellfish", "Contains Tree Nuts", "Contains Soy", "Contains Wheat",
    "Contains Mustard", "Contains Sesame", "Contains Celery", "Contains Lupin",
    "Contains Gluten", "Contains Sulphur Dioxide",
]


def allergen_label(val):
    if val is None or val == 0:
        return "No"
    if val == 1:
        return "May Contain"
    return "Contains"  # 2 or 3


def nutrition_row(category, name, nutrition, allergens):
    n = nutrition or {}
    a = allergens or {}

    def v(key):
        val = n.get(key)
        if val is None:
            return ""
        return round(val, 3) if isinstance(val, float) else val

    row = {
        "Category": category,
        "Item": name,
        "Serving Weight (g)": v("weight"),
        "Calories": v("calories"),
        "Fat (g)": v("fat"),
        "Saturated Fat (g)": v("saturatedFat"),
        "Trans Fat (g)": v("transFat"),
        "Cholesterol (mg)": v("cholesterol"),
        "Sodium (mg)": v("sodium"),
        "Carbohydrates (g)": v("carbohydrates"),
        "Fiber (g)": v("fiber"),
        "Sugar (g)": v("sugar"),
        "Protein (g)": v("proteins"),
    }

    allergen_col_map = {
        "milk": "Contains Milk", "eggs": "Contains Eggs", "fish": "Contains Fish",
        "peanuts": "Contains Peanuts", "shellfish": "Contains Shellfish",
        "treeNuts": "Contains Tree Nuts", "soy": "Contains Soy", "wheat": "Contains Wheat",
        "mustard": "Contains Mustard", "sesame": "Contains Sesame", "celery": "Contains Celery",
        "lupin": "Contains Lupin", "gluten": "Contains Gluten",
        "sulphurDioxide": "Contains Sulphur Dioxide",
    }
    for field, col in allergen_col_map.items():
        row[col] = allergen_label(a.get(field))

    return row


def extract_items(section_name, options, rows):
    for item in options:
        item_type = item.get("_type")
        name = item.get("name", {}).get("locale", "Unknown").strip()

        if item_type == "item":
            nutrition = item.get("nutrition") or item.get("nutritionWithModifiers")
            allergens = item.get("allergens")
            if nutrition:
                rows.append(nutrition_row(section_name, name, nutrition, allergens))

        elif item_type == "picker":
            # Picker = item with size/option variants
            for mapping in item.get("options", []):
                for picker_item in mapping.get("option", {}).get("options", []) if isinstance(mapping.get("option"), dict) else []:
                    pass
            # Use pickerAspectItemOptionMappings to get variants
            for mapping in item.get("pickerAspectItemOptionMappings", []):
                for opt in mapping.get("options", []):
                    variant = opt.get("option") or {}
                    variant_name = variant.get("name", {}).get("locale", "")
                    full_name = f"{name} - {variant_name}".strip(" -")
                    nutrition = variant.get("nutrition") or variant.get("nutritionWithModifiers")
                    allergens = variant.get("allergens")
                    if nutrition:
                        rows.append(nutrition_row(section_name, full_name, nutrition, allergens))
            # Fallback: direct options list
            for opt_group in item.get("options", []):
                opt_item = opt_group.get("option") or opt_group.get("pickerItemMappings", [{}])[0].get("option") if opt_group.get("pickerItemMappings") else None
                if opt_item:
                    variant_name = opt_item.get("name", {}).get("locale", "")
                    full_name = f"{name} - {variant_name}".strip(" -")
                    nutrition = opt_item.get("nutrition") or opt_item.get("nutritionWithModifiers")
                    allergens = opt_item.get("allergens")
                    if nutrition and not any(r["Item"] == full_name and r["Category"] == section_name for r in rows):
                        rows.append(nutrition_row(section_name, full_name, nutrition, allergens))

        elif item_type == "combo":
            main = item.get("mainItem") or {}
            nutrition = main.get("nutrition") or main.get("nutritionWithModifiers")
            allergens = main.get("allergens")
            if nutrition:
                rows.append(nutrition_row(section_name, name, nutrition, allergens))

        elif item_type == "section":
            # Nested section
            extract_items(name or section_name, item.get("options", []), rows)


def main():
    with open(INPUT, encoding="utf-8") as f:
        data = json.load(f)

    sections = data["data"]["StaticPage"]["widgets"][0]["menu"]["options"]
    rows = []

    for section in sections:
        section_name = section.get("name", {}).get("locale", "Unknown")
        print(f"  Processing: {section_name}")
        extract_items(section_name, section.get("options", []), rows)

    OUTPUT.parent.mkdir(exist_ok=True)
    with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} items to {OUTPUT}")


if __name__ == "__main__":
    main()
