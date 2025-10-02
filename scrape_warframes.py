import requests
from bs4 import BeautifulSoup
import json

BASE_URL = "https://wiki.warframe.com"
LIST_URL = f"{BASE_URL}/w/Warframes"

response = requests.get(LIST_URL)
soup = BeautifulSoup(response.text, "html.parser")

warframes = []

# Find all warframe links in the main list (A-Z)
for link in soup.find_all("a", href=True):
    href = link["href"]
    if href.startswith("/w/") and not href.startswith("/w/File:") and link.text.strip():
        name = link.text.strip()
        # Skip non-warframe links
        if name.lower() in ["overview", "lore & history", "acquisition", "attributes", "leveling up", "cosmetics", "release order", "trivia", "media", "references", "patch history"]:
            continue
        # Visit the warframe's page
        wf_url = BASE_URL + href
        wf_resp = requests.get(wf_url)
        wf_soup = BeautifulSoup(wf_resp.text, "html.parser")
        # Try to get the first image
        img_tag = wf_soup.find("img")
        img_url = img_tag["src"] if img_tag else None
        # Try to get a description (first paragraph)
        desc_tag = wf_soup.find("p")
        desc = desc_tag.text.strip() if desc_tag else ""
        warframes.append({
            "name": name,
            "url": wf_url,
            "image": img_url,
            "description": desc
        })

with open("wfdata/warframes.json", "w", encoding="utf-8") as f:
    json.dump(warframes, f, ensure_ascii=False, indent=2)

print(f"Scraped {len(warframes)} warframes and saved to wfdata/warframes.json")
