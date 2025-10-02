import requests
import time
import json
import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading
import database
import io
from PIL import Image, ImageTk

API_BASE = "https://api.warframestat.us/pc"

def fetch_api(endpoint):
    try:
        response = requests.get(f"{API_BASE}/{endpoint}?language=en", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return None

def get_fissures():
    return fetch_api("fissures") or []

def get_alerts():
    return fetch_api("alerts") or []

def get_invasions():
    return fetch_api("invasions") or []

def get_sortie():
    return fetch_api("sortie") or {}

def get_cycles():
    data = fetch_api("") or {}
    cycles = {
        'earthCycle': data.get('earthCycle', {}),
        'cetusCycle': data.get('cetusCycle', {}),
        'vallisCycle': data.get('vallisCycle', {}),
        'zarimanCycle': data.get('zarimanCycle', {}),
        'cambionCycle': data.get('cambionCycle', {})
    }
    return cycles

class WarframeAgentGUI:
    def debug_print(self, msg):
        print(f"[DEBUG] {msg}")
    def create_tab(self, tab_name, columns):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=tab_name)
        if tab_name == "Warframes":
            search_frame = tk.Frame(tab, bg="#23272A")
            search_frame.pack(fill=tk.X)
            self.search_var = tk.StringVar()
            search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Segoe UI", 12))
            search_entry.pack(side=tk.LEFT, padx=10, pady=5)
            search_btn = tk.Button(search_frame, text="Search", command=self.update_warframes)
            search_btn.pack(side=tk.LEFT, padx=5)
            self.search_var.trace_add("write", lambda *args: self.update_warframes())
            # Scrollable canvas
            canvas_frame = tk.Frame(tab, bg="#23272A")
            canvas_frame.pack(fill=tk.BOTH, expand=True)
            self.warframe_grid = tk.Canvas(canvas_frame, bg="#23272A", highlightthickness=0)
            def on_resize(event):
                # Only update if Warframes tab is selected
                if self.notebook.index(self.notebook.select()) == list(self.tabs.keys()).index("Warframes"):
                    self.update_warframes()
            self.warframe_grid.bind('<Configure>', on_resize)
            v_scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.warframe_grid.yview)
            self.warframe_grid.configure(yscrollcommand=v_scroll.set)
            self.warframe_grid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            self.warframe_grid.bind_all("<MouseWheel>", self._on_mousewheel)
            self.tabs[tab_name] = tab
            self.status_labels[tab_name] = tk.Label(tab, text="", bg="#23272A", fg="#FFFFFF")
            self.status_labels[tab_name].pack()
        else:
            tree = ttk.Treeview(tab, columns=columns, show="headings")
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=120)
            tree.pack(fill=tk.BOTH, expand=True)
            self.tabs[tab_name] = tab
            self.trees[tab_name] = tree
            self.status_labels[tab_name] = tk.Label(tab, text="")
            self.status_labels[tab_name].pack()
        if tab_name == "Player":
            self.player_name_var = tk.StringVar()
            entry = tk.Entry(tab, textvariable=self.player_name_var)
            entry.pack(side=tk.LEFT)
            btn = tk.Button(tab, text="Load Player", command=self.update_player)
            btn.pack(side=tk.LEFT)

    def _on_mousewheel(self, event):
        # For Windows, event.delta is multiples of 120
        self.warframe_grid.yview_scroll(int(-1*(event.delta/120)), "units")

    def show_warframe_details(self, warframe):
        import io
        from PIL import Image, ImageTk
        details = tk.Toplevel(self.root)
        details.title(warframe.get("name", "Warframe Details"))
        details.configure(bg="#23272A")
        # Main Image (from DB)
        img = None
        if warframe.get("image_data"):
            try:
                pil_img = Image.open(io.BytesIO(warframe["image_data"])).resize((180, 180))
                img = ImageTk.PhotoImage(pil_img)
                img_label = tk.Label(details, image=img, bg="#23272A")
                img_label.image = img
                img_label.grid(row=0, column=0, rowspan=3, padx=20, pady=20)
            except Exception:
                pass
        # Name and description
        name = warframe.get("name", "N/A")
        desc = warframe.get("description", "")
        tk.Label(details, text=name, font=("Segoe UI", 18, "bold"), fg="#FFFFFF", bg="#23272A").grid(row=0, column=1, sticky="w", pady=(20,0))
        tk.Label(details, text=desc, font=("Segoe UI", 11), fg="#CCCCCC", bg="#23272A", wraplength=400, justify="left").grid(row=1, column=1, sticky="w")
        # Stats (if available)
        stats_frame = tk.Frame(details, bg="#23272A")
        stats_frame.grid(row=2, column=1, sticky="nw", pady=10)
        stats = warframe.get("stats", {})
        if stats:
            for idx, (stat, value) in enumerate(stats.items()):
                tk.Label(stats_frame, text=f"{stat}: {value}", font=("Segoe UI", 10), fg="#FFD700", bg="#23272A").grid(row=0, column=idx, padx=10)
        else:
            tk.Label(stats_frame, text="No stats available for this Warframe.", font=("Segoe UI", 10, "italic"), fg="#CCCCCC", bg="#23272A").grid(row=0, column=0, padx=10)
        # Abilities (if available)
        abilities = warframe.get("abilities", [])
        if abilities:
            ab_frame = tk.LabelFrame(details, text="Abilities", fg="#FFFFFF", bg="#23272A", font=("Segoe UI", 12, "bold"))
            ab_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
            for ab in abilities:
                ab_name = ab.get("name", "") if isinstance(ab, dict) else str(ab)
                ab_desc = ab.get("description", "") if isinstance(ab, dict) else ""
                ab_img_data = ab.get("image_data") if isinstance(ab, dict) else None
                ab_row = tk.Frame(ab_frame, bg="#23272A")
                ab_row.pack(fill=tk.X, pady=2)
                if ab_img_data:
                    try:
                        ab_pil_img = Image.open(io.BytesIO(ab_img_data)).resize((32, 32))
                        ab_imgtk = ImageTk.PhotoImage(ab_pil_img)
                        img_label = tk.Label(ab_row, image=ab_imgtk, bg="#23272A")
                        img_label.image = ab_imgtk
                        img_label.pack(side=tk.LEFT, padx=4)
                    except Exception:
                        pass
                tk.Label(ab_row, text=ab_name, font=("Segoe UI", 10, "bold"), fg="#FFFFFF", bg="#23272A").pack(side=tk.LEFT, padx=4)
                tk.Label(ab_row, text=ab_desc, font=("Segoe UI", 10), fg="#CCCCCC", bg="#23272A", wraplength=350, justify="left").pack(side=tk.LEFT, padx=4)
        # Components (if available)
        components = warframe.get("components", [])
        if components:
            comp_frame = tk.LabelFrame(details, text="Components", fg="#FFFFFF", bg="#23272A", font=("Segoe UI", 12, "bold"))
            comp_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
            for comp in components:
                comp_name = comp.get("name", "") if isinstance(comp, dict) else str(comp)
                comp_desc = comp.get("description", "") if isinstance(comp, dict) else ""
                comp_img_data = comp.get("image_data") if isinstance(comp, dict) else None
                comp_row = tk.Frame(comp_frame, bg="#23272A")
                comp_row.pack(fill=tk.X, pady=2)
                if comp_img_data:
                    try:
                        comp_pil_img = Image.open(io.BytesIO(comp_img_data)).resize((32, 32))
                        comp_imgtk = ImageTk.PhotoImage(comp_pil_img)
                        img_label = tk.Label(comp_row, image=comp_imgtk, bg="#23272A")
                        img_label.image = comp_imgtk
                        img_label.pack(side=tk.LEFT, padx=4)
                    except Exception:
                        pass
                tk.Label(comp_row, text=comp_name, font=("Segoe UI", 10, "bold"), fg="#A3E635", bg="#23272A").pack(side=tk.LEFT, padx=4)
                tk.Label(comp_row, text=comp_desc, font=("Segoe UI", 10), fg="#CCCCCC", bg="#23272A", wraplength=350, justify="left").pack(side=tk.LEFT, padx=4)
        # Drop locations (if available)
        drops = warframe.get("drops", [])
        if drops:
            drop_frame = tk.LabelFrame(details, text="Drop locations", fg="#FFFFFF", bg="#23272A", font=("Segoe UI", 12, "bold"))
            drop_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
            for drop in drops:
                tk.Label(drop_frame, text=drop, font=("Segoe UI", 10), fg="#00BFFF", bg="#23272A", anchor="w").pack(fill=tk.X)
        details.grab_set()

    def create_item_tabs(self):
        pass

    def create_mod_tabs(self):
        pass

    def create_warframe_tabs(self):
        pass

    def create_weapon_tabs(self):
        self.create_tab("Weapon Statistics", ["Name", "Type", "Stats"])
        # Implement update methods for each tab as needed

    def __init__(self, root):
        self.debug_print("Initializing WarframeAgentGUI")
        self.root = root
        self.root.title("Warframe Agent Dashboard")
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.tabs = {}
        self.trees = {}
        self.status_labels = {}
        self.data_synced = False
        self.sync_lock = threading.Lock()
        self.create_tab("Player", ["Name", "Mastery Rank", "Last Login"])
        self.create_tab("Warframes", ["Name", "Type", "Description"])
        self.create_tab("Weapons", ["Name", "Type", "Stats"])
        self.create_tab("Mods", ["Name", "Type", "Effect"])
        self.create_tab("Fissures", ["Node", "Mission Type", "Tier", "Enemy", "ETA"])
        self.create_tab("Alerts", ["Node", "Type", "Faction", "ETA"])
        self.create_tab("Invasions", ["Node", "Desc", "Completion"])
        self.create_tab("Sortie", ["Boss", "Faction", "Reward Pool", "Variant Info"])
        self.create_tab("Cycles", ["Cycle", "State", "Time Left"])
        self.create_tab("Weapon Statistics", ["Name", "Type", "Stats"])
        # Load data before updating tabs
        db_path = database.get_db_path()
        if not os.path.exists(db_path):
            self.populate_database_first_time()
        self.load_all_data()
        self.update_warframes()
        self.update_weapons()
        self.update_mods()
        self.update_fissures()
        self.update_alerts()
        self.update_invasions()
        self.update_sortie()
        self.update_cycles()
        self.update_weapon_statistics()
    def update_weapons(self):
        self.debug_print("update_weapons called")
        tree = self.trees.get("Weapons")
        if not tree: return
        tree.delete(*tree.get_children())
        for w in getattr(self, "weapons_data", []):
            tree.insert("", "end", values=[w.get("name", "N/A"), w.get("type", "N/A"), w.get("stats", "")])
        self.status_labels["Weapons"].config(text=f"{len(getattr(self, 'weapons_data', []))} weapons loaded.")

    def update_mods(self):
        self.debug_print("update_mods called")
        tree = self.trees.get("Mods")
        if not tree: return
        tree.delete(*tree.get_children())
        for m in getattr(self, "mods_data", []):
            tree.insert("", "end", values=[m.get("name", "N/A"), m.get("type", "N/A"), m.get("effect", "")])
        self.status_labels["Mods"].config(text=f"{len(getattr(self, 'mods_data', []))} mods loaded.")

    def update_fissures(self):
        self.debug_print("update_fissures called")
        tree = self.trees.get("Fissures")
        if not tree: return
        tree.delete(*tree.get_children())
        for f in getattr(self, "fissures_data", []):
            tree.insert("", "end", values=[f.get("node", "N/A"), f.get("missionType", "N/A"), f.get("tier", "N/A"), f.get("enemy", "N/A"), f.get("eta", "")])
        self.status_labels["Fissures"].config(text=f"{len(getattr(self, 'fissures_data', []))} fissures loaded.")

    def update_alerts(self):
        self.debug_print("update_alerts called")
        tree = self.trees.get("Alerts")
        if not tree: return
        tree.delete(*tree.get_children())
        for a in getattr(self, "alerts_data", []):
            tree.insert("", "end", values=[a.get("node", "N/A"), a.get("type", "N/A"), a.get("faction", "N/A"), a.get("eta", "")])
        self.status_labels["Alerts"].config(text=f"{len(getattr(self, 'alerts_data', []))} alerts loaded.")

    def update_invasions(self):
        self.debug_print("update_invasions called")
        tree = self.trees.get("Invasions")
        if not tree: return
        tree.delete(*tree.get_children())
        for i in getattr(self, "invasions_data", []):
            tree.insert("", "end", values=[i.get("node", "N/A"), i.get("desc", "N/A"), i.get("completion", "")])
        self.status_labels["Invasions"].config(text=f"{len(getattr(self, 'invasions_data', []))} invasions loaded.")

    def update_sortie(self):
        self.debug_print("update_sortie called")
        tree = self.trees.get("Sortie")
        if not tree: return
        tree.delete(*tree.get_children())
        for s in getattr(self, "sortie_data", []):
            tree.insert("", "end", values=[s.get("boss", "N/A"), s.get("faction", "N/A"), s.get("rewardPool", "N/A"), s.get("variants", "")])
        self.status_labels["Sortie"].config(text=f"{len(getattr(self, 'sortie_data', []))} sorties loaded.")

    def update_cycles(self):
        tree = self.trees.get("Cycles")
        if not tree: return
        tree.delete(*tree.get_children())
        for c in getattr(self, "cycles_data", []):
            for cycle_name, cycle_info in c.items():
                tree.insert("", "end", values=[cycle_name, cycle_info.get("state", "N/A"), cycle_info.get("timeLeft", "")])
        self.status_labels["Cycles"].config(text=f"{len(getattr(self, 'cycles_data', []))} cycles loaded.")

    def update_weapon_statistics(self):
        tree = self.trees.get("Weapon Statistics")
        if not tree: return
        tree.delete(*tree.get_children())
        for w in getattr(self, "weapons_data", []):
            tree.insert("", "end", values=[w.get("name", "N/A"), w.get("type", "N/A"), w.get("stats", "")])
        self.status_labels["Weapon Statistics"].config(text=f"{len(getattr(self, 'weapons_data', []))} weapon stats loaded.")
        self.create_item_tabs()
        self.create_mod_tabs()
        self.create_warframe_tabs()
        self.create_weapon_tabs()
        self.refresh_interval = 3600000  # 60 minutes in ms
        db_path = database.get_db_path()
        if not os.path.exists(db_path):
            self.populate_database_first_time()
        self.load_all_data()
        self.root.after(1000, self.start_background_sync)
        refresh_btn = tk.Button(self.root, text="Refresh Database", command=self.manual_refresh_database, bg="#7289DA", fg="#FFFFFF", font=("Segoe UI", 12, "bold"))
        refresh_btn.pack(side=tk.TOP, pady=5)

    def populate_database_first_time(self):
        import warframes, weapons, mods, fissures, alerts, invasions, sortie, cycles, database
        # Fetch warframes and their images
        warframe_list = warframes.get_warframes()
        for wf in warframe_list:
            # Main image
            img_name = wf.get("imageName")
            img_url = f"https://cdn.warframestat.us/img/{img_name}" if img_name else None
            if img_url:
                try:
                    resp = requests.get(img_url, timeout=10)
                    wf["image_data"] = resp.content
                except Exception:
                    wf["image_data"] = None
            # Ability images
            if "abilities" in wf:
                for ab in wf["abilities"]:
                    ab_img = ab.get("imageName") if isinstance(ab, dict) else None
                    if ab_img:
                        ab_url = f"https://cdn.warframestat.us/img/{ab_img}"
                        try:
                            ab_resp = requests.get(ab_url, timeout=10)
                            ab["image_data"] = ab_resp.content
                        except Exception:
                            ab["image_data"] = None
            # Component images
            if "components" in wf:
                for comp in wf["components"]:
                    comp_img = comp.get("imageName") if isinstance(comp, dict) else None
                    if comp_img:
                        comp_url = f"https://cdn.warframestat.us/img/{comp_img}"
                        try:
                            comp_resp = requests.get(comp_url, timeout=10)
                            comp["image_data"] = comp_resp.content
                        except Exception:
                            comp["image_data"] = None
        # Print out the full data for each warframe before saving
        for wf in warframe_list:
            print("Saving Warframe:", json.dumps({k: v for k, v in wf.items() if k != 'image_data'}, indent=2, ensure_ascii=False))
        database.save_data("warframes", warframe_list, "name")
        database.save_data("weapons", weapons.get_weapons(), "name")
        database.save_data("mods", mods.get_mods(), "name")
        database.save_data("fissures", fissures.get_fissures(), "node")
        database.save_data("alerts", alerts.get_alerts(), "node")
        database.save_data("invasions", invasions.get_invasions(), "node")
        database.save_data("sortie", [sortie.get_sortie()], "boss")
        database.save_data("cycles", [cycles.get_cycles()], "cycle")
        self.load_all_data()

    def load_all_data(self):
        self.warframes_data = database.load_data("warframes")
        # If any warframe is missing image_data, fetch and update it immediately
        missing_images = [wf for wf in self.warframes_data if not wf.get("image_data") and wf.get("imageName")]
        if missing_images:
            for wf in missing_images:
                img_name = wf.get("imageName")
                img_url = f"https://cdn.warframestat.us/img/{img_name}" if img_name else None
                if img_url:
                    try:
                        resp = requests.get(img_url, timeout=10)
                        wf["image_data"] = resp.content
                    except Exception:
                        wf["image_data"] = None
            # Save updated warframes with images back to the database
            database.save_data("warframes", self.warframes_data, "name")
            self.warframes_data = database.load_data("warframes")
        self.weapons_data = database.load_data("weapons")
        self.mods_data = database.load_data("mods")
        self.fissures_data = database.load_data("fissures")
        self.alerts_data = database.load_data("alerts")
        self.invasions_data = database.load_data("invasions")
        self.sortie_data = database.load_data("sortie")
        self.cycles_data = database.load_data("cycles")

    def start_background_sync(self):
        self.sync_data_background()
        self.root.after(self.refresh_interval, self.start_background_sync)

    def sync_data_background(self):
        def sync():
            with self.sync_lock:
                import warframes, weapons, mods, fissures, alerts, invasions, sortie, cycles, database
                # Fetch warframes and their images for sync
                warframe_list = warframes.get_warframes()
                for wf in warframe_list:
                    # Main image
                    img_name = wf.get("imageName")
                    img_url = f"https://cdn.warframestat.us/img/{img_name}" if img_name else None
                    if img_url:
                        try:
                            resp = requests.get(img_url, timeout=10)
                            wf["image_data"] = resp.content
                        except Exception:
                            wf["image_data"] = None
                    # Ability images
                    if "abilities" in wf:
                        for ab in wf["abilities"]:
                            ab_img = ab.get("imageName") if isinstance(ab, dict) else None
                            if ab_img:
                                ab_url = f"https://cdn.warframestat.us/img/{ab_img}"
                                try:
                                    ab_resp = requests.get(ab_url, timeout=10)
                                    ab["image_data"] = ab_resp.content
                                except Exception:
                                    ab["image_data"] = None
                    # Component images
                    if "components" in wf:
                        for comp in wf["components"]:
                            comp_img = comp.get("imageName") if isinstance(comp, dict) else None
                            if comp_img:
                                comp_url = f"https://cdn.warframestat.us/img/{comp_img}"
                                try:
                                    comp_resp = requests.get(comp_url, timeout=10)
                                    comp["image_data"] = comp_resp.content
                                except Exception:
                                    comp["image_data"] = None
                database.save_data("warframes", warframe_list, "name")
                database.save_data("weapons", weapons.get_weapons(), "name")
                database.save_data("mods", mods.get_mods(), "name")
                database.save_data("fissures", fissures.get_fissures(), "node")
                database.save_data("alerts", alerts.get_alerts(), "node")
                database.save_data("invasions", invasions.get_invasions(), "node")
                database.save_data("sortie", [sortie.get_sortie()], "boss")
                database.save_data("cycles", [cycles.get_cycles()], "cycle")
                self.load_all_data()
        threading.Thread(target=sync, daemon=True).start()

    def update_warframes(self):
        warframes = self.warframes_data
        search_term = self.search_var.get().lower() if hasattr(self, 'search_var') else ""
        filtered = [wf for wf in warframes if search_term in wf.get("name", "").lower() or search_term in wf.get("description", "").lower()]
        canvas = self.warframe_grid
        canvas.delete("all")
        card_width = 200
        card_height = 280
        padding = 20
        # Responsive columns based on canvas width
        canvas_width = self.warframe_grid.winfo_width() or (5 * (card_width + padding))
        cols = max(1, canvas_width // (card_width + padding))
        images = []
        def load_image(idx, x, y, wf):
            try:
                if wf.get("image_data"):
                    pil_img = Image.open(io.BytesIO(wf["image_data"])).resize((120, 120))
                else:
                    img_name = wf.get("imageName")
                    img_url = f"https://cdn.warframestat.us/img/{img_name}" if img_name else None
                    if img_url:
                        resp = requests.get(img_url, timeout=10)
                        pil_img = Image.open(io.BytesIO(resp.content)).resize((120, 120))
                    else:
                        return
                img = ImageTk.PhotoImage(pil_img)
                images.append(img)
                def draw_image():
                    canvas.create_image(x+card_width//2, y+50+60, image=img)
                canvas.after(0, draw_image)
            except Exception as e:
                print(f"[Image Load Error] {e}")
        for idx, wf in enumerate(filtered):
            x = padding + (idx % cols) * (card_width + padding)
            y = padding + (idx // cols) * (card_height + padding)
            card = canvas.create_rectangle(x, y, x+card_width, y+card_height, fill="#2C2F33", outline="#7289DA", width=2)
            name = wf.get("name", "N/A")
            name_id = canvas.create_text(x+card_width//2, y+20, text=name, fill="#FFFFFF", font=("Segoe UI", 12, "bold"))
            threading.Thread(target=load_image, args=(idx, x, y, wf), daemon=True).start()
            desc = wf.get("description", "")
            desc_id = canvas.create_text(x+card_width//2, y+200, text=desc[:120]+("..." if len(desc)>120 else ""), fill="#CCCCCC", font=("Segoe UI", 9), width=card_width-20)
            # Add 'More...' button at the bottom of the card
            btn_x = x + card_width//2
            btn_y = y + card_height - 30
            btn_rect = canvas.create_rectangle(x+card_width//2-40, btn_y-12, x+card_width//2+40, btn_y+12, fill="#7289DA", outline="#23272A", width=1)
            btn_text = canvas.create_text(btn_x, btn_y, text="More...", fill="#FFFFFF", font=("Segoe UI", 10, "bold"))
            # Bind click to card, name, description, and button
            for tag in [card, name_id, desc_id, btn_rect, btn_text]:
                canvas.tag_bind(tag, "<Button-1>", lambda e, wf=wf: self.show_warframe_details_inplace(wf))
        self.status_labels["Warframes"].config(text=f"{len(filtered)} warframes loaded.")
        canvas.images = images
        total_rows = (len(filtered) + cols - 1) // cols
        canvas.config(scrollregion=(0, 0, cols*(card_width+padding), total_rows*(card_height+padding)+padding))

    def show_warframe_details_inplace(self, warframe):
        # Clear grid and show details in a scrollable frame
        canvas = self.warframe_grid
        canvas.delete("all")
        details_frame = tk.Frame(canvas, bg="#23272A")
        canvas.create_window(0, 0, window=details_frame, anchor="nw")
        import requests
        from PIL import Image, ImageTk
        import io
        img = None
        if warframe.get("image_data"):
            try:
                pil_img = Image.open(io.BytesIO(warframe["image_data"])).resize((180, 180))
                img = ImageTk.PhotoImage(pil_img)
                img_label = tk.Label(details_frame, image=img, bg="#23272A")
                img_label.image = img
                img_label.grid(row=0, column=0, rowspan=3, padx=20, pady=20)
            except Exception:
                pass
        # Abilities (if available)
        abilities = warframe.get("abilities", [])
        if abilities:
            ab_frame = tk.LabelFrame(details_frame, text="Abilities", fg="#FFFFFF", bg="#23272A", font=("Segoe UI", 12, "bold"))
            ab_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
            for ab in abilities:
                ab_name = ab.get("name", "") if isinstance(ab, dict) else str(ab)
                ab_desc = ab.get("description", "") if isinstance(ab, dict) else ""
                ab_img_data = ab.get("image_data") if isinstance(ab, dict) else None
                ab_row = tk.Frame(ab_frame, bg="#23272A")
                ab_row.pack(fill=tk.X, pady=2)
                if ab_img_data:
                    try:
                        ab_pil_img = Image.open(io.BytesIO(ab_img_data)).resize((32, 32))
                        ab_imgtk = ImageTk.PhotoImage(ab_pil_img)
                        img_label = tk.Label(ab_row, image=ab_imgtk, bg="#23272A")
                        img_label.image = ab_imgtk
                        img_label.pack(side=tk.LEFT, padx=4)
                    except Exception:
                        pass
                tk.Label(ab_row, text=ab_name, font=("Segoe UI", 10, "bold"), fg="#FFFFFF", bg="#23272A").pack(side=tk.LEFT, padx=4)
                tk.Label(ab_row, text=ab_desc, font=("Segoe UI", 10), fg="#CCCCCC", bg="#23272A", wraplength=350, justify="left").pack(side=tk.LEFT, padx=4)
        # Components (if available)
        components = warframe.get("components", [])
        if components:
            comp_frame = tk.LabelFrame(details_frame, text="Components", fg="#FFFFFF", bg="#23272A", font=("Segoe UI", 12, "bold"))
            comp_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
            for comp in components:
                comp_name = comp.get("name", "") if isinstance(comp, dict) else str(comp)
                comp_desc = comp.get("description", "") if isinstance(comp, dict) else ""
                comp_img_data = comp.get("image_data") if isinstance(comp, dict) else None
                comp_row = tk.Frame(comp_frame, bg="#23272A")
                comp_row.pack(fill=tk.X, pady=2)
                if comp_img_data:
                    try:
                        comp_pil_img = Image.open(io.BytesIO(comp_img_data)).resize((32, 32))
                        comp_imgtk = ImageTk.PhotoImage(comp_pil_img)
                        img_label = tk.Label(comp_row, image=comp_imgtk, bg="#23272A")
                        img_label.image = comp_imgtk
                        img_label.pack(side=tk.LEFT, padx=4)
                    except Exception:
                        pass
                tk.Label(comp_row, text=comp_name, font=("Segoe UI", 10, "bold"), fg="#A3E635", bg="#23272A").pack(side=tk.LEFT, padx=4)
                tk.Label(comp_row, text=comp_desc, font=("Segoe UI", 10), fg="#CCCCCC", bg="#23272A", wraplength=350, justify="left").pack(side=tk.LEFT, padx=4)
        # Drop locations (if available)
        drops = warframe.get("drops", [])
        if drops:
            drop_frame = tk.LabelFrame(details_frame, text="Drop locations", fg="#FFFFFF", bg="#23272A", font=("Segoe UI", 12, "bold"))
            drop_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
            for drop in drops:
                tk.Label(drop_frame, text=drop, font=("Segoe UI", 10), fg="#00BFFF", bg="#23272A", anchor="w").pack(fill=tk.X)
        name = warframe.get("name", "N/A")
        desc = warframe.get("description", "")
        tk.Label(details_frame, text=name, font=("Segoe UI", 18, "bold"), fg="#FFFFFF", bg="#23272A").grid(row=0, column=1, sticky="w", pady=(20,0))
        tk.Label(details_frame, text=desc, font=("Segoe UI", 11), fg="#CCCCCC", bg="#23272A", wraplength=400, justify="left").grid(row=1, column=1, sticky="w")
        back_btn = tk.Button(details_frame, text="Back", command=self.update_warframes, bg="#7289DA", fg="#FFFFFF", font=("Segoe UI", 12, "bold"))
        back_btn.grid(row=0, column=2, padx=10, pady=10)
        # Stats (if available)
        stats_frame = tk.Frame(details_frame, bg="#23272A")
        stats_frame.grid(row=2, column=1, sticky="nw", pady=10)
        stats = warframe.get("stats", {})
        if stats:
            for idx, (stat, value) in enumerate(stats.items()):
                tk.Label(stats_frame, text=f"{stat}: {value}", font=("Segoe UI", 10), fg="#FFD700", bg="#23272A").grid(row=0, column=idx, padx=10)
        else:
            tk.Label(stats_frame, text="No stats available for this Warframe.", font=("Segoe UI", 10, "italic"), fg="#CCCCCC", bg="#23272A").grid(row=0, column=0, padx=10)
        # Abilities (if available)
        abilities = warframe.get("abilities", [])
        if abilities:
            ab_frame = tk.LabelFrame(details_frame, text="Abilities", fg="#FFFFFF", bg="#23272A", font=("Segoe UI", 12, "bold"))
            ab_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
            for ab in abilities:
                ab_name = ab.get("name", "") if isinstance(ab, dict) else str(ab)
                ab_desc = ab.get("description", "") if isinstance(ab, dict) else ""
                ab_img = ab.get("imageName", None) if isinstance(ab, dict) else None
                ab_row = tk.Frame(ab_frame, bg="#23272A")
                ab_row.pack(fill=tk.X, pady=2)
                if ab_img:
                    try:
                        img_url = f"https://cdn.warframestat.us/img/{ab_img}"
                        resp = requests.get(img_url, timeout=10)
                        pil_img = Image.open(io.BytesIO(resp.content)).resize((32, 32))
                        ab_imgtk = ImageTk.PhotoImage(pil_img)
                        img_label = tk.Label(ab_row, image=ab_imgtk, bg="#23272A")
                        img_label.image = ab_imgtk
                        img_label.pack(side=tk.LEFT, padx=4)
                    except Exception:
                        pass
                tk.Label(ab_row, text=ab_name, font=("Segoe UI", 10, "bold"), fg="#FFFFFF", bg="#23272A").pack(side=tk.LEFT, padx=4)
                tk.Label(ab_row, text=ab_desc, font=("Segoe UI", 10), fg="#CCCCCC", bg="#23272A", wraplength=350, justify="left").pack(side=tk.LEFT, padx=4)
        # Components (if available)
        components = warframe.get("components", [])
        if components:
            comp_frame = tk.LabelFrame(details_frame, text="Components", fg="#FFFFFF", bg="#23272A", font=("Segoe UI", 12, "bold"))
            comp_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
            for comp in components:
                comp_name = comp.get("name", "") if isinstance(comp, dict) else str(comp)
                comp_desc = comp.get("description", "") if isinstance(comp, dict) else ""
                comp_img = comp.get("imageName", None) if isinstance(comp, dict) else None
                comp_row = tk.Frame(comp_frame, bg="#23272A")
                comp_row.pack(fill=tk.X, pady=2)
                if comp_img:
                    try:
                        img_url = f"https://cdn.warframestat.us/img/{comp_img}"
                        resp = requests.get(img_url, timeout=10)
                        pil_img = Image.open(io.BytesIO(resp.content)).resize((32, 32))
                        comp_imgtk = ImageTk.PhotoImage(pil_img)
                        img_label = tk.Label(comp_row, image=comp_imgtk, bg="#23272A")
                        img_label.image = comp_imgtk
                        img_label.pack(side=tk.LEFT, padx=4)
                    except Exception:
                        pass
                tk.Label(comp_row, text=comp_name, font=("Segoe UI", 10, "bold"), fg="#A3E635", bg="#23272A").pack(side=tk.LEFT, padx=4)
                tk.Label(comp_row, text=comp_desc, font=("Segoe UI", 10), fg="#CCCCCC", bg="#23272A", wraplength=350, justify="left").pack(side=tk.LEFT, padx=4)
        # Drop locations (if available)
        drops = warframe.get("drops", [])
        if drops:
            drop_frame = tk.LabelFrame(details_frame, text="Drop locations", fg="#FFFFFF", bg="#23272A", font=("Segoe UI", 12, "bold"))
            drop_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
            for drop in drops:
                tk.Label(drop_frame, text=drop, font=("Segoe UI", 10), fg="#00BFFF", bg="#23272A", anchor="w").pack(fill=tk.X)
        details_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    def update_player(self):
        try:
            from player import get_profile
        except ImportError:
            def get_profile(name):
                return {}
        player_name = self.player_name_var.get().strip()
        if not player_name:
            self.status_labels["Player"].config(text="Enter a player name.")
            return
        profile = get_profile(player_name)
        tree = self.trees["Player"]
        for i in tree.get_children():
            tree.delete(i)
        if profile:
            name = profile.get("name", player_name)
            mr = profile.get("masteryRank", "N/A")
            last_login = profile.get("lastLogin", "N/A")
            tree.insert("", "end", values=(name, mr, last_login))
            self.status_labels["Player"].config(text=f"Player '{name}' loaded.")
        else:
            self.status_labels["Player"].config(text=f"No data found for '{player_name}'.")
    def update_all(self):
        self.update_fissures()
        self.update_alerts()
        self.update_invasions()
        self.update_sortie()
        self.update_cycles()
        self.update_warframes()
        self.update_weapons()
        self.update_mods()
        self.update_player()
    def update_fissures(self):
        fissures = self.fissures_data
        tree = self.trees["Fissures"]
        for i in tree.get_children():
            tree.delete(i)
        for fissure in fissures:
            node = fissure.get("node", "N/A")
            mission_type = fissure.get("missionType", "N/A")
            tier = fissure.get("tier", "N/A")
            enemy = fissure.get("enemy", "N/A")
            eta = fissure.get("eta", "N/A")
            tree.insert("", "end", values=(node, mission_type, tier, enemy, eta))
        self.status_labels["Fissures"].config(text=f"{len(fissures)} active fissures found.")
    def update_alerts(self):
        alerts = self.alerts_data
        tree = self.trees["Alerts"]
        for i in tree.get_children():
            tree.delete(i)
        for alert in alerts:
            mission = alert.get('mission', {})
            node = mission.get('node', 'N/A')
            type_ = mission.get('type', 'N/A')
            faction = mission.get('faction', 'N/A')
            eta = alert.get('eta', 'N/A')
            tree.insert("", "end", values=(node, type_, faction, eta))
        self.status_labels["Alerts"].config(text=f"{len(alerts)} active alerts found.")
    def update_invasions(self):
        invasions = self.invasions_data
        tree = self.trees["Invasions"]
        for i in tree.get_children():
            tree.delete(i)
        for invasion in invasions:
            node = invasion.get('node', 'N/A')
            desc = invasion.get('desc', 'N/A')
            completion = invasion.get('completion', 'N/A')
            tree.insert("", "end", values=(node, desc, completion))
        self.status_labels["Invasions"].config(text=f"{len(invasions)} active invasions found.")
    def update_sortie(self):
        sortie = self.sortie_data[0] if self.sortie_data else {}
        tree = self.trees["Sortie"]
        for i in tree.get_children():
            tree.delete(i)
        if sortie:
            boss = sortie.get('boss', 'N/A')
            faction = sortie.get('faction', 'N/A')
            reward_pool = sortie.get('rewardPool', 'N/A')
            variants = sortie.get('variants', [])
            for variant in variants:
                variant_info = f"Node: {variant.get('node', 'N/A')}, Type: {variant.get('missionType', 'N/A')}, Modifier: {variant.get('modifier', 'N/A')}"
                tree.insert("", "end", values=(boss, faction, reward_pool, variant_info))
            self.status_labels["Sortie"].config(text="Sortie data loaded.")
        else:
            self.status_labels["Sortie"].config(text="No sortie data found.")
    def update_cycles(self):
        cycles = self.cycles_data[0] if self.cycles_data else {}
        tree = self.trees["Cycles"]
        for i in tree.get_children():
            tree.delete(i)
        for name, cycle in cycles.items():
            state = cycle.get('state', 'N/A')
            time_left = cycle.get('timeLeft', 'N/A')
            tree.insert("", "end", values=(name, state, time_left))
        self.status_labels["Cycles"].config(text="Cycle data loaded.")
    def update_weapons(self):
        weapons = self.weapons_data
        tree = self.trees["Weapons"]
        for i in tree.get_children():
            tree.delete(i)
        for weapon in weapons:
            name = weapon.get("name", "N/A")
            type_ = weapon.get("type", "N/A")
            stats = weapon.get("description", "N/A")
            tree.insert("", "end", values=(name, type_, stats))
        self.status_labels["Weapons"].config(text=f"{len(weapons)} weapons found.")
    def update_mods(self):
        mods = self.mods_data
        tree = self.trees["Mods"]
        for i in tree.get_children():
            tree.delete(i)
        for mod in mods:
            name = mod.get("name", "N/A")
            type_ = mod.get("type", "N/A")
            effect = mod.get("description", mod.get("compatName", "N/A"))
            tree.insert("", "end", values=(name, type_, effect))
        self.status_labels["Mods"].config(text=f"{len(mods)} mods found.")
    def manual_refresh_database(self):
        self.sync_data_background()
        self.root.after(3000, self.load_all_data)
        self.root.after(3500, self.update_all)
def fetch_and_save_all_data():
    import json
    import os
    from warframes import get_warframes
    from weapons import get_weapons
    from mods import get_mods
    from items import get_items
    from fissures import get_fissures
    from alerts import get_alerts
    from invasions import get_invasions
    from sortie import get_sortie
    from cycles import get_cycles
    from player import get_profile, get_stats
    from rivens import get_rivens
    from arcanes import get_arcanes
    from translations import get_translations

    data_map = {
        "warframes": get_warframes(),
        "weapons": get_weapons(),
        "mods": get_mods(),
        "items": get_items(),
        "fissures": get_fissures(),
        "alerts": get_alerts(),
        "invasions": get_invasions(),
        "sortie": get_sortie(),
        "cycles": get_cycles(),
        "rivens": get_rivens(),
        "arcanes": get_arcanes(),
        "translations": get_translations(),
        # Player data requires a username, so you may need to pass it in
        # "player_profile": get_profile("your_username"),
        # "player_stats": get_stats("your_username"),
    }
    outdir = os.path.join(os.path.dirname(__file__), "wfdata")
    os.makedirs(outdir, exist_ok=True)
    for key, value in data_map.items():
        with open(os.path.join(outdir, f"{key}.json"), "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
    print(f"Saved all data to {outdir}")

if __name__ == "__main__":
    try:
        fetch_and_save_all_data()
        root = tk.Tk()
        app = WarframeAgentGUI(root)
        root.mainloop()
    except Exception as e:
        import traceback
        print("\n[ERROR] Unhandled exception:")
        traceback.print_exc()
