import customtkinter as ctk
import threading
import time
import tkinter as tk

COLORS = {
    "bg_dark":     "#0A0F1E",
    "bg_card":     "#0D1B2A",
    "accent":      "#1E90FF",
    "accent_glow": "#63B3ED",
    "text_white":  "#E8F4FD",
    "text_gray":   "#8BA3BF",
    "bar_bg":      "#1A2744",
}

class SplashScreen:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("")
        self.root.overrideredirect(True)

        width, height = 650, 400
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.configure(fg_color=COLORS["bg_dark"])

        self.progress_value = 0
        self._build_ui()

    def _build_ui(self):
        self.canvas = tk.Canvas(
            self.root,
            width=650, height=400,
            bg=COLORS["bg_dark"],
            highlightthickness=0
        )
        self.canvas.place(x=0, y=0)

        for i in range(0, 650, 40):
            self.canvas.create_line(i, 0, i, 400, fill="#0D1B2A", width=1)
        for i in range(0, 400, 40):
            self.canvas.create_line(0, i, 650, i, fill="#0D1B2A", width=1)

        self.canvas.create_oval(470, -80, 750, 200, outline=COLORS["bar_bg"], width=2, fill="")
        self.canvas.create_oval(-100, 200, 180, 480, outline=COLORS["bar_bg"], width=2, fill="")

        ctk.CTkLabel(
            self.root,
            text="T-TOOLS",
            font=ctk.CTkFont(family="Segoe UI", size=72, weight="bold"),
            text_color=COLORS["accent"]
        ).place(x=325, y=100, anchor="center")

        ctk.CTkLabel(
            self.root,
            text="⚡",
            font=ctk.CTkFont(size=30),
        ).place(x=530, y=85, anchor="center")

        ctk.CTkLabel(
            self.root,
            text="Infrastructure Suite",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=COLORS["text_gray"]
        ).place(x=325, y=158, anchor="center")

        self.canvas.create_line(125, 185, 525, 185, fill=COLORS["accent"], width=1)

        self.bar = ctk.CTkProgressBar(
            self.root,
            width=400, height=5,
            fg_color=COLORS["bar_bg"],
            progress_color=COLORS["accent"],
            corner_radius=3
        )
        self.bar.place(x=325, y=230, anchor="center")
        self.bar.set(0)

        self.status_label = ctk.CTkLabel(
            self.root,
            text="Initializing...",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_gray"]
        )
        self.status_label.place(x=325, y=260, anchor="center")

        self.dots_label = ctk.CTkLabel(
            self.root,
            text="● ○ ○",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS["accent"]
        )
        self.dots_label.place(x=325, y=290, anchor="center")

        ctk.CTkLabel(
            self.root,
            text="v1.0.0  |  Windows Edition  |  t-tools.site",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLORS["bar_bg"]
        ).place(x=325, y=375, anchor="center")

        self._animate_dots()

    def _animate_dots(self):
        frames = ["●  ○  ○", "○  ●  ○", "○  ○  ●", "○  ●  ○"]
        self._dot_frame = getattr(self, '_dot_frame', 0)
        self._dot_frame = (self._dot_frame + 1) % len(frames)
        self.dots_label.configure(text=frames[self._dot_frame])
        if hasattr(self, '_running') and not self._running:
            return
        self.root.after(300, self._animate_dots)

    def _animate_loading(self):
        self._running = True
        steps = [
            (0.15, "Loading hardware modules..."),
            (0.30, "Loading network modules..."),
            (0.50, "Loading security modules..."),
            (0.65, "Loading IT modules..."),
            (0.80, "Loading cloud modules..."),
            (0.95, "Almost ready..."),
            (1.0,  "Welcome to T-TOOLS!"),
        ]
        for value, message in steps:
            time.sleep(0.5)
            self.bar.set(value)
            self.status_label.configure(text=message)
            if value == 1.0:
                self.status_label.configure(text_color=COLORS["accent"])

        time.sleep(0.4)
        self._running = False
        self.root.after(0, self.root.destroy)

    def run(self):
        threading.Thread(target=self._animate_loading, daemon=True).start()
        self.root.mainloop()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    splash = SplashScreen()
    splash.run()