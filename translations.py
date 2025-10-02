import requests

API_BASE = "https://api.warframestat.us/pc"

def get_translations():
    try:
        response = requests.get(f"{API_BASE}/translations", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []
