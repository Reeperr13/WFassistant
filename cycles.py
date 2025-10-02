import requests

def get_cycles():
    url = "https://api.warframestat.us/pc"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        cycles = {
            'earthCycle': data.get('earthCycle', {}),
            'cetusCycle': data.get('cetusCycle', {}),
            'vallisCycle': data.get('vallisCycle', {}),
            'zarimanCycle': data.get('zarimanCycle', {}),
            'cambionCycle': data.get('cambionCycle', {})
        }
        return cycles
    except requests.RequestException as e:
        print(f"Error fetching cycles: {e}")
        return {}

if __name__ == "__main__":
    cycles = get_cycles()
    for name, cycle in cycles.items():
        print(f"{name}: State: {cycle.get('state', 'N/A')}, Time Left: {cycle.get('timeLeft', 'N/A')}")
