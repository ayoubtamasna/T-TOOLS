import customtkinter as ctk
import webbrowser
import tkinter as tk

COLORS = {
    "bg_dark":    "#0A0F1E",
    "bg_card":    "#0D1B2A",
    "sidebar":    "#080D1A",
    "accent":     "#1E90FF",
    "accent_glow":"#63B3ED",
    "text_white": "#E8F4FD",
    "text_gray":  "#8BA3BF",
    "bar_bg":     "#1A2744",
    "selected":   "#1E3A5F",
    "green":      "#00C896",
    "orange":     "#FFA500",
}

LINKEDIN_URL = "https://www.linkedin.com/in/ayoub-tamasna-b59aa3399"
INSTAGRAM_URL = "https://www.instagram.com/t_a_youb"
WEBSITE_URL   = "https://www.gpu-t.com"  # placeholder

class AboutWindow:
    def __init__(self, parent):
        self.window = ctk.CTkToplevel(parent)
        self.window.title("About GPU-T")
        self.window.geometry("520x620")
        self.window.resizable(False, False)
        self.window.configure(fg_color=COLORS["bg_dark"])
        self.window.grab_set()  # نافذة modal

        self.window.update_idletasks()
        w = self.window.winfo_width()
        h = self.window.winfo_height()
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.window.geometry(f"520x620+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        canvas = tk.Canvas(
            self.window,
            width=520, height=620,
            bg=COLORS["bg_dark"],
            highlightthickness=0
        )
        canvas.place(x=0, y=0)

        canvas.create_oval(350, -80, 620, 190,
                          outline=COLORS["bar_bg"], width=1)
        canvas.create_oval(-100, 400, 170, 670,
                          outline=COLORS["bar_bg"], width=1)

        header = ctk.CTkFrame(
            self.window,
            fg_color=COLORS["bg_card"],
            corner_radius=0,
            height=180
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="⚡",
            font=ctk.CTkFont(size=45),
        ).pack(pady=(25, 0))

        ctk.CTkLabel(
            header,
            text="GPU-T",
            font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"),
            text_color=COLORS["accent"]
        ).pack()

        ctk.CTkLabel(
            header,
            text="Infrastructure Diagnostic Tool",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_gray"]
        ).pack()

        ctk.CTkLabel(
            header,
            text="v1.0.0  |  Windows Edition",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLORS["bar_bg"]
        ).pack(pady=(3, 0))

        ctk.CTkFrame(
            self.window,
            height=1,
            fg_color=COLORS["accent"]
        ).pack(fill="x")

        body = ctk.CTkFrame(self.window, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=25, pady=20)

        dev_card = ctk.CTkFrame(body, fg_color=COLORS["bg_card"], corner_radius=12)
        dev_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            dev_card,
            text="👨‍💻  Developer",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_gray"]
        ).pack(anchor="w", padx=15, pady=(12, 2))

        ctk.CTkLabel(
            dev_card,
            text="AYOUB TAMASNA",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLORS["text_white"]
        ).pack(anchor="w", padx=15)

        ctk.CTkLabel(
            dev_card,
            text="Infrastructure Engineer",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["accent"]
        ).pack(anchor="w", padx=15, pady=(2, 12))

        social_frame = ctk.CTkFrame(body, fg_color="transparent")
        social_frame.pack(fill="x", pady=(0, 15))
        social_frame.grid_columnconfigure((0, 1), weight=1)

        linkedin_btn = ctk.CTkButton(
            social_frame,
            text="🔗  LinkedIn",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#0A66C2",
            hover_color="#004182",
            corner_radius=10,
            height=42,
            command=lambda: webbrowser.open(LINKEDIN_URL)
        )
        linkedin_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        instagram_btn = ctk.CTkButton(
            social_frame,
            text="📸  Instagram",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#C13584",
            hover_color="#833AB4",
            corner_radius=10,
            height=42,
            command=lambda: webbrowser.open(INSTAGRAM_URL)
        )
        instagram_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        ctk.CTkButton(
            body,
            text="🌐  www.gpu-t.com  —  Coming Soon",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=COLORS["selected"],
            hover_color=COLORS["bar_bg"],
            corner_radius=10,
            height=42,
            text_color=COLORS["text_gray"],
            command=lambda: webbrowser.open(WEBSITE_URL)
        ).pack(fill="x", pady=(0, 15))

        mission_card = ctk.CTkFrame(body, fg_color=COLORS["bg_card"], corner_radius=12)
        mission_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            mission_card,
            text="🎯  Mission",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_gray"]
        ).pack(anchor="w", padx=15, pady=(12, 5))

        ctk.CTkLabel(
            mission_card,
            text="GPU-T is built to give Infrastructure, Cyber, IT,\nand Cloud engineers a powerful all-in-one diagnostic\ntool to monitor, analyze, and secure their systems.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_white"],
            justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 12))

        ctk.CTkButton(
            body,
            text="✕  Close",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_glow"],
            corner_radius=10,
            height=40,
            command=self.window.destroy
        ).pack(fill="x")