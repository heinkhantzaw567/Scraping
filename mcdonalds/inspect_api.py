import json

data = json.load(open("api_response.json"))
nutrients = data["item"]["nutrient_facts"]["nutrient"]
for n in nutrients:
    print(n)
