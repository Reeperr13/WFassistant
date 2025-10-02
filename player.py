import requests

API_BASE = "https://api.warframestat.us/pc"

def get_profile(player_name):
    try:
        response = requests.get(f"{API_BASE}/profile/{player_name}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return {}

def get_stats(player_name):
    try:
        response = requests.get(f"{API_BASE}/profile/{player_name}/stats", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return {}
