import json

data = json.load(open("meal_api_response.json"))
item = data["item"]

print("item_name:", item.get("item_name"))
print("item_type:", item.get("item_type"))
print()

nf = item.get("nutrient_facts", {})
nutrients = nf.get("nutrient", [])
print(f"nutrient_facts.nutrient count: {len(nutrients)}")
for n in nutrients:
    print(f"  id={n.get('id')} name={n.get('name')!r:25} value={n.get('value')!r:10} uom={n.get('uom')!r}")

print()
# Check for components / sub-items
components = item.get("components", {}).get("component", [])
print(f"components count: {len(components)}")
for c in components[:3]:
    print(f"  {c.get('product_name')} (id={c.get('id')}) — nutrients: {len(c.get('nutrient_facts',{}).get('nutrient',[]))}")
