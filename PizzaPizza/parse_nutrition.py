import csv
import os
from bs4 import BeautifulSoup

base = os.path.dirname(os.path.abspath(__file__))

file_labels = {
    "small.html": "Small",
    "medium.html": "Medium",
    "large.html": "Large",
    "x-large.html": "X-Large",
    "xxl-pizza.html": "XXL",
    "stuffed-crust.html": "Stuffed Crust",
    "gourmet.html": "Gourmet",
    "walk-in.html": "Walk-In",
    "alternative.html": "Alternative",
    "chicken.html": "Chicken",
    "desserts.html": "Desserts",
    "dips.html": "Dips",
    "donair.html": "Donair",
    "loaded-tots.html": "Loaded Tots",
    "plant-based-chicken.html": "Plant-Based Chicken",
    "poutine.html": "Poutine",
    "sandwiches.html": "Sandwiches",
    "sides.html": "Sides",
    "strombolis.html": "Strombolis",
    "wingsause.html": "Wing Sauce",
}

# Canonical output columns (after Category)
CANONICAL = [
    "Product Name", "Serving Size (g)", "Weight Per Slice (g)", "Serving Size",
    "Calories (Cals)", "Protein (g)", "Carbs (g)", "Fibre (g)", "Sugars (g)",
    "Total Fat (g)", "Sat. Fat (g)", "Trans Fat (g)", "Cholesterol (mg)",
    "Sodium (mg)", "Potassium (% DV)", "Calcium (% DV)", "Iron (% DV)",
]

def normalize_header(h):
    # Fix known typo in source data
    return h.replace("Calcium (% VQ)", "Calcium (% DV)")

rows = []

for filename, label in file_labels.items():
    path = os.path.join(base, filename)
    if not os.path.exists(path):
        continue
    with open(path, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    raw_headers = [normalize_header(th.get_text(strip=True)) for th in soup.select("thead th")]

    for tr in soup.select("tbody tr"):
        tds = tr.find_all("td")
        if not tds:
            continue
        cells = [td.get_text(strip=True) for td in tds]
        src = dict(zip(raw_headers, cells))
        row = [label] + [src.get(col, "") for col in CANONICAL]
        rows.append(row)

out_path = os.path.join(base, "nutrition.csv")
with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Category"] + CANONICAL)
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows to {out_path}")
