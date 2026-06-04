import json
import csv
from collections import OrderedDict

with open("data.json", encoding="utf-8") as f:
    data = json.load(f)

# Each entry: (category, item_name, caloric_value, {component: (value, unit)})
items = OrderedDict()
nutrient_order = []

def walk_categories(categories, category_path=""):
    for cat in categories:
        cat_name = cat.get("name", "")
        path = f"{category_path} > {cat_name}".strip(" > ")

        for product in cat.get("products", []):
            for item in product.get("items", []):
                content = item.get("content") or {}
                nutrition_list = content.get("nutritionalInformation") or []
                if not nutrition_list:
                    continue

                key = item.get("name", "")
                if key not in items:
                    items[key] = {
                        "category": path,
                        "item_name": key,
                        "caloric_value": content.get("caloricValue", ""),
                        "nutrients": {},
                    }

                for n in nutrition_list:
                    if not n.get("isActive", True):
                        continue
                    component = n.get("nutritionComponent", "")
                    unit = n.get("nutritionUnit", "")
                    col = f"{component} ({unit})"
                    items[key]["nutrients"][col] = n.get("serveWiseValue", "")
                    if col not in nutrient_order:
                        nutrient_order.append(col)

        walk_categories(cat.get("categories", []), path)

for top_cat in data.get("categories", []):
    walk_categories(top_cat.get("categories", []), top_cat.get("name", ""))

fieldnames = ["category", "item_name", "caloric_value"] + nutrient_order

with open("nutrition_data.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for entry in items.values():
        row = {
            "category": entry["category"],
            "item_name": entry["item_name"],
            "caloric_value": entry["caloric_value"],
            **entry["nutrients"],
        }
        writer.writerow(row)

print(f"Saved {len(items)} items to nutrition_data.csv ({len(nutrient_order)} nutrition columns)")
