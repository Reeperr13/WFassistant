import requests

def get_invasions():
    url = "https://api.warframestat.us/pc/invasions"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching invasions: {e}")
        return []

if __name__ == "__main__":
    invasions = get_invasions()
    for invasion in invasions:
        print(f"Node: {invasion.get('node', 'N/A')}, Desc: {invasion.get('desc', 'N/A')}, Completion: {invasion.get('completion', 'N/A')}")
