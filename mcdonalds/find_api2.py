import re

html = open("debug_page.html", encoding="utf-8").read()

# Find dnaapp context
idx = html.find("dnaapp")
while idx >= 0:
    print(html[max(0, idx-80):idx+200])
    print("---")
    idx = html.find("dnaapp", idx + 1)
    if idx > 0:
        next_idx = html.find("dnaapp", idx + 1)
        if next_idx == idx:
            break
