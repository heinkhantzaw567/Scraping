"""Quick test: scrape only the 8 Happy Meal rows."""
import csv, time, random, logging
import requests
from scrape_nutrition_from_csv import scrape_item, FIELDNAMES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

HAPPY_MEALS = [
    ("Grilled Cheese Happy Meal",          "https://www.mcdonalds.com/ca/en-ca/meal/grilled-cheese-happy-meal.html"),
    ("Lettuce and Tomato Snack Wrap Happy Meal", "https://www.mcdonalds.com/ca/en-ca/meal/lettuce-and-tomato-snack-wrap-happy-meal.html"),
    ("4 Chicken McNuggets Happy Meal",     "https://www.mcdonalds.com/ca/en-ca/meal/4-chicken-mcnuggets-happy-meal.html"),
    ("Cheeseburger Happy Meal",            "https://www.mcdonalds.com/ca/en-ca/meal/hm-cheeseburger.html"),
    ("Hamburger Happy Meal",               "https://www.mcdonalds.com/ca/en-ca/meal/hamburger-happy-meal.html"),
    ("Chicken Snack Wrap Happy Meal with Crispy Chicken", "https://www.mcdonalds.com/ca/en-ca/meal/snack-wrap-crispy-happy-meal.html"),
    ("Chicken Snack Wrap Happy Meal with Grilled Chicken", "https://www.mcdonalds.com/ca/en-ca/meal/snack-wrap-with-grilled-chicken-happy-meal.html"),
    ("Hotcakes Happy Meal",                "https://www.mcdonalds.com/ca/en-ca/meal/hotcakes-happy-meal.html"),
]

session = requests.Session()
results = []
for i, (name, url) in enumerate(HAPPY_MEALS, 1):
    print(f"\n[{i}/{len(HAPPY_MEALS)}] {name}")
    r = scrape_item(name, url, session)
    results.append(r)
    time.sleep(random.uniform(0.8, 1.2))

print(f"\n{'Item':<48} {'Cal':>7} {'Fat':>7} {'Carbs':>8} {'Pro':>7} {'Na':>9}")
print("-" * 95)
for r in results:
    print(f"{r['Item Name']:<48} "
          f"{r.get('Calories',''):>7} "
          f"{r.get('Total Fat (g)',''):>7} "
          f"{r.get('Carbohydrates (g)',''):>8} "
          f"{r.get('Protein (g)',''):>7} "
          f"{r.get('Sodium (mg)',''):>9}")
