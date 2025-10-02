import requests

def get_alerts():
    url = "https://api.warframestat.us/pc/alerts"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching alerts: {e}")
        return []

if __name__ == "__main__":
    alerts = get_alerts()
    for alert in alerts:
        mission = alert.get('mission', {})
        print(f"Node: {mission.get('node', 'N/A')}, Type: {mission.get('type', 'N/A')}, Faction: {mission.get('faction', 'N/A')}, ETA: {alert.get('eta', 'N/A')}")
