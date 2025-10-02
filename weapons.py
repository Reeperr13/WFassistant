import requests

API_BASE = "https://api.warframestat.us"

def get_weapons():
    try:
        response = requests.get(f"{API_BASE}/weapons", timeout=10)
        response.raise_for_status()
        data = response.json()
        # Expecting a list of weapon dicts
        if isinstance(data, list):
            return data
        return []
    except requests.RequestException as e:
        print(f"Error fetching weapons: {e}")
        return []
