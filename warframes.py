import requests

API_BASE = "https://api.warframestat.us"

def get_warframes():
    try:
        response = requests.get(f"{API_BASE}/warframes", timeout=10)
        response.raise_for_status()
        data = response.json()
        # Expecting a list of warframe dicts
        if isinstance(data, list):
            for wf in data:
                wf["stats"] = {
                    "Armor": wf.get("armor"),
                    "Health": wf.get("health"),
                    "Shield": wf.get("shield"),
                    "Power": wf.get("power"),
                    "Sprint Speed": wf.get("sprint"),
                    "Stamina": wf.get("stamina"),
                    "Mastery Req": wf.get("masteryReq"),
                }
            return data
        return []
    except requests.RequestException as e:
        print(f"Error fetching warframes: {e}")
        return []
