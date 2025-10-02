import requests

def get_sortie():
    url = "https://api.warframestat.us/pc/sortie"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching sortie: {e}")
        return None

if __name__ == "__main__":
    sortie = get_sortie()
    if sortie:
        print(f"Boss: {sortie.get('boss', 'N/A')}, Faction: {sortie.get('faction', 'N/A')}, Reward Pool: {sortie.get('rewardPool', 'N/A')}")
        for variant in sortie.get('variants', []):
            print(f"  Node: {variant.get('node', 'N/A')}, Mission Type: {variant.get('missionType', 'N/A')}, Modifier: {variant.get('modifier', 'N/A')}")
