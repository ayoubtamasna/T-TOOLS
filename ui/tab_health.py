import customtkinter as ctk
import psutil
import threading
import pythoncom
import wmi
import tkinter as tk
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

class HealthTab:
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
        cpu_usage = psutil.cpu_percent(interval=2)
        cpu_temp  = self._get_cpu_temp(c)
        ram = psutil.virtual_memory()
        ram_usage = ram.percent
        disks = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "mount":   part.mountpoint,
                    "percent": usage.percent,
                    "total":   usage.total // (1024**3),
                    "used":    usage.used // (1024**3),
                    "free":    usage.free // (1024**3),
                })
            except:
                pass
        scores = self._calculate_scores(cpu_usage, ram_usage, disks, cpu_temp)
        self.frame.after(0, lambda: self._build_ui(scores, cpu_usage, ram_usage, disks, cpu_temp))

    def _get_cpu_temp(self, c):
        try:
            temps = c.MSAcpi_ThermalZoneTemperature()
            if temps:
                kelvin = temps[0].CurrentTemperature / 10
                return round(kelvin - 273.15, 1)
        except:
            pass
        return None

    def _calculate_scores(self, cpu, ram, disks, temp):
        scores = {}
        if cpu < 30:   scores["cpu"] = (100, "Excellent")
        elif cpu < 60: scores["cpu"] = (80,  "Good")
        elif cpu < 80: scores["cpu"] = (50,  "Warning")
        else:          scores["cpu"] = (20,  "Critical")

        if ram < 50:   scores["ram"] = (100, "Excellent")
        elif ram < 70: scores["ram"] = (75,  "Good")
        elif ram < 85: scores["ram"] = (45,  "Warning")
        else:          scores["ram"] = (15,  "Critical")

        disk_score = 100
        for d in disks:
            if d["percent"] > 90:   disk_score = min(disk_score, 20)
            elif d["percent"] > 75: disk_score = min(disk_score, 60)
            elif d["percent"] > 50: disk_score = min(disk_score, 85)
        scores["disk"] = (disk_score, "Excellent" if disk_score >= 85 else "Good" if disk_score >= 60 else "Warning" if disk_score >= 30 else "Critical")

        if temp is None:  scores["temp"] = (80, "Unknown")
        elif temp < 60:   scores["temp"] = (100, "Excellent")
        elif temp < 75:   scores["temp"] = (70,  "Good")
        elif temp < 90:   scores["temp"] = (40,  "Warning")
        else:             scores["temp"] = (10,  "Critical")

        total = sum(s[0] for s in scores.values()) // len(scores)
        scores["overall"] = total
        return scores

    def _build_ui(self, scores, cpu_usage, ram_usage, disks, cpu_temp):
        self.loading_label.destroy()
        self.refresh_btn.configure(text=get("refresh"), state="normal")

        ctk.CTkLabel(
            self.frame,
            text=get("health_title"),
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLORS["text_white"]
        ).pack(anchor="w", pady=(0, 15))

        self._build_overall_score(scores["overall"])
        self._build_score_card(get("cpu_load"),   scores["cpu"][0],  scores["cpu"][1],  f"{cpu_usage}%")
        self._build_score_card(get("mem_usage"),  scores["ram"][0],  scores["ram"][1],  f"{ram_usage}%")
        self._build_score_card(get("disk_health"),scores["disk"][0], scores["disk"][1], f"{len(disks)} drives")
        self._build_score_card(get("temperature"),scores["temp"][0], scores["temp"][1],
                               f"{cpu_temp}°C" if cpu_temp else "N/A")
        self._build_disk_details(disks)

    def _build_overall_score(self, score):
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=8)
        color = COLORS["green"] if score >= 75 else COLORS["orange"] if score >= 50 else COLORS["red"]
        status = "Healthy" if score >= 75 else "Fair" if score >= 50 else "Critical"
        canvas = tk.Canvas(card, width=200, height=200, bg=COLORS["bg_card"], highlightthickness=0)
        canvas.pack(pady=20)
        canvas.create_oval(20, 20, 180, 180, outline=COLORS["bar_bg"], width=15)
        angle = (score / 100) * 360
        canvas.create_arc(20, 20, 180, 180, start=90, extent=-angle, outline=color, width=15, style="arc")
        canvas.create_text(100, 85, text=str(score), fill=color, font=("Segoe UI", 36, "bold"))
        canvas.create_text(100, 125, text="/100", fill=COLORS["text_gray"], font=("Segoe UI", 14))
        canvas.create_text(100, 155, text=status, fill=color, font=("Segoe UI", 13, "bold"))

    def _build_score_card(self, title, score, status, value):
        color = COLORS["green"] if score >= 75 else COLORS["orange"] if score >= 50 else COLORS["red"]
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=5)
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=12)
        ctk.CTkLabel(row, text=title, font=ctk.CTkFont(family="Segoe UI", size=13),
                     text_color=COLORS["text_white"], width=180, anchor="w").pack(side="left")
        bar = ctk.CTkProgressBar(row, width=300, height=8, fg_color=COLORS["bar_bg"],
                                  progress_color=color, corner_radius=4)
        bar.pack(side="left", padx=10)
        bar.set(score / 100)
        ctk.CTkLabel(row, text=status, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                     text_color=color, width=80).pack(side="left", padx=5)
        ctk.CTkLabel(row, text=value, font=ctk.CTkFont(family="Segoe UI", size=12),
                     text_color=COLORS["text_gray"]).pack(side="right")

    def _build_disk_details(self, disks):
        ctk.CTkLabel(self.frame, text=get("disk_details"),
                     font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
                     text_color=COLORS["text_white"]).pack(anchor="w", pady=(15, 5))
        for disk in disks:
            card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=10)
            card.pack(fill="x", pady=4)
            color = COLORS["green"] if disk["percent"] < 70 else COLORS["orange"] if disk["percent"] < 90 else COLORS["red"]
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=10)
            ctk.CTkLabel(row, text=f"📁  {disk['mount']}",
                         font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                         text_color=COLORS["text_white"], width=80).pack(side="left")
            bar = ctk.CTkProgressBar(row, height=8, fg_color=COLORS["bar_bg"],
                                      progress_color=color, corner_radius=4)
            bar.pack(side="left", fill="x", expand=True, padx=10)
            bar.set(disk["percent"] / 100)
            ctk.CTkLabel(row, text=f"{disk['used']}GB / {disk['total']}GB  ({disk['percent']}%)",
                         font=ctk.CTkFont(family="Segoe UI", size=11),
                         text_color=COLORS["text_gray"]).pack(side="right")