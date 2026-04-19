import customtkinter as ctk
import psutil
import threading
import time
from datetime import datetime

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

class AlertsTab:
    def __init__(self, parent):
        self.parent = parent
        self.running = True
        self.alerts = []

        self.frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_dark"])
        self.frame.pack(fill="both", expand=True, padx=15, pady=15)

        self._build_ui()
        threading.Thread(target=self._monitor_loop, daemon=True).start()

    def _build_ui(self):
        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            header,
            text="🔔  Alerts & Monitoring",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLORS["text_white"]
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="🗑️  Clear All",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=COLORS["selected"],
            hover_color=COLORS["bar_bg"],
            corner_radius=8,
            height=32,
            width=100,
            command=self._clear_alerts
        ).pack(side="right")

        self._build_thresholds()

        self._build_live_stats()

        ctk.CTkLabel(
            self.frame,
            text="📋  Alert Log",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLORS["text_white"]
        ).pack(anchor="w", pady=(15, 5))

        self.alerts_frame = ctk.CTkScrollableFrame(
            self.frame,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            scrollbar_button_color=COLORS["bar_bg"],
        )
        self.alerts_frame.pack(fill="both", expand=True)

        self.empty_label = ctk.CTkLabel(
            self.alerts_frame,
            text="✅  No alerts - System is running normally",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["green"]
        )
        self.empty_label.pack(pady=30)

    def _build_thresholds(self):
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            card,
            text="⚙️  Alert Thresholds",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLORS["text_white"]
        ).pack(anchor="w", padx=15, pady=(12, 8))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=(0, 12))

        ctk.CTkLabel(
            row,
            text="CPU Alert at:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_gray"]
        ).pack(side="left")

        self.cpu_threshold = ctk.CTkSlider(
            row,
            from_=50, to=95,
            width=150,
            button_color=COLORS["accent"],
            progress_color=COLORS["accent"],
            fg_color=COLORS["bar_bg"],
        )
        self.cpu_threshold.set(85)
        self.cpu_threshold.pack(side="left", padx=10)

        self.cpu_thresh_label = ctk.CTkLabel(
            row,
            text="85%",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLORS["accent"],
            width=40
        )
        self.cpu_thresh_label.pack(side="left")
        self.cpu_threshold.configure(command=lambda v: self.cpu_thresh_label.configure(text=f"{int(v)}%"))

        ctk.CTkLabel(
            row,
            text="RAM Alert at:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_gray"]
        ).pack(side="left", padx=(20, 0))

        self.ram_threshold = ctk.CTkSlider(
            row,
            from_=50, to=95,
            width=150,
            button_color=COLORS["green"],
            progress_color=COLORS["green"],
            fg_color=COLORS["bar_bg"],
        )
        self.ram_threshold.set(85)
        self.ram_threshold.pack(side="left", padx=10)

        self.ram_thresh_label = ctk.CTkLabel(
            row,
            text="85%",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLORS["green"],
            width=40
        )
        self.ram_thresh_label.pack(side="left")
        self.ram_threshold.configure(command=lambda v: self.ram_thresh_label.configure(text=f"{int(v)}%"))

    def _build_live_stats(self):
        row = ctk.CTkFrame(self.frame, fg_color="transparent")
        row.pack(fill="x", pady=(0, 5))
        row.grid_columnconfigure((0, 1, 2), weight=1)

        cpu_card = ctk.CTkFrame(row, fg_color=COLORS["bg_card"], corner_radius=10)
        cpu_card.grid(row=0, column=0, padx=5, sticky="ew")

        ctk.CTkLabel(
            cpu_card,
            text="🖥️  CPU",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_gray"]
        ).pack(pady=(8, 2))

        self.cpu_live = ctk.CTkLabel(
            cpu_card,
            text="0%",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=COLORS["green"]
        )
        self.cpu_live.pack(pady=(0, 8))

        ram_card = ctk.CTkFrame(row, fg_color=COLORS["bg_card"], corner_radius=10)
        ram_card.grid(row=0, column=1, padx=5, sticky="ew")

        ctk.CTkLabel(
            ram_card,
            text="🧠  RAM",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_gray"]
        ).pack(pady=(8, 2))

        self.ram_live = ctk.CTkLabel(
            ram_card,
            text="0%",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=COLORS["green"]
        )
        self.ram_live.pack(pady=(0, 8))

        status_card = ctk.CTkFrame(row, fg_color=COLORS["bg_card"], corner_radius=10)
        status_card.grid(row=0, column=2, padx=5, sticky="ew")

        ctk.CTkLabel(
            status_card,
            text="📡  Status",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_gray"]
        ).pack(pady=(8, 2))

        self.status_live = ctk.CTkLabel(
            status_card,
            text="Normal",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=COLORS["green"]
        )
        self.status_live.pack(pady=(0, 8))

    def _monitor_loop(self):
        last_cpu_alert = 0
        last_ram_alert = 0

        while self.running:
            cpu = psutil.cpu_percent(interval=2)
            ram = psutil.virtual_memory().percent

            cpu_thresh = self.cpu_threshold.get()
            ram_thresh = self.ram_threshold.get()

            now = time.time()

            try:
                self.frame.after(0, lambda c=cpu, r=ram: self._update_live(c, r))
            except:
                break

            if cpu >= cpu_thresh and (now - last_cpu_alert) > 30:
                last_cpu_alert = now
                self._add_alert("🔴  HIGH CPU", f"CPU usage reached {cpu:.1f}%", "critical")

            if ram >= ram_thresh and (now - last_ram_alert) > 30:
                last_ram_alert = now
                self._add_alert("🟠  HIGH RAM", f"RAM usage reached {ram:.1f}%", "warning")

            if cpu < cpu_thresh * 0.7:
                pass 

    def _update_live(self, cpu, ram):
        cpu_color = COLORS["green"] if cpu < 60 else COLORS["orange"] if cpu < 85 else COLORS["red"]
        ram_color = COLORS["green"] if ram < 60 else COLORS["orange"] if ram < 85 else COLORS["red"]

        self.cpu_live.configure(text=f"{cpu:.1f}%", text_color=cpu_color)
        self.ram_live.configure(text=f"{ram:.1f}%", text_color=ram_color)

        cpu_thresh = self.cpu_threshold.get()
        ram_thresh = self.ram_threshold.get()

        if cpu >= cpu_thresh or ram >= ram_thresh:
            self.status_live.configure(text="⚠️ Alert!", text_color=COLORS["red"])
        else:
            self.status_live.configure(text="Normal", text_color=COLORS["green"])

    def _add_alert(self, title, message, level):
        color = COLORS["red"] if level == "critical" else COLORS["orange"]
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.alerts.append({"title": title, "message": message, "time": timestamp})

        try:
            self.frame.after(0, lambda: self._render_alert(title, message, timestamp, color))
        except:
            pass

    def _render_alert(self, title, message, timestamp, color):
        if hasattr(self, 'empty_label') and self.empty_label.winfo_exists():
            self.empty_label.destroy()

        alert = ctk.CTkFrame(self.alerts_frame, fg_color=COLORS["selected"], corner_radius=8)
        alert.pack(fill="x", padx=10, pady=4)

        row = ctk.CTkFrame(alert, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(
            row,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=color
        ).pack(side="left")

        ctk.CTkLabel(
            row,
            text=message,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_gray"]
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            row,
            text=timestamp,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["bar_bg"]
        ).pack(side="right")

    def _clear_alerts(self):
        self.alerts = []
        for widget in self.alerts_frame.winfo_children():
            widget.destroy()
        self.empty_label = ctk.CTkLabel(
            self.alerts_frame,
            text="✅  No alerts - System is running normally",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["green"]
        )
        self.empty_label.pack(pady=30)

    def destroy(self):
        self.running = False