import customtkinter as ctk
import subprocess
import threading
import psutil
import socket
import pythoncom
import wmi
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

class CloudTab:
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
            "interfaces":     self._get_network_interfaces(),
            "dns":            self._get_dns_servers(c),
            "routing":        self._get_routing_table(),
            "gateway":        self._get_default_gateway(),
            "public_ip":      self._get_public_ip(),
            "virtualization": self._get_virtualization(c),
            "bandwidth":      self._get_bandwidth(),
        }
        self.frame.after(0, lambda: self._build_ui(data))

    def _get_network_interfaces(self):
        interfaces = []
        for name, addrs in psutil.net_if_addrs().items():
            stats = psutil.net_if_stats().get(name)
            info = {"name": name, "up": stats.isup if stats else False,
                    "speed": f"{stats.speed} Mbps" if stats and stats.speed > 0 else "N/A",
                    "ipv4": "N/A", "ipv6": "N/A", "mac": "N/A"}
            for addr in addrs:
                if addr.family == 2:    info["ipv4"] = addr.address
                elif addr.family == 23: info["ipv6"] = addr.address[:30]
                elif addr.family == -1: info["mac"] = addr.address
            interfaces.append(info)
        return interfaces

    def _get_dns_servers(self, c):
        try:
            dns_list = []
            for adapter in c.Win32_NetworkAdapterConfiguration(IPEnabled=True):
                if adapter.DNSServerSearchOrder:
                    for dns in adapter.DNSServerSearchOrder:
                        if dns not in dns_list:
                            dns_list.append(dns)
            return dns_list if dns_list else ["Not found"]
        except:
            return ["Unknown"]

    def _get_routing_table(self):
        try:
            result = subprocess.run(["route", "print", "-4"], capture_output=True, text=True, timeout=5)
            lines = result.stdout.splitlines()
            routes = []
            capture = False
            for line in lines:
                if "Network Destination" in line:
                    capture = True
                    continue
                if capture and line.strip() and not line.startswith("="):
                    parts = line.split()
                    if len(parts) >= 4:
                        routes.append({"destination": parts[0], "netmask": parts[1],
                                       "gateway": parts[2], "interface": parts[3]})
            return routes[:10]
        except:
            return []

    def _get_default_gateway(self):
        try:
            result = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=5)
            for line in result.stdout.splitlines():
                if "Default Gateway" in line and ":" in line:
                    gw = line.split(":")[-1].strip()
                    if gw:
                        return gw
            return "N/A"
        except:
            return "N/A"

    def _get_public_ip(self):
        try:
            import urllib.request
            return urllib.request.urlopen("https://api.ipify.org", timeout=5).read().decode()
        except:
            return "No internet / Timeout"

    def _get_virtualization(self, c):
        try:
            system = c.Win32_ComputerSystem()[0]
            model = (system.Model or "").lower()
            manufacturer = (system.Manufacturer or "").lower()
            virt_keywords = {"vmware": "VMware", "virtualbox": "VirtualBox",
                             "hyper-v": "Hyper-V", "kvm": "KVM", "qemu": "QEMU", "xen": "Xen"}
            for key, name in virt_keywords.items():
                if key in model or key in manufacturer:
                    return {"type": name, "is_vm": True}
            return {"type": "Physical Machine", "is_vm": False}
        except:
            return {"type": "Unknown", "is_vm": False}

    def _get_bandwidth(self):
        import time
        try:
            net1 = psutil.net_io_counters()
            time.sleep(1)
            net2 = psutil.net_io_counters()
            sent = (net2.bytes_sent - net1.bytes_sent) / 1024
            recv = (net2.bytes_recv - net1.bytes_recv) / 1024
            return {"sent": f"{sent:.1f} KB/s", "recv": f"{recv:.1f} KB/s",
                    "total_sent": f"{net2.bytes_sent // (1024**2)} MB",
                    "total_recv": f"{net2.bytes_recv // (1024**2)} MB"}
        except:
            return {"sent": "N/A", "recv": "N/A", "total_sent": "N/A", "total_recv": "N/A"}

    def _build_ui(self, data):
        self.loading_label.destroy()
        self.refresh_btn.configure(text=get("refresh"), state="normal")

        ctk.CTkLabel(self.frame, text=get("cloud_title"),
                     font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
                     text_color=COLORS["text_white"]).pack(anchor="w", pady=(0, 15))

        self._build_summary(data)
        self._build_interfaces(data["interfaces"])
        self._build_dns(data["dns"])
        self._build_routing(data["routing"])
        self._build_virtualization(data["virtualization"])

    def _build_summary(self, data):
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=8)
        header = ctk.CTkFrame(card, fg_color=COLORS["selected"], corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(header, text=get("net_summary"),
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=COLORS["text_white"]).pack(side="left", padx=15, pady=8)
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=(5, 12))
        row.grid_columnconfigure((0, 1, 2, 3), weight=1)
        stats = [
            ("🌐 Public IP", data["public_ip"],         COLORS["accent"]),
            ("🚪 Gateway",   data["gateway"],            COLORS["green"]),
            ("📤 Upload",    data["bandwidth"]["sent"],  COLORS["orange"]),
            ("📥 Download",  data["bandwidth"]["recv"],  COLORS["green"]),
        ]
        for i, (label, value, color) in enumerate(stats):
            col = ctk.CTkFrame(row, fg_color=COLORS["bar_bg"], corner_radius=8)
            col.grid(row=0, column=i, padx=5, sticky="ew")
            ctk.CTkLabel(col, text=value,
                         font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                         text_color=color).pack(pady=(10, 2))
            ctk.CTkLabel(col, text=label,
                         font=ctk.CTkFont(family="Segoe UI", size=10),
                         text_color=COLORS["text_gray"]).pack(pady=(0, 10))

    def _build_interfaces(self, interfaces):
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=8)
        header = ctk.CTkFrame(card, fg_color=COLORS["selected"], corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(header, text=f"{get('interfaces')} ({len(interfaces)})",
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=COLORS["text_white"]).pack(side="left", padx=15, pady=8)
        for iface in interfaces:
            color = COLORS["green"] if iface["up"] else COLORS["text_gray"]
            icon = "🟢" if iface["up"] else "🔴"
            iface_card = ctk.CTkFrame(card, fg_color=COLORS["bar_bg"], corner_radius=8)
            iface_card.pack(fill="x", padx=12, pady=3)
            inner = ctk.CTkFrame(iface_card, fg_color="transparent")
            inner.pack(fill="x", padx=10, pady=8)
            ctk.CTkLabel(inner, text=f"{icon} {iface['name'][:20]}",
                         font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                         text_color=color, width=180, anchor="w").pack(side="left")
            ctk.CTkLabel(inner, text=f"IPv4: {iface['ipv4']}",
                         font=ctk.CTkFont(family="Segoe UI", size=11),
                         text_color=COLORS["text_white"], width=160, anchor="w").pack(side="left")
            ctk.CTkLabel(inner, text=f"Speed: {iface['speed']}",
                         font=ctk.CTkFont(family="Segoe UI", size=11),
                         text_color=COLORS["accent"]).pack(side="right")
        ctk.CTkFrame(card, height=1, fg_color=COLORS["bar_bg"]).pack(fill="x", padx=15, pady=8)

    def _build_dns(self, dns_list):
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=8)
        header = ctk.CTkFrame(card, fg_color=COLORS["selected"], corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(header, text=get("dns"),
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=COLORS["text_white"]).pack(side="left", padx=15, pady=8)
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=(5, 12))
        for dns in dns_list:
            ctk.CTkLabel(row, text=f"🔹  {dns}",
                         font=ctk.CTkFont(family="Segoe UI", size=12),
                         text_color=COLORS["accent"]).pack(anchor="w", pady=2)

    def _build_routing(self, routes):
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=8)
        header = ctk.CTkFrame(card, fg_color=COLORS["selected"], corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(header, text=f"{get('routing')} (Top 10)",
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=COLORS["text_white"]).pack(side="left", padx=15, pady=8)
        if not routes:
            ctk.CTkLabel(card, text="No routes found",
                         font=ctk.CTkFont(family="Segoe UI", size=12),
                         text_color=COLORS["text_gray"]).pack(pady=10)
        else:
            for route in routes:
                row = ctk.CTkFrame(card, fg_color=COLORS["bar_bg"], corner_radius=6)
                row.pack(fill="x", padx=12, pady=2)
                inner = ctk.CTkFrame(row, fg_color="transparent")
                inner.pack(fill="x", padx=10, pady=6)
                ctk.CTkLabel(inner, text=route["destination"],
                             font=ctk.CTkFont(family="Segoe UI", size=11),
                             text_color=COLORS["text_white"], width=120, anchor="w").pack(side="left")
                ctk.CTkLabel(inner, text=route["netmask"],
                             font=ctk.CTkFont(family="Segoe UI", size=11),
                             text_color=COLORS["text_gray"], width=120, anchor="w").pack(side="left")
                ctk.CTkLabel(inner, text=f"→ {route['gateway']}",
                             font=ctk.CTkFont(family="Segoe UI", size=11),
                             text_color=COLORS["accent"], anchor="w").pack(side="left")
        ctk.CTkFrame(card, height=1, fg_color=COLORS["bar_bg"]).pack(fill="x", padx=15, pady=8)

    def _build_virtualization(self, virt):
        card = ctk.CTkFrame(self.frame, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=8)
        header = ctk.CTkFrame(card, fg_color=COLORS["selected"], corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(header, text=get("virt"),
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=COLORS["text_white"]).pack(side="left", padx=15, pady=8)
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=(5, 12))
        color = COLORS["orange"] if virt["is_vm"] else COLORS["green"]
        icon = "☁️" if virt["is_vm"] else "🖥️"
        ctk.CTkLabel(row, text=f"{icon}  {virt['type']}",
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=color).pack(side="left")