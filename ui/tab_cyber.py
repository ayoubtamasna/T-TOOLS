import customtkinter as ctk
import subprocess
import threading
import psutil
import socket
import pythoncom
from languages.translations import get

try:
    import wmi
except ImportError:
    wmi = None

COLORS = {
    "bg_dark":   "#0A0F1E",
    "bg_card":   "#0D1B2A",
    "accent":    "#1E90FF",
    "text_white":"#E8F4FD",
    "text_gray": "#8BA3BF",
    "bar_bg":    "#1A2744",
    "selected":  "#1E3A5F",
    "green":     "#00C896",
    "orange":    "#FFA500",
    "red":       "#FF4444",
}

class CyberTab:
    def __init__(self, parent):
        self.parent = parent

        self.top_bar = ctk.CTkFrame(parent, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=15, pady=(10, 0))

        self.refresh_btn = ctk.CTkButton(
            self.top_bar,
            text=get("refresh"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=COLORS["selected"],
            hover_color=COLORS["bar_bg"],
            text_color=COLORS["accent"],
            corner_radius=8,
            width=120, height=32,
            command=self._refresh
        )
        self.refresh_btn.pack(side="right")

        self.frame = ctk.CTkScrollableFrame(
            parent,
            fg_color=COLORS["bg_dark"],
            scrollbar_button_color=COLORS["bar_bg"],
        )
        self.frame.pack(fill="both", expand=True, padx=15, pady=(5, 15))
        self._show_loading()
        threading.Thread(target=self._load_data, daemon=True).start()

    def _refresh(self):
        self.refresh_btn.configure(text="⏳ ...", state="disabled")
        for widget in self.frame.winfo_children():
            widget.destroy()
        self._show_loading()
        threading.Thread(target=self._load_data, daemon=True).start()

    def _show_loading(self):
        self.loading_label = ctk.CTkLabel(
            self.frame,
            text=get("scanning_hw"),
            font=ctk.CTkFont(family="Segoe UI", size=16),
            text_color=COLORS["text_gray"]
        )
        self.loading_label.pack(expand=True, pady=100)

    def _load_data(self):
        pythoncom.CoInitialize()
        c = wmi.WMI() if wmi else None
        data = {
            "firewall":    self._get_firewall_status(),
            "antivirus":   self._get_antivirus(c),
            "updates":     self._get_windows_update(c),
            "users":       self._get_logged_users(),
            "processes":   self._get_suspicious_processes(),
            "connections": self._get_active_connections(),
            "shares":      self._get_shared_folders(c),
        }
        self.frame.after(0, lambda: self._build_ui(data))

    def _get_firewall_status(self):
        try:
            result = subprocess.run(["netsh", "advfirewall", "show", "allprofiles", "state"],
                                    capture_output=True, text=True, timeout=5)
            output = result.stdout
            profiles = {}
            for line in output.splitlines():
                if "Domain Profile" in line:
                    profiles["Domain"] = "ON" if "ON" in output.split("Domain Profile")[1][:100] else "OFF"
                elif "Private Profile" in line:
                    profiles["Private"] = "ON" if "ON" in output.split("Private Profile")[1][:100] else "OFF"
                elif "Public Profile" in line:
                    profiles["Public"] = "ON" if "ON" in output.split("Public Profile")[1][:100] else "OFF"
            return profiles if profiles else {"Status": "Unknown"}
        except:
            return {"Status": "Unknown"}

    def _get_antivirus(self, c):
        if not c:
            return [{"name": "Unknown", "enabled": False, "updated": False}]
        try:
            wmi_security = wmi.WMI(namespace="root\\SecurityCenter2")
            avs = wmi_security.AntiVirusProduct()
            result = []
            for av in avs:
                state = av.productState
                enabled = (state >> 12 & 0xF) == 1
                updated = (state >> 4 & 0xFF) == 0
                result.append({"name": av.displayName, "enabled": enabled, "updated": updated})
            return result if result else [{"name": "None detected", "enabled": False, "updated": False}]
        except:
            return [{"name": "Unknown", "enabled": False, "updated": False}]

    def _get_windows_update(self, c):
        if not c:
            return {"count": 0, "latest": "Unknown"}
        try:
            updates = c.Win32_QuickFixEngineering()
            latest = sorted(updates, key=lambda x: x.InstalledOn or "", reverse=True)
            return {"count": len(updates), "latest": latest[0].InstalledOn if latest and latest[0].InstalledOn else "Unknown"}
        except:
            return {"count": 0, "latest": "Unknown"}

    def _get_logged_users(self):
        try:
            result = subprocess.run(["query", "user"], capture_output=True, text=True, timeout=5)
            lines = result.stdout.strip().splitlines()
            users = []
            for line in lines[1:]:
                parts = line.split()
                if parts:
                    users.append(parts[0].replace(">", ""))
            return users if users else ["No active sessions"]
        except:
            return ["Unknown"]

    def _get_suspicious_processes(self):
        suspicious_names = ["netcat", "nc.exe", "nmap", "wireshark", "mimikatz",
                            "psexec", "meterpreter", "cobaltstrike", "empire"]
        found = []
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                name = proc.info['name'].lower()
                if any(s in name for s in suspicious_names):
                    found.append(f"{proc.info['name']} (PID: {proc.info['pid']})")
            except:
                pass
        return found

    def _get_active_connections(self):
        connections = []
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'ESTABLISHED' and conn.raddr:
                    try:
                        proc_name = psutil.Process(conn.pid).name() if conn.pid else "Unknown"
                    except:
                        proc_name = "Unknown"
                    connections.append({
                        "local":   f"{conn.laddr.ip}:{conn.laddr.port}",
                        "remote":  f"{conn.raddr.ip}:{conn.raddr.port}",
                        "process": proc_name,
                    })
        except:
            pass
        return connections[:15]

    def _get_shared_folders(self, c):
        if not c:
            return []
        try:
            shares = c.Win32_Share()
            return [{"name": s.Name, "path": s.Path or "N/A", "type": s.Type} for s in shares]
        except:
            return []

    def _build_ui(self, data):
        self.loading_label.destroy()
        self.refresh_btn.configure(text=get("refresh"), state="normal")

        ctk.CTkLabel(self.frame, text=get("cyber_title"),
                     font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
                     text_color=COLORS["text_white"]).pack(anchor="w", pady=(0, 15))

        self._build_firewall(data["firewall"])
        self._build_antivirus(data["antivirus"])
        self._build_updates(data["updates"])
        self._build_section_list(get("users"), data["users"], COLORS["accent"])
        self._build_suspicious(data["processes"])
        self._build_connections(data["connections"])
        self._build_shares(data["shares"])

    def _build_firewall(self, firewall):
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=8)
        header = ctk.CTkFrame(card, fg_color=COLORS["selected"], corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(header, text=get("firewall"),
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=COLORS["text_white"]).pack(side="left", padx=15, pady=8)
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=(5, 12))
        for profile, status in firewall.items():
            col = ctk.CTkFrame(row, fg_color=COLORS["bar_bg"], corner_radius=8)
            col.pack(side="left", padx=5, pady=5, ipadx=10, ipady=5)
            is_on = status == "ON"
            color = COLORS["green"] if is_on else COLORS["red"]
            icon = "✅" if is_on else "❌"
            ctk.CTkLabel(col, text=f"{icon} {profile}",
                         font=ctk.CTkFont(family="Segoe UI", size=12),
                         text_color=color).pack(padx=10, pady=5)

    def _build_antivirus(self, avlist):
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=8)
        header = ctk.CTkFrame(card, fg_color=COLORS["selected"], corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(header, text=get("antivirus"),
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=COLORS["text_white"]).pack(side="left", padx=15, pady=8)
        for av in avlist:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=5)
            ctk.CTkLabel(row, text=av["name"],
                         font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                         text_color=COLORS["text_white"], width=250, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text="✅ Enabled" if av["enabled"] else "❌ Disabled",
                         font=ctk.CTkFont(family="Segoe UI", size=12),
                         text_color=COLORS["green"] if av["enabled"] else COLORS["red"]).pack(side="left", padx=20)
            ctk.CTkLabel(row, text="✅ Updated" if av["updated"] else "⚠️ Outdated",
                         font=ctk.CTkFont(family="Segoe UI", size=12),
                         text_color=COLORS["green"] if av["updated"] else COLORS["orange"]).pack(side="left")
        ctk.CTkFrame(card, height=1, fg_color=COLORS["bar_bg"]).pack(fill="x", padx=15, pady=8)

    def _build_updates(self, updates):
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=8)
        header = ctk.CTkFrame(card, fg_color=COLORS["selected"], corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(header, text=get("updates"),
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=COLORS["text_white"]).pack(side="left", padx=15, pady=8)
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=(5, 12))
        ctk.CTkLabel(row, text="📦  Installed: ",
                     font=ctk.CTkFont(family="Segoe UI", size=12),
                     text_color=COLORS["text_gray"]).pack(side="left")
        ctk.CTkLabel(row, text=str(updates["count"]),
                     font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                     text_color=COLORS["accent"]).pack(side="left")
        ctk.CTkLabel(row, text=f"   📅  Last: {updates['latest']}",
                     font=ctk.CTkFont(family="Segoe UI", size=12),
                     text_color=COLORS["text_gray"]).pack(side="left", padx=20)

    def _build_section_list(self, title, items, color):
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=8)
        header = ctk.CTkFrame(card, fg_color=COLORS["selected"], corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(header, text=title,
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=COLORS["text_white"]).pack(side="left", padx=15, pady=8)
        for item in items:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=3)
            ctk.CTkLabel(row, text=f"•  {item}",
                         font=ctk.CTkFont(family="Segoe UI", size=12),
                         text_color=color, anchor="w").pack(fill="x")
        ctk.CTkFrame(card, height=1, fg_color=COLORS["bar_bg"]).pack(fill="x", padx=15, pady=8)

    def _build_suspicious(self, processes):
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=8)
        header = ctk.CTkFrame(card, fg_color=COLORS["selected"], corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(header, text=get("suspicious"),
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=COLORS["text_white"]).pack(side="left", padx=15, pady=8)
        if not processes:
            ctk.CTkLabel(card, text=f"✅  {get('no_alerts')}",
                         font=ctk.CTkFont(family="Segoe UI", size=12),
                         text_color=COLORS["green"]).pack(pady=10)
        else:
            for proc in processes:
                ctk.CTkLabel(card, text=f"🔴  {proc}",
                             font=ctk.CTkFont(family="Segoe UI", size=12),
                             text_color=COLORS["red"]).pack(anchor="w", padx=15, pady=3)
        ctk.CTkFrame(card, height=1, fg_color=COLORS["bar_bg"]).pack(fill="x", padx=15, pady=8)

    def _build_connections(self, connections):
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=8)
        header = ctk.CTkFrame(card, fg_color=COLORS["selected"], corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(header, text=f"{get('connections')} ({len(connections)})",
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=COLORS["text_white"]).pack(side="left", padx=15, pady=8)
        if not connections:
            ctk.CTkLabel(card, text="No active connections",
                         font=ctk.CTkFont(family="Segoe UI", size=12),
                         text_color=COLORS["text_gray"]).pack(pady=10)
        else:
            for conn in connections:
                row = ctk.CTkFrame(card, fg_color=COLORS["bar_bg"], corner_radius=6)
                row.pack(fill="x", padx=12, pady=3)
                inner = ctk.CTkFrame(row, fg_color="transparent")
                inner.pack(fill="x", padx=10, pady=6)
                ctk.CTkLabel(inner, text=conn["process"],
                             font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                             text_color=COLORS["accent"], width=120, anchor="w").pack(side="left")
                ctk.CTkLabel(inner, text=conn["local"],
                             font=ctk.CTkFont(family="Segoe UI", size=11),
                             text_color=COLORS["text_gray"], width=150, anchor="w").pack(side="left")
                ctk.CTkLabel(inner, text="→",
                             font=ctk.CTkFont(family="Segoe UI", size=11),
                             text_color=COLORS["text_gray"]).pack(side="left")
                ctk.CTkLabel(inner, text=conn["remote"],
                             font=ctk.CTkFont(family="Segoe UI", size=11),
                             text_color=COLORS["orange"], anchor="w").pack(side="left", padx=5)
        ctk.CTkFrame(card, height=1, fg_color=COLORS["bar_bg"]).pack(fill="x", padx=15, pady=8)

    def _build_shares(self, shares):
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=8)
        header = ctk.CTkFrame(card, fg_color=COLORS["selected"], corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(header, text=f"{get('shares')} ({len(shares)})",
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=COLORS["text_white"]).pack(side="left", padx=15, pady=8)
        if not shares:
            ctk.CTkLabel(card, text="No shared folders",
                         font=ctk.CTkFont(family="Segoe UI", size=12),
                         text_color=COLORS["text_gray"]).pack(pady=10)
        else:
            for share in shares:
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=15, pady=3)
                ctk.CTkLabel(row, text=f"📂  {share['name']}",
                             font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                             text_color=COLORS["orange"], width=120, anchor="w").pack(side="left")
                ctk.CTkLabel(row, text=share["path"],
                             font=ctk.CTkFont(family="Segoe UI", size=12),
                             text_color=COLORS["text_gray"], anchor="w").pack(side="left", padx=10)
        ctk.CTkFrame(card, height=1, fg_color=COLORS["bar_bg"]).pack(fill="x", padx=15, pady=8)