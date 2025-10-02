import sqlite3
import json
import os

def get_db_path():
    return os.path.join(os.path.dirname(__file__), 'wfdata', 'warframeagent.db')

def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Create tables for each data type
    c.execute('''CREATE TABLE IF NOT EXISTS warframes (id INTEGER PRIMARY KEY, name TEXT, data TEXT, image BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS weapons (id INTEGER PRIMARY KEY, name TEXT, data TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mods (id INTEGER PRIMARY KEY, name TEXT, data TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fissures (id INTEGER PRIMARY KEY, node TEXT, data TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY, node TEXT, data TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS invasions (id INTEGER PRIMARY KEY, node TEXT, data TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sortie (id INTEGER PRIMARY KEY, boss TEXT, data TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS cycles (id INTEGER PRIMARY KEY, cycle TEXT, data TEXT)''')
    conn.commit()
    # Migration: add image column to warframes if missing
    try:
        c.execute("ALTER TABLE warframes ADD COLUMN image BLOB")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.close()

def save_data(table, items, key_field):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(f"DELETE FROM {table}")
    for item in items:
        key = item.get(key_field, '')
        # For warframes, store image as BLOB if present in item['image_data']
        if table == "warframes" and "image_data" in item:
            image_bytes = item["image_data"]
            item_copy = dict(item)
            del item_copy["image_data"]
            c.execute(f"INSERT INTO {table} ({key_field}, data, image) VALUES (?, ?, ?)", (key, json.dumps(item_copy), image_bytes))
        else:
            c.execute(f"INSERT INTO {table} ({key_field}, data) VALUES (?, ?)", (key, json.dumps(item)))
    conn.commit()
    conn.close()

def load_data(table):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    if table == "warframes":
        c.execute(f"SELECT data, image FROM {table}")
        rows = c.fetchall()
        conn.close()
        result = []
        for row in rows:
            obj = json.loads(row[0])
            if row[1] is not None:
                obj["image_data"] = row[1]
            result.append(obj)
        return result
    else:
        c.execute(f"SELECT data FROM {table}")
        rows = c.fetchall()
        conn.close()
        return [json.loads(row[0]) for row in rows]

init_db()
