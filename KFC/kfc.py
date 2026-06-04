import requests
import json

URL = "https://orderserv-kfc-na-olo-api.yum.com/dev/v1/catalogs/a087813cef074625a8341e162356a1e5/KFCCanadaMenu-Generic-en"

# Copy these from Network tab → click the request → Headers tab
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.kfc.ca/",
    "Origin": "https://www.kfc.ca",
    "Accept": "application/json",
    # Add any of these if you see them in the request headers:
    # "Authorization": "Bearer xxx",
    # "x-api-key": "xxx",
    # "x-tenant-id": "xxx",
}

r = requests.get(URL, headers=HEADERS)
print(r.status_code)
data = r.json()

# Save raw response
with open("kfc_menu.json", "w") as f:
    json.dump(data, f, indent=2)

print(json.dumps(data, indent=2)[:1000])  # preview