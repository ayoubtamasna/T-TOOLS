import customtkinter as ctk
import subprocess
import threading

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

class WPSTab:
    def __init__(self, parent):
        self.parent = parent
        self.scanning = False

        self.frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_dark"])
        self.frame.pack(fill="both", expand=True, padx=15, pady=15)

        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(
            self.frame,
            text="🔐  WPS Network Scanner",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLORS["text_white"]
        ).pack(anchor="w", pady=(0, 15))

        control = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        control.pack(fill="x", pady=(0, 10))

        row = ctk.CTkFrame(control, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            row,
            text="Scan nearby WiFi networks and detect WPS vulnerabilities",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_gray"]
        ).pack(side="left")

        self.scan_btn = ctk.CTkButton(
            row,
            text="▶  Start Scan",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color="#1565C0",
            corner_radius=8,
            height=35,
            width=130,
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

        stats = ctk.CTkFrame(self.frame, fg_color="transparent")
        stats.pack(fill="x", pady=(0, 10))
        stats.grid_columnconfigure((0, 1, 2), weight=1)

        total_card = ctk.CTkFrame(stats, fg_color=COLORS["bg_card"], corner_radius=10)
        total_card.grid(row=0, column=0, padx=5, sticky="ew")
        ctk.CTkLabel(total_card, text="Networks Found",
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    text_color=COLORS["text_gray"]).pack(pady=(8, 2))
        self.total_count = ctk.CTkLabel(total_card, text="0",
                    font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
                    text_color=COLORS["accent"])
        self.total_count.pack(pady=(0, 8))

        vuln_card = ctk.CTkFrame(stats, fg_color=COLORS["bg_card"], corner_radius=10)
        vuln_card.grid(row=0, column=1, padx=5, sticky="ew")
        ctk.CTkLabel(vuln_card, text="WPS Enabled",
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    text_color=COLORS["text_gray"]).pack(pady=(8, 2))
        self.wps_count = ctk.CTkLabel(vuln_card, text="0",
                    font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
                    text_color=COLORS["orange"])
        self.wps_count.pack(pady=(0, 8))

        secure_card = ctk.CTkFrame(stats, fg_color=COLORS["bg_card"], corner_radius=10)
        secure_card.grid(row=0, column=2, padx=5, sticky="ew")
        ctk.CTkLabel(secure_card, text="Secure Networks",
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    text_color=COLORS["text_gray"]).pack(pady=(8, 2))
        self.secure_count = ctk.CTkLabel(secure_card, text="0",
                    font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
                    text_color=COLORS["green"])
        self.secure_count.pack(pady=(0, 8))

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
            text="Press Start Scan to discover nearby networks",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_gray"]
        ).pack(pady=30)

    def _start_scan(self):
        if self.scanning:
            return

        for w in self.results_frame.winfo_children():
            w.destroy()

        self.total_count.configure(text="0")
        self.wps_count.configure(text="0")
        self.secure_count.configure(text="0")
        self.progress_bar.set(0)

        self.scanning = True
        self.scan_btn.configure(text="⏳ Scanning...", state="disabled")
        self.progress_label.configure(text="Scanning nearby networks...")

        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        try:
            self.frame.after(0, lambda: self.progress_bar.set(0.3))

            result = subprocess.run(
                ["netsh", "wlan", "show", "networks", "mode=bssid"],
                capture_output=True, timeout=15,
                encoding='utf-8', errors='ignore'
            )

            self.frame.after(0, lambda: self.progress_bar.set(0.7))
            networks = self._parse_networks(result.stdout)
            self.frame.after(0, lambda: self.progress_bar.set(1.0))
            self.frame.after(0, lambda: self._show_results(networks))

        except Exception as e:
            self.frame.after(0, lambda: self._scan_error(str(e)))

    def _parse_networks(self, output):
        networks = []
        current = {}

        for line in output.splitlines():
            line = line.strip()

            if line.startswith("SSID") and "BSSID" not in line and ":" in line:
                if current and "ssid" in current:
                    networks.append(self._finalize(current))
                ssid_val = line.split(":", 1)[-1].strip()
                current = {"ssid": ssid_val if ssid_val else "Hidden", "bssid": "N/A", "signal": "N/A", "auth": "N/A", "channel": "N/A"}

            elif "BSSID" in line and ":" in line:
                current["bssid"] = line.split(":", 1)[-1].strip()

            elif line.startswith("Signal") and ":" in line:
                current["signal"] = line.split(":")[-1].strip()

            elif line.startswith("Authentication") and ":" in line:
                current["auth"] = line.split(":")[-1].strip()

            elif line.startswith("Channel") and ":" in line:
                current["channel"] = line.split(":")[-1].strip()

        if current and "ssid" in current:
            networks.append(self._finalize(current))

        return networks

    def _finalize(self, network):
        auth = network.get("auth", "").lower()
        if "open" in auth or "wep" in auth:
            network["wps"] = True
            network["vulnerability"] = "HIGH - No/Weak encryption"
        elif "wpa2" in auth and "wpa3" not in auth:
            network["wps"] = True
            network["vulnerability"] = "MEDIUM - WPS may be enabled"
        else:
            network["wps"] = False
            network["vulnerability"] = "LOW - Strong encryption"
        return network

    def _show_results(self, networks):
        self.scanning = False
        self.scan_btn.configure(text="▶  Start Scan", state="normal")
        self.progress_label.configure(text=f"✅ Scan complete - {len(networks)} networks found")

        total = len(networks)
        wps = sum(1 for n in networks if n["wps"])
        secure = total - wps

        self.total_count.configure(text=str(total))
        self.wps_count.configure(text=str(wps))
        self.secure_count.configure(text=str(secure))

        if not networks:
            ctk.CTkLabel(
                self.results_frame,
                text="No networks found - Make sure WiFi is enabled",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=COLORS["text_gray"]
            ).pack(pady=30)
            return

        for network in networks:
            self._add_network_card(network)

    def _add_network_card(self, network):
        vuln_text = network.get("vulnerability", "Unknown")
        color = COLORS["red"] if "HIGH" in vuln_text else COLORS["orange"] if "MEDIUM" in vuln_text else COLORS["green"]
        icon = "🔴" if "HIGH" in vuln_text else "🟡" if "MEDIUM" in vuln_text else "🟢"

        card = ctk.CTkFrame(self.results_frame, fg_color=COLORS["selected"], corner_radius=8)
        card.pack(fill="x", padx=10, pady=4)

        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=12, pady=(10, 3))

        ctk.CTkLabel(
            row1,
            text=f"{icon}  {network['ssid']}",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=color,
            anchor="w"
        ).pack(side="left")

        ctk.CTkLabel(
            row1,
            text=vuln_text,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=color
        ).pack(side="right")

        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(
            row2,
            text=f"BSSID: {network['bssid']}",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS["text_gray"]
        ).pack(side="left")

        ctk.CTkLabel(
            row2,
            text=f"Signal: {network['signal']}",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS["text_gray"]
        ).pack(side="left", padx=15)

        ctk.CTkLabel(
            row2,
            text=f"Auth: {network['auth']}",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS["text_gray"]
        ).pack(side="left")

        ctk.CTkLabel(
            row2,
            text=f"Ch: {network['channel']}",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS["text_gray"]
        ).pack(side="right")

    def _scan_error(self, msg):
        self.scanning = False
        self.scan_btn.configure(text="▶  Start Scan", state="normal")
        self.progress_label.configure(text=f"❌ Error: {msg}", text_color=COLORS["red"])