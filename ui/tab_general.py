import customtkinter as ctk
from PIL import Image
import os
import threading
import pythoncom
import psutil
from collectors.hardware import (
    get_cpu_info, get_ram_info,
    get_gpu_info, get_motherboard_info,
    get_disk_info, get_os_info
)
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

LOGOS_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "logos")

def get_battery_info():
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return None
        return {
            "percent": battery.percent,
            "plugged":  battery.power_plugged,
            "seconds":  battery.secsleft,
        }
    except:
        return None

class GeneralTab:
    def __init__(self, parent):
        self.parent = parent
        self._logo_cache = {}

        # Top bar مع Refresh
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
        try:
            pythoncom.CoInitialize()
            data = {
                "cpu":     get_cpu_info(),
                "ram":     get_ram_info(),
                "gpu":     get_gpu_info(),
                "board":   get_motherboard_info(),
                "disk":    get_disk_info(),
                "os":      get_os_info(),
                "battery": get_battery_info(),
            }
            self.frame.after(0, lambda: self._build_ui(data))
        except Exception as e:
            print(f"❌ ERROR: {e}")
            self.frame.after(0, lambda: self.loading_label.configure(
                text=f"❌ Error: {e}",
                text_color="#FF4444"
            ))

    def _build_ui(self, data):
        self.loading_label.destroy()
        self.refresh_btn.configure(text=get("refresh"), state="normal")
        self._build_os_bar(data["os"])

        self._build_section(get("processor"), [
            ("Name",      data["cpu"]["name"]),
            ("Cores",     str(data["cpu"]["cores"])),
            ("Threads",   str(data["cpu"]["threads"])),
            ("Max Speed", data["cpu"]["max_speed"]),
            ("Usage",     f"{data['cpu']['usage']}%"),
        ], data["cpu"]["brand"])

        self._build_section(get("memory"), [
            ("Total",  data["ram"]["total"]),
            ("Used",   data["ram"]["used"]),
            ("Free",   data["ram"]["free"]),
            ("Usage",  f"{data['ram']['percent']}%"),
            ("Sticks", str(len(data["ram"]["sticks"]))),
        ], data["ram"]["brand"])

        for i, gpu in enumerate(data["gpu"]):
            self._build_section(f"{get('gpu')} {i+1}", [
                ("Name",   gpu["name"]),
                ("VRAM",   gpu["vram"]),
                ("Driver", gpu["driver"]),
            ], gpu["brand"])

        self._build_section(get("motherboard"), [
            ("Manufacturer", data["board"]["manufacturer"]),
            ("Model",        data["board"]["model"]),
            ("BIOS Version", data["board"]["bios_version"]),
            ("BIOS Date",    data["board"]["bios_date"]),
        ], data["board"]["brand"])

        for i, disk in enumerate(data["disk"]):
            self._build_section(f"{get('disk')} {i+1}", [
                ("Model", disk["model"]),
                ("Size",  disk["size"]),
                ("Type",  disk["type"]),
            ], disk["brand"])

        if data["battery"]:
            self._build_battery_section(data["battery"])

    def _build_battery_section(self, battery):
        pct     = battery["percent"]
        plugged = battery["plugged"]
        secs    = battery["seconds"]

        if plugged:
            time_str = get("charging")
        elif secs == psutil.POWER_TIME_UNLIMITED:
            time_str = get("plugged_in")
        elif secs == psutil.POWER_TIME_UNKNOWN:
            time_str = get("calculating")
        else:
            h = secs // 3600
            m = (secs % 3600) // 60
            time_str = f"{h}h {m}m"

        bar_color = COLORS["green"] if pct >= 60 else COLORS["orange"] if pct >= 30 else COLORS["red"]

        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=8)

        header = ctk.CTkFrame(card, fg_color=COLORS["selected"], corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 8))

        ctk.CTkLabel(
            header,
            text=get("battery"),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLORS["text_white"]
        ).pack(side="left", padx=15, pady=8)

        status_icon = "🔌" if plugged else "🔋"
        ctk.CTkLabel(
            header,
            text=f"{status_icon} {get('plugged') if plugged else get('unplugged')}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["green"] if plugged else COLORS["orange"]
        ).pack(side="right", padx=15, pady=8)

        bar_frame = ctk.CTkFrame(card, fg_color="transparent")
        bar_frame.pack(fill="x", padx=15, pady=(5, 5))

        ctk.CTkLabel(
            bar_frame,
            text=f"{pct:.1f}%",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=bar_color
        ).pack(side="left")

        ctk.CTkLabel(
            bar_frame,
            text=f"  ⏱ {time_str}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_gray"]
        ).pack(side="left", pady=5)

        bar = ctk.CTkProgressBar(
            card,
            width=400, height=10,
            fg_color=COLORS["bar_bg"],
            progress_color=bar_color,
            corner_radius=5
        )
        bar.pack(fill="x", padx=15, pady=(0, 12))
        bar.set(pct / 100)

    def _build_os_bar(self, os_info):
        bar = ctk.CTkFrame(self.frame, fg_color=COLORS["selected"], corner_radius=10)
        bar.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(
            bar,
            text=f"🖥️  {os_info['hostname']}   |   Windows {os_info['release']}   |   {os_info['machine']}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_gray"]
        ).pack(pady=10, padx=15, anchor="w")

    def _build_section(self, title, fields, brand="default"):
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=8)

        header = ctk.CTkFrame(card, fg_color=COLORS["selected"], corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 8))

        logo = self._load_logo(brand)
        if logo:
            lbl = ctk.CTkLabel(header, image=logo, text="", width=40, height=40)
            lbl.image = logo
            lbl.pack(side="left", padx=10, pady=6)

        ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLORS["text_white"]
        ).pack(side="left", padx=5, pady=8)

        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=15, pady=(5, 12))

        for key, value in fields:
            row = ctk.CTkFrame(grid, fg_color="transparent")
            row.pack(fill="x", pady=3)

            ctk.CTkLabel(
                row,
                text=key,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=COLORS["text_gray"],
                width=130,
                anchor="w"
            ).pack(side="left")

            color = COLORS["text_white"]
            if "%" in str(value):
                try:
                    pct = float(str(value).replace("%", ""))
                    color = COLORS["green"] if pct < 60 else COLORS["orange"] if pct < 85 else COLORS["red"]
                except:
                    pass

            ctk.CTkLabel(
                row,
                text=value,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=color,
                anchor="w"
            ).pack(side="left")

    def _load_logo(self, brand):
        if brand in self._logo_cache:
            return self._logo_cache[brand]
        try:
            path = os.path.join(LOGOS_PATH, f"{brand}.png")
            if not os.path.exists(path):
                path = os.path.join(LOGOS_PATH, "default.png")
            if not os.path.exists(path):
                self._logo_cache[brand] = None
                return None
            img = Image.open(path).convert("RGBA").resize((40, 40), Image.LANCZOS)
            photo = ctk.CTkImage(light_image=img, dark_image=img, size=(40, 40))
            self._logo_cache[brand] = photo
            return photo
        except Exception as e:
            print(f"Logo error: {e}")
            self._logo_cache[brand] = None
            return None