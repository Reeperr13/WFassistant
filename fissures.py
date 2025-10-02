import requests

def get_fissures():
    url = "https://api.warframestat.us/pc/fissures"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching fissures: {e}")
        return []

if __name__ == "__main__":
    fissures = get_fissures()
    for fissure in fissures:
        print(f"Node: {fissure.get('node', 'N/A')}, Mission: {fissure.get('missionType', 'N/A')}, Tier: {fissure.get('tier', 'N/A')}, ETA: {fissure.get('eta', 'N/A')}")
