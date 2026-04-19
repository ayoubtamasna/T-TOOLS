import requests
import subprocess
import os
import sys
import threading
import tempfile
import customtkinter as ctk
from languages.translations import get

CURRENT_VERSION = "1.0.0"
VERSION_URL = "https://t-tools.site/version.json"

COLORS = {
    "bg_dark":   "#0A0F1E",
    "bg_card":   "#0D1B2A",
    "accent":    "#1E90FF",
    "text_white":"#E8F4FD",
    "text_gray": "#8BA3BF",
    "bar_bg":    "#1A2744",
    "selected":  "#1E3A5F",
    "green":     "#00C896",
}

class AutoUpdater:
    def __init__(self, parent_window):
        self.parent = parent_window

    def check_for_updates(self, silent=False):
        threading.Thread(
            target=self._check_worker,
            args=(silent,),
            daemon=True
        ).start()

    def _check_worker(self, silent):
        try:
            response = requests.get(VERSION_URL, timeout=5)
            data = response.json()
            latest = data.get("version", "1.0.0")
            download_url = data.get("download_url", "")
            changelog = data.get("changelog", "")

            if self._is_newer(latest, CURRENT_VERSION):
                self.parent.after(0, lambda: self._show_update_dialog(
                    latest, download_url, changelog
                ))
            else:
                if not silent:
                    self.parent.after(0, self._show_no_update)

        except Exception as e:
            if not silent:
                self.parent.after(0, lambda: self._show_error(str(e)))

    def _is_newer(self, latest, current):
        try:
            l = list(map(int, latest.split(".")))
            c = list(map(int, current.split(".")))
            return l > c
        except:
            return False

    def _show_update_dialog(self, version, download_url, changelog):
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("T-TOOLS Update")
        dialog.geometry("420x300")
        dialog.resizable(False, False)
        dialog.configure(fg_color=COLORS["bg_dark"])
        dialog.grab_set()

        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - 210
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - 150
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            dialog,
            text="⚡ T-TOOLS",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(pady=(25, 5))

        ctk.CTkLabel(
            dialog,
            text=f"🎉 {get('update_available')} v{version}",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=COLORS["text_white"]
        ).pack(pady=5)

        ctk.CTkLabel(
            dialog,
            text=changelog,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_gray"]
        ).pack(pady=3)

        self.progress_bar = ctk.CTkProgressBar(
            dialog,
            width=300, height=8,
            fg_color=COLORS["bar_bg"],
            progress_color=COLORS["accent"],
            corner_radius=4
        )
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            dialog,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_gray"]
        )
        self.status_label.pack(pady=5)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=15)

        self.dl_btn = ctk.CTkButton(
            btn_frame,
            text=f"⬇️  {get('download_install')}",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color="#1565C0",
            corner_radius=8,
            width=180, height=38,
            command=lambda: self._start_download(download_url, dialog)
        )
        self.dl_btn.pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame,
            text=get("later"),
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=COLORS["selected"],
            hover_color=COLORS["bar_bg"],
            corner_radius=8,
            width=100, height=38,
            command=dialog.destroy
        ).pack(side="left", padx=8)

        self._dialog = dialog

    def _start_download(self, url, dialog):
        self.dl_btn.configure(state="disabled", text=get("downloading"))
        self.progress_bar.pack(pady=5)
        threading.Thread(
            target=self._download_worker,
            args=(url, dialog),
            daemon=True
        ).start()

    def _download_worker(self, url, dialog):
        try:
            response = requests.get(url, stream=True, timeout=30)
            total = int(response.headers.get("content-length", 0))
            downloaded = 0

            tmp = tempfile.NamedTemporaryFile(
                delete=False, suffix=".exe", prefix="T-TOOLS_update_"
            )
            tmp_path = tmp.name

            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    tmp.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = downloaded / total
                        self.parent.after(0, lambda p=pct: (
                            self.progress_bar.set(p),
                            self.status_label.configure(text=f"{int(p*100)}%")
                        ))
            tmp.close()
            self.parent.after(0, lambda: self._install_update(tmp_path, dialog))

        except Exception as e:
            self.parent.after(0, lambda: self.status_label.configure(
                text=f"❌ {get('update_fail')}: {e}",
                text_color="#FF4444"
            ))

    def _install_update(self, exe_path, dialog):
        self.status_label.configure(text=f"✅ {get('installing')}...")
        bat = f'@echo off\ntimeout /t 2 /nobreak >nul\nmove /y "{exe_path}" "{sys.executable}"\nstart "" "{sys.executable}"\n'
        bat_path = os.path.join(tempfile.gettempdir(), "t_tools_update.bat")
        with open(bat_path, "w") as f:
            f.write(bat)
        subprocess.Popen(["cmd", "/c", bat_path], creationflags=subprocess.CREATE_NO_WINDOW)
        dialog.destroy()
        self.parent.destroy()

    def _show_no_update(self):
        import tkinter.messagebox as mb
        mb.showinfo("T-TOOLS", f"✅ {get('up_to_date')} (v{CURRENT_VERSION})")

    def _show_error(self, error):
        import tkinter.messagebox as mb
        mb.showerror("T-TOOLS", f"❌ {get('update_check_fail')}\n{error}")