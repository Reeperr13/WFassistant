import requests

API_BASE = "https://api.warframestat.us/pc"

def get_items():
    try:
        response = requests.get(f"{API_BASE}/items", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []
