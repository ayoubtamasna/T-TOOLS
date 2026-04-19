import customtkinter as ctk
from datetime import datetime
import threading
import pythoncom
from languages.translations import get, set_lang
from utils.updater import AutoUpdater

COLORS = {
    "bg_dark":    "#0A0F1E",
    "bg_card":    "#0D1B2A",
    "sidebar":    "#080D1A",
    "accent":     "#1E90FF",
    "accent_glow":"#63B3ED",
    "text_white": "#E8F4FD",
    "text_gray":  "#8BA3BF",
    "bar_bg":     "#1A2744",
    "hover":      "#1A2744",
    "selected":   "#1E3A5F",
    "green":      "#00C896",
}

class MainWindow:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("T-TOOLS - Infrastructure Suite")
        self.root.geometry("1100x680")
        self.root.minsize(900, 600)
        self.root.configure(fg_color=COLORS["bg_dark"])
        self.active_tab = None
        self.active_graphs = None
        self.active_alerts = None
        self.current_lang = "en"
        self._build_ui()
        # Auto check updates عند البداية
        self.updater = AutoUpdater(self.root)
        self.root.after(3000, lambda: self.updater.check_for_updates(silent=True))

    def _build_ui(self):
        self._build_header()
        body = ctk.CTkFrame(self.root, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)
        self._build_sidebar(body)
        self._build_content(body)

    def _build_header(self):
        header = ctk.CTkFrame(self.root, fg_color=COLORS["bg_card"], height=55, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="⚡ T-TOOLS",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(side="left", padx=20)

        self.subtitle_label = ctk.CTkLabel(
            header,
            text=get("app_subtitle"),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_gray"]
        )
        self.subtitle_label.pack(side="left", padx=5)

        self.time_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_gray"]
        )
        self.time_label.pack(side="right", padx=20)
        self._update_time()

        lang_frame = ctk.CTkFrame(header, fg_color="transparent")
        lang_frame.pack(side="right", padx=10)

        for lang, flag in [("en", "GB"), ("ar", "SA"), ("fr", "FR")]:
            ctk.CTkButton(
                lang_frame,
                text=flag,
                width=35,
                height=30,
                fg_color=COLORS["selected"] if lang == self.current_lang else "transparent",
                hover_color=COLORS["hover"],
                corner_radius=6,
                font=ctk.CTkFont(size=12),
                command=lambda l=lang: self._change_lang(l)
            ).pack(side="left", padx=2)

    def _change_lang(self, lang):
        self.current_lang = lang
        set_lang(lang)
        self._refresh_ui()

    def _refresh_ui(self):
        self.subtitle_label.configure(text=get("app_subtitle"))
        for key, btn in self.tab_buttons.items():
            btn.configure(text=get(key))
        self.export_btn.configure(text=get("export"))
        self.about_btn.configure(text=get("about"))
        self.modules_label.configure(text=get("modules"))
        if self.active_tab is None:
            self._show_welcome()

    def _update_time(self):
        now = datetime.now().strftime("%Y-%m-%d  |  %H:%M:%S")
        self.time_label.configure(text=now)
        self.root.after(1000, self._update_time)

    def _build_sidebar(self, parent):
        sidebar = ctk.CTkFrame(parent, fg_color=COLORS["sidebar"], width=200, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        self.modules_label = ctk.CTkLabel(
            sidebar,
            text=get("modules"),
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=COLORS["text_gray"]
        )
        self.modules_label.pack(pady=(20, 10), padx=15, anchor="w")

        self.tabs = [
            ("general", "general"),
            ("graphs",  "graphs"),
            ("health",  "health"),
            ("alerts",  "alerts"),
            ("ports",   "ports"),
            ("wps",     "wps"),
            ("cyber",   "cyber"),
            ("it",      "it"),
            ("cloud",   "cloud"),
        ]

        self.tab_buttons = {}
        for key, trans_key in self.tabs:
            btn = ctk.CTkButton(
                sidebar,
                text=get(trans_key),
                anchor="w",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                fg_color="transparent",
                text_color=COLORS["text_gray"],
                hover_color=COLORS["hover"],
                corner_radius=8,
                height=42,
                command=lambda k=key: self._switch_tab(k)
            )
            btn.pack(fill="x", padx=10, pady=3)
            self.tab_buttons[key] = btn

        ctk.CTkFrame(sidebar, height=1, fg_color=COLORS["bar_bg"]).pack(fill="x", padx=15, pady=20)

        self.export_btn = ctk.CTkButton(
            sidebar,
            text=get("export"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_glow"],
            corner_radius=8,
            height=38,
            command=self._export
        )
        self.export_btn.pack(fill="x", padx=10, pady=5)

        self.export_status = ctk.CTkLabel(
            sidebar,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS["green"]
        )
        self.export_status.pack(pady=2)

        # زر Check Updates
        self.check_update_btn = ctk.CTkButton(
            sidebar,
            text="🔄  Check Updates",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            hover_color=COLORS["hover"],
            text_color=COLORS["text_gray"],
            corner_radius=8,
            height=35,
            command=lambda: AutoUpdater(self.root).check_for_updates(silent=False)
        )
        self.check_update_btn.pack(fill="x", padx=10, pady=(0, 5))

        self.about_btn = ctk.CTkButton(
            sidebar,
            text=get("about"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            hover_color=COLORS["hover"],
            text_color=COLORS["text_gray"],
            corner_radius=8,
            height=35,
            command=self._show_about
        )
        self.about_btn.pack(fill="x", padx=10, pady=(0, 10))

    def _build_content(self, parent):
        self.content_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self._show_welcome()

    def _show_welcome(self):
        self._clear_content()

        ctk.CTkLabel(
            self.content_frame,
            text="⚡",
            font=ctk.CTkFont(size=60)
        ).pack(pady=(80, 5))

        ctk.CTkLabel(
            self.content_frame,
            text="T-TOOLS",
            font=ctk.CTkFont(family="Segoe UI", size=48, weight="bold"),
            text_color=COLORS["accent"]
        ).pack()

        ctk.CTkLabel(
            self.content_frame,
            text=get("welcome_sub"),
            font=ctk.CTkFont(family="Segoe UI", size=15),
            text_color=COLORS["text_gray"]
        ).pack(pady=5)

        ctk.CTkFrame(
            self.content_frame,
            height=1,
            fg_color=COLORS["bar_bg"],
            width=400
        ).pack(pady=10)

        ctk.CTkLabel(
            self.content_frame,
            text=get("welcome_msg"),
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_gray"]
        ).pack()

        ctk.CTkLabel(
            self.content_frame,
            text="t-tools.site",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["bar_bg"]
        ).pack(pady=5)

    def _switch_tab(self, key):
        from ui.tab_general import GeneralTab
        from ui.tab_graphs import GraphsTab
        from ui.tab_health import HealthTab
        from ui.tab_alerts import AlertsTab
        from ui.tab_ports import PortsTab
        from ui.tab_wps import WPSTab
        from ui.tab_cyber import CyberTab
        from ui.tab_it import ITTab
        from ui.tab_cloud import CloudTab

        if self.active_graphs:
            self.active_graphs.destroy()
            self.active_graphs = None

        if self.active_alerts:
            self.active_alerts.destroy()
            self.active_alerts = None

        for k, btn in self.tab_buttons.items():
            if k == key:
                btn.configure(fg_color=COLORS["selected"], text_color=COLORS["text_white"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_gray"])

        self.active_tab = key
        self._clear_content()

        if key == "general":
            GeneralTab(self.content_frame)
        elif key == "graphs":
            self.active_graphs = GraphsTab(self.content_frame)
        elif key == "health":
            HealthTab(self.content_frame)
        elif key == "alerts":
            self.active_alerts = AlertsTab(self.content_frame)
        elif key == "ports":
            PortsTab(self.content_frame)
        elif key == "wps":
            WPSTab(self.content_frame)
        elif key == "cyber":
            CyberTab(self.content_frame)
        elif key == "it":
            ITTab(self.content_frame)
        elif key == "cloud":
            CloudTab(self.content_frame)

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _show_about(self):
        from ui.about_window import AboutWindow
        AboutWindow(self.root)

    def _export(self):
        self.export_btn.configure(text=get("generating"), state="disabled")
        self.export_status.configure(text="")
        threading.Thread(target=self._export_worker, daemon=True).start()

    def _export_worker(self):
        try:
            pythoncom.CoInitialize()
            from collectors.hardware import (
                get_cpu_info, get_ram_info, get_gpu_info,
                get_motherboard_info, get_disk_info, get_os_info
            )
            from utils.exporter import export_report, export_json

            data = {
                "os":    get_os_info(),
                "cpu":   get_cpu_info(),
                "ram":   get_ram_info(),
                "gpu":   get_gpu_info(),
                "board": get_motherboard_info(),
                "disk":  get_disk_info(),
            }

            pdf_path  = export_report(data)
            json_path = export_json(data)

            self.root.after(0, lambda: self._export_done(pdf_path))

        except Exception as e:
            self.root.after(0, lambda: self._export_error(str(e)))

    def _export_done(self, path):
        self.export_btn.configure(text=get("export"), state="normal")
        self.export_status.configure(text=get("export_done"), text_color=COLORS["green"])
        self.root.after(4000, lambda: self.export_status.configure(text=""))

    def _export_error(self, error):
        self.export_btn.configure(text=get("export"), state="normal")
        self.export_status.configure(text=get("export_fail"), text_color="#FF4444")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = MainWindow()
    app.run()