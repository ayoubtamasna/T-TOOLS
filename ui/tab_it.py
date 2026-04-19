import customtkinter as ctk
import subprocess
import threading
import psutil
import pythoncom
import wmi
from datetime import datetime
from languages.translations import get

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

class ITTab:
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
        c = wmi.WMI()
        data = {
            "os":      self._get_os_details(c),
            "uptime":  self._get_uptime(),
            "software":self._get_installed_software(c),
            "services":self._get_services(),
            "startup": self._get_startup_programs(c),
            "events":  self._get_recent_events(),
        }
        self.frame.after(0, lambda: self._build_ui(data))

    def _get_os_details(self, c):
        try:
            os_info = c.Win32_OperatingSystem()[0]
            return {
                "name":          os_info.Caption.strip(),
                "version":       os_info.Version,
                "build":         os_info.BuildNumber,
                "architecture":  os_info.OSArchitecture,
                "serial":        os_info.SerialNumber,
                "install_date":  os_info.InstallDate[:8] if os_info.InstallDate else "N/A",
                "registered_to": os_info.RegisteredUser or "N/A",
            }
        except:
            return {}

    def _get_uptime(self):
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = (datetime.now() - datetime.fromtimestamp(boot_time)).total_seconds()
            days    = int(uptime_seconds // 86400)
            hours   = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            boot_str = datetime.fromtimestamp(boot_time).strftime("%Y-%m-%d %H:%M")
            return {"days": days, "hours": hours, "minutes": minutes, "boot_time": boot_str}
        except:
            return {"days": 0, "hours": 0, "minutes": 0, "boot_time": "Unknown"}

    def _get_installed_software(self, c):
        try:
            software = c.Win32_Product()
            result = []
            for s in sorted(software, key=lambda x: x.Name or ""):
                result.append({"name": s.Name or "Unknown", "version": s.Version or "N/A", "vendor": s.Vendor or "N/A"})
            return result[:30]
        except:
            return []

    def _get_services(self):
        try:
            services = []
            for svc in psutil.win_service_iter():
                try:
                    info = svc.as_dict()
                    if info["status"] == "running":
                        services.append({"name": info["display_name"], "status": info["status"], "start": info["start_type"]})
                except:
                    pass
            return services[:20]
        except:
            return []

    def _get_startup_programs(self, c):
        try:
            startup = c.Win32_StartupCommand()
            return [{"name": s.Name or "Unknown", "command": s.Command or "N/A", "location": s.Location or "N/A"} for s in startup]
        except:
            return []

    def _get_recent_events(self):
        try:
            result = subprocess.run(["wevtutil", "qe", "System", "/c:10", "/rd:true", "/f:text"],
                                    capture_output=True, text=True, timeout=10)
            lines = result.stdout.strip().splitlines()
            events = []
            current = {}
            for line in lines:
                line = line.strip()
                if line.startswith("Event["):
                    if current:
                        events.append(current)
                    current = {}
                elif "Date:" in line:
                    current["date"] = line.split("Date:")[-1].strip()[:19]
                elif "Level:" in line:
                    current["level"] = line.split("Level:")[-1].strip()
                elif "Description:" in line:
                    current["desc"] = line.split("Description:")[-1].strip()[:60]
            if current:
                events.append(current)
            return events[:10]
        except:
            return []

    def _build_ui(self, data):
        self.loading_label.destroy()
        self.refresh_btn.configure(text=get("refresh"), state="normal")

        ctk.CTkLabel(self.frame, text=get("it_title"),
                     font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
                     text_color=COLORS["text_white"]).pack(anchor="w", pady=(0, 15))

        self._build_os_card(data["os"], data["uptime"])
        self._build_services(data["services"])
        self._build_startup(data["startup"])
        self._build_software(data["software"])
        self._build_events(data["events"])

    def _build_os_card(self, os_info, uptime):
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=8)
        header = ctk.CTkFrame(card, fg_color=COLORS["selected"], corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(header, text=get("os"),
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=COLORS["text_white"]).pack(side="left", padx=15, pady=8)
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=15, pady=(5, 5))
        fields = [
            ("OS Name",       os_info.get("name", "N/A")),
            ("Version",       os_info.get("version", "N/A")),
            ("Build",         os_info.get("build", "N/A")),
            ("Architecture",  os_info.get("architecture", "N/A")),
            ("Install Date",  os_info.get("install_date", "N/A")),
            ("Registered To", os_info.get("registered_to", "N/A")),
        ]
        for key, value in fields:
            row = ctk.CTkFrame(grid, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=key, font=ctk.CTkFont(family="Segoe UI", size=12),
                         text_color=COLORS["text_gray"], width=130, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=value, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                         text_color=COLORS["text_white"], anchor="w").pack(side="left")
        ctk.CTkFrame(card, height=1, fg_color=COLORS["bar_bg"]).pack(fill="x", padx=15, pady=8)
        uptime_row = ctk.CTkFrame(card, fg_color="transparent")
        uptime_row.pack(fill="x", padx=15, pady=(0, 12))
        ctk.CTkLabel(uptime_row, text=f"⏱️  Uptime:  {uptime['days']}d {uptime['hours']}h {uptime['minutes']}m",
                     font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                     text_color=COLORS["green"]).pack(side="left")
        ctk.CTkLabel(uptime_row, text=f"   |   Last Boot: {uptime['boot_time']}",
                     font=ctk.CTkFont(family="Segoe UI", size=12),
                     text_color=COLORS["text_gray"]).pack(side="left")

    def _build_services(self, services):
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=8)
        header = ctk.CTkFrame(card, fg_color=COLORS["selected"], corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(header, text=f"{get('services')} ({len(services)})",
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=COLORS["text_white"]).pack(side="left", padx=15, pady=8)
        for svc in services[:10]:
            row = ctk.CTkFrame(card, fg_color=COLORS["bar_bg"], corner_radius=6)
            row.pack(fill="x", padx=12, pady=3)
            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=10, pady=6)
            ctk.CTkLabel(inner, text="🟢", font=ctk.CTkFont(size=10)).pack(side="left")
            ctk.CTkLabel(inner, text=svc["name"][:45],
                         font=ctk.CTkFont(family="Segoe UI", size=11),
                         text_color=COLORS["text_white"], anchor="w").pack(side="left", padx=8)
            ctk.CTkLabel(inner, text=svc["start"],
                         font=ctk.CTkFont(family="Segoe UI", size=10),
                         text_color=COLORS["text_gray"]).pack(side="right")
        ctk.CTkFrame(card, height=1, fg_color=COLORS["bar_bg"]).pack(fill="x", padx=15, pady=8)

    def _build_startup(self, startup):
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=8)
        header = ctk.CTkFrame(card, fg_color=COLORS["selected"], corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(header, text=f"{get('startup')} ({len(startup)})",
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=COLORS["text_white"]).pack(side="left", padx=15, pady=8)
        if not startup:
            ctk.CTkLabel(card, text="No startup programs found",
                         font=ctk.CTkFont(family="Segoe UI", size=12),
                         text_color=COLORS["text_gray"]).pack(pady=10)
        else:
            for s in startup:
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=15, pady=3)
                ctk.CTkLabel(row, text=f"▶  {s['name'][:40]}",
                             font=ctk.CTkFont(family="Segoe UI", size=12),
                             text_color=COLORS["orange"], anchor="w").pack(side="left")
                ctk.CTkLabel(row, text=s["location"],
                             font=ctk.CTkFont(family="Segoe UI", size=11),
                             text_color=COLORS["text_gray"]).pack(side="right")
        ctk.CTkFrame(card, height=1, fg_color=COLORS["bar_bg"]).pack(fill="x", padx=15, pady=8)

    def _build_software(self, software):
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=8)
        header = ctk.CTkFrame(card, fg_color=COLORS["selected"], corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(header, text=f"{get('software')} (Top 30)",
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=COLORS["text_white"]).pack(side="left", padx=15, pady=8)
        if not software:
            ctk.CTkLabel(card, text="No software found",
                         font=ctk.CTkFont(family="Segoe UI", size=12),
                         text_color=COLORS["text_gray"]).pack(pady=10)
        else:
            for s in software:
                row = ctk.CTkFrame(card, fg_color=COLORS["bar_bg"], corner_radius=6)
                row.pack(fill="x", padx=12, pady=2)
                inner = ctk.CTkFrame(row, fg_color="transparent")
                inner.pack(fill="x", padx=10, pady=5)
                ctk.CTkLabel(inner, text=s["name"][:45],
                             font=ctk.CTkFont(family="Segoe UI", size=11),
                             text_color=COLORS["text_white"], anchor="w").pack(side="left")
                ctk.CTkLabel(inner, text=s["version"],
                             font=ctk.CTkFont(family="Segoe UI", size=10),
                             text_color=COLORS["accent"]).pack(side="right")
        ctk.CTkFrame(card, height=1, fg_color=COLORS["bar_bg"]).pack(fill="x", padx=15, pady=8)

    def _build_events(self, events):
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=8)
        header = ctk.CTkFrame(card, fg_color=COLORS["selected"], corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(header, text=get("events"),
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=COLORS["text_white"]).pack(side="left", padx=15, pady=8)
        if not events:
            ctk.CTkLabel(card, text="No recent events",
                         font=ctk.CTkFont(family="Segoe UI", size=12),
                         text_color=COLORS["text_gray"]).pack(pady=10)
        else:
            for event in events:
                row = ctk.CTkFrame(card, fg_color=COLORS["bar_bg"], corner_radius=6)
                row.pack(fill="x", padx=12, pady=2)
                inner = ctk.CTkFrame(row, fg_color="transparent")
                inner.pack(fill="x", padx=10, pady=6)
                level = event.get("level", "")
                color = COLORS["red"] if "Error" in level else COLORS["orange"] if "Warning" in level else COLORS["green"]
                icon = "🔴" if "Error" in level else "🟡" if "Warning" in level else "🟢"
                ctk.CTkLabel(inner, text=f"{icon} {level}",
                             font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                             text_color=color, width=80).pack(side="left")
                ctk.CTkLabel(inner, text=event.get("date", ""),
                             font=ctk.CTkFont(family="Segoe UI", size=10),
                             text_color=COLORS["text_gray"], width=130).pack(side="left", padx=5)
                ctk.CTkLabel(inner, text=event.get("desc", "No description"),
                             font=ctk.CTkFont(family="Segoe UI", size=10),
                             text_color=COLORS["text_white"], anchor="w").pack(side="left", padx=5)
        ctk.CTkFrame(card, height=1, fg_color=COLORS["bar_bg"]).pack(fill="x", padx=15, pady=8)