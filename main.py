import customtkinter as ctk
import pythoncom
from splash_screen import SplashScreen
from main_window import MainWindow

def main():
    pythoncom.CoInitialize()
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    splash = SplashScreen()
    splash.run()

    import time
    time.sleep(0.3)

    app = MainWindow()
    app.run()

if __name__ == "__main__":
    main()