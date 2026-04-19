import customtkinter as ctk
import socket
import threading
import tkinter as tk
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

COMMON_PORTS = {
    21:   "FTP",
    22:   "SSH",
    23:   "Telnet",
    25:   "SMTP",
    53:   "DNS",
    80:   "HTTP",
    110:  "POP3",
    135:  "RPC",
    139:  "NetBIOS",
    143:  "IMAP",
    443:  "HTTPS",
    445:  "SMB",
    3306: "MySQL",
    3389: "RDP",
    5985: "WinRM",
    8080: "HTTP-Alt",
    8443: "HTTPS-Alt",
    27017:"MongoDB",
}

DANGEROUS_PORTS = {23, 135, 139, 445, 3389, 5985}

class PortsTab:
    def __init__(self, parent):
        self.parent = parent
        self.scanning = False
        self.scan_thread = None

        self.frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_dark"])
        self.frame.pack(fill="both", expand=True, padx=15, pady=15)

        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(
            self.frame,
            text="🔌  Port Scanner",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLORS["text_white"]
        ).pack(anchor="w", pady=(0, 15))

        control = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        control.pack(fill="x", pady=(0, 10))

        row1 = ctk.CTkFrame(control, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(
            row1,
            text="Target:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_gray"]
        ).pack(side="left")

        self.target_entry = ctk.CTkEntry(
            row1,
            width=200,
            placeholder_text="IP or hostname (e.g. 192.168.1.1)",
            fg_color=COLORS["selected"],
            border_color=COLORS["accent"],
            text_color=COLORS["text_white"],
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.target_entry.pack(side="left", padx=10)
        self.target_entry.insert(0, "127.0.0.1")

        ctk.CTkLabel(
            row1,
            text="Scan:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_gray"]
        ).pack(side="left", padx=(10, 5))

        self.scan_type = ctk.CTkSegmentedButton(
            row1,
            values=["Common Ports", "Full Scan (1-1024)"],
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=COLORS["selected"],
            selected_color=COLORS["accent"],
            text_color=COLORS["text_white"],
        )
        self.scan_type.set("Common Ports")
        self.scan_type.pack(side="left", padx=10)

        self.scan_btn = ctk.CTkButton(
            row1,
            text="▶  Start Scan",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color="#1565C0",
            corner_radius=8,
            height=35,
            width=120,
            command=self._start_scan
        )
        self.scan_btn.pack(side="right")

        self.progress_label = ctk.CTkLabel(
            control,
            text="Ready to scan",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_gray"]
        )
        self.progress_label.pack(padx=15, pady=(0, 5), anchor="w")

        self.progress_bar = ctk.CTkProgressBar(
            control,
            height=4,
            fg_color=COLORS["bar_bg"],
            progress_color=COLORS["accent"],
            corner_radius=2
        )
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 12))
        self.progress_bar.set(0)

        # Stats Row
        stats = ctk.CTkFrame(self.frame, fg_color="transparent")
        stats.pack(fill="x", pady=(0, 10))
        stats.grid_columnconfigure((0, 1, 2), weight=1)

        open_card = ctk.CTkFrame(stats, fg_color=COLORS["bg_card"], corner_radius=10)
        open_card.grid(row=0, column=0, padx=5, sticky="ew")
        ctk.CTkLabel(open_card, text="Open Ports",
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    text_color=COLORS["text_gray"]).pack(pady=(8,2))
        self.open_count = ctk.CTkLabel(open_card, text="0",
                    font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
                    text_color=COLORS["green"])
        self.open_count.pack(pady=(0,8))

        danger_card = ctk.CTkFrame(stats, fg_color=COLORS["bg_card"], corner_radius=10)
        danger_card.grid(row=0, column=1, padx=5, sticky="ew")
        ctk.CTkLabel(danger_card, text="⚠️ Dangerous",
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    text_color=COLORS["text_gray"]).pack(pady=(8,2))
        self.danger_count = ctk.CTkLabel(danger_card, text="0",
                    font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
                    text_color=COLORS["red"])
        self.danger_count.pack(pady=(0,8))

        closed_card = ctk.CTkFrame(stats, fg_color=COLORS["bg_card"], corner_radius=10)
        closed_card.grid(row=0, column=2, padx=5, sticky="ew")
        ctk.CTkLabel(closed_card, text="Closed Ports",
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    text_color=COLORS["text_gray"]).pack(pady=(8,2))
        self.closed_count = ctk.CTkLabel(closed_card, text="0",
                    font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
                    text_color=COLORS["text_gray"])
        self.closed_count.pack(pady=(0,8))

        ctk.CTkLabel(
            self.frame,
            text="📋  Scan Results",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLORS["text_white"]
        ).pack(anchor="w", pady=(5, 5))

        self.results_frame = ctk.CTkScrollableFrame(
            self.frame,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            scrollbar_button_color=COLORS["bar_bg"],
        )
        self.results_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.results_frame,
            text="Enter a target and press Start Scan",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_gray"]
        ).pack(pady=30)

    def _start_scan(self):
        if self.scanning:
            return

        target = self.target_entry.get().strip()
        if not target:
            return

        for w in self.results_frame.winfo_children():
            w.destroy()

        self.open_count.configure(text="0")
        self.danger_count.configure(text="0")
        self.closed_count.configure(text="0")

        self.scanning = True
        self.scan_btn.configure(text="⏳ Scanning...", state="disabled")

        self.scan_thread = threading.Thread(
            target=self._scan_worker,
            args=(target,),
            daemon=True
        )
        self.scan_thread.start()

    def _scan_worker(self, target):
        try:
            ip = socket.gethostbyname(target)
        except:
            self.frame.after(0, lambda: self._scan_error("Could not resolve host"))
            return

        if self.scan_type.get() == "Common Ports":
            ports = list(COMMON_PORTS.keys())
        else:
            ports = list(range(1, 1025))

        total = len(ports)
        open_ports = []
        closed = 0

        for i, port in enumerate(ports):
            progress = (i + 1) / total
            self.frame.after(0, lambda p=progress, port=port: self._update_progress(p, port))

            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex((ip, port))
                sock.close()

                if result == 0:
                    service = COMMON_PORTS.get(port, "Unknown")
                    dangerous = port in DANGEROUS_PORTS
                    open_ports.append((port, service, dangerous))
                    self.frame.after(0, lambda p=port, s=service, d=dangerous:
                                    self._add_result(p, s, d))
                else:
                    closed += 1
            except:
                closed += 1

        self.frame.after(0, lambda: self._scan_complete(open_ports, closed))

    def _update_progress(self, progress, port):
        self.progress_bar.set(progress)
        self.progress_label.configure(text=f"Scanning port {port}...")

    def _add_result(self, port, service, dangerous):
        color = COLORS["red"] if dangerous else COLORS["green"]
        icon = "⚠️" if dangerous else "✅"

        row = ctk.CTkFrame(self.results_frame, fg_color=COLORS["selected"], corner_radius=8)
        row.pack(fill="x", padx=10, pady=3)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(
            inner,
            text=f"{icon}  Port {port}",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=color,
            width=120
        ).pack(side="left")

        ctk.CTkLabel(
            inner,
            text=service,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_white"],
            width=100
        ).pack(side="left")

        status_text = "⚠️ DANGEROUS - Consider closing" if dangerous else "OPEN"
        ctk.CTkLabel(
            inner,
            text=status_text,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=color
        ).pack(side="left", padx=10)

        current = int(self.open_count.cget("text"))
        self.open_count.configure(text=str(current + 1))

        if dangerous:
            current_d = int(self.danger_count.cget("text"))
            self.danger_count.configure(text=str(current_d + 1))

    def _scan_complete(self, open_ports, closed):
        self.scanning = False
        self.scan_btn.configure(text="▶  Start Scan", state="normal")
        self.progress_bar.set(1)
        self.progress_label.configure(
            text=f"✅ Scan complete - {len(open_ports)} open, {closed} closed"
        )
        self.closed_count.configure(text=str(closed))

        if not open_ports:
            ctk.CTkLabel(
                self.results_frame,
                text="✅  No open ports found",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=COLORS["green"]
            ).pack(pady=30)

    def _scan_error(self, msg):
        self.scanning = False
        self.scan_btn.configure(text="▶  Start Scan", state="normal")
        self.progress_label.configure(text=f"❌ Error: {msg}", text_color=COLORS["red"])