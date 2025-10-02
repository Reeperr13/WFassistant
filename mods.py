import requests

API_BASE = "https://api.warframestat.us"

def get_mods():
    try:
        response = requests.get(f"{API_BASE}/mods", timeout=10)
        response.raise_for_status()
        data = response.json()
        # Expecting a list of mod dicts
        if isinstance(data, list):
            return data
        return []
    except requests.RequestException as e:
        print(f"Error fetching mods: {e}")
        return []
