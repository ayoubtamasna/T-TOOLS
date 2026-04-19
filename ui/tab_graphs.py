import customtkinter as ctk
import psutil
import threading
import time
from collections import deque
import tkinter as tk

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

MAX_POINTS = 60

class GraphsTab:
    def __init__(self, parent):
        self.parent = parent
        self.running = True

        self.cpu_data    = deque([0] * MAX_POINTS, maxlen=MAX_POINTS)
        self.ram_data    = deque([0] * MAX_POINTS, maxlen=MAX_POINTS)

        self.frame = ctk.CTkScrollableFrame(
            parent,
            fg_color=COLORS["bg_dark"],
            scrollbar_button_color=COLORS["bar_bg"],
        )
        self.frame.pack(fill="both", expand=True, padx=15, pady=15)

        self._build_ui()

        threading.Thread(target=self._update_loop, daemon=True).start()

    def _build_ui(self):
        ctk.CTkLabel(
            self.frame,
            text="📊  Live System Monitor",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLORS["text_white"]
        ).pack(anchor="w", pady=(0, 15))

        self.cpu_card = self._build_graph_card("🖥️  CPU Usage", COLORS["accent"])
        self.cpu_canvas, self.cpu_percent_label, self.cpu_bar = self.cpu_card

        self.ram_card = self._build_graph_card("🧠  RAM Usage", COLORS["green"])
        self.ram_canvas, self.ram_percent_label, self.ram_bar = self.ram_card

        self._build_stats_row()

    def _build_graph_card(self, title, color):
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=8)

        header = ctk.CTkFrame(card, fg_color=COLORS["selected"], corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 8))

        ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLORS["text_white"]
        ).pack(side="left", padx=15, pady=8)

        percent_label = ctk.CTkLabel(
            header,
            text="0%",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=color
        )
        percent_label.pack(side="right", padx=15)

        canvas = tk.Canvas(
            card,
            height=120,
            bg="#0D1B2A",
            highlightthickness=0
        )
        canvas.pack(fill="x", padx=12, pady=(0, 8))

        bar = ctk.CTkProgressBar(
            card,
            height=8,
            fg_color=COLORS["bar_bg"],
            progress_color=color,
            corner_radius=4
        )
        bar.pack(fill="x", padx=12, pady=(0, 12))
        bar.set(0)

        return canvas, percent_label, bar

    def _build_stats_row(self):
        row = ctk.CTkFrame(self.frame, fg_color="transparent")
        row.pack(fill="x", pady=8)
        row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        stats = [
            ("⚡ CPU Cores",   str(psutil.cpu_count(logical=False)), COLORS["accent"]),
            ("🔀 Threads",     str(psutil.cpu_count(logical=True)),  COLORS["accent"]),
            ("💾 Total RAM",   f"{psutil.virtual_memory().total // (1024**3)} GB", COLORS["green"]),
            ("📊 Swap",        f"{psutil.swap_memory().total // (1024**3)} GB",    COLORS["green"]),
        ]

        for i, (label, value, color) in enumerate(stats):
            card = ctk.CTkFrame(row, fg_color=COLORS["bg_card"], corner_radius=10)
            card.grid(row=0, column=i, padx=5, sticky="ew")

            ctk.CTkLabel(
                card,
                text=value,
                font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
                text_color=color
            ).pack(pady=(12, 2))

            ctk.CTkLabel(
                card,
                text=label,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=COLORS["text_gray"]
            ).pack(pady=(0, 12))

    def _draw_graph(self, canvas, data, color):
        canvas.delete("all")
        w = canvas.winfo_width()
        h = canvas.winfo_height()

        if w < 10 or h < 10:
            return

        points = list(data)
        n = len(points)
        step = w / (n - 1) if n > 1 else w

        for i in range(0, 101, 25):
            y = h - (i / 100) * h
            canvas.create_line(0, y, w, y, fill="#1A2744", width=1)

        coords = []
        for i, val in enumerate(points):
            x = i * step
            y = h - (val / 100) * h
            coords.extend([x, y])

        if len(coords) >= 4:
            fill_coords = [0, h] + coords + [w, h]
            canvas.create_polygon(fill_coords, fill="#1E3A5F", outline="")
            canvas.create_line(coords, fill=color, width=2, smooth=True)

    def _get_color(self, value):
        if value < 60:
            return COLORS["green"]
        elif value < 85:
            return COLORS["orange"]
        else:
            return COLORS["red"]

    def _update_loop(self):
        while self.running:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent

            self.cpu_data.append(cpu)
            self.ram_data.append(ram)

            try:
                self.cpu_canvas.after(0, lambda c=cpu: self._update_cpu(c))
                self.ram_canvas.after(0, lambda r=ram: self._update_ram(r))
            except:
                break

    def _update_cpu(self, value):
        color = self._get_color(value)
        self.cpu_percent_label.configure(text=f"{value:.1f}%", text_color=color)
        self.cpu_bar.configure(progress_color=color)
        self.cpu_bar.set(value / 100)
        self._draw_graph(self.cpu_canvas, self.cpu_data, color)

    def _update_ram(self, value):
        color = self._get_color(value)
        self.ram_percent_label.configure(text=f"{value:.1f}%", text_color=color)
        self.ram_bar.configure(progress_color=color)
        self.ram_bar.set(value / 100)
        self._draw_graph(self.ram_canvas, self.ram_data, color)

    def destroy(self):
        self.running = False