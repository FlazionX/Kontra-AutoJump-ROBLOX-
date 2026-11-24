import json
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

try:
    from pynput import keyboard
except ImportError:
    keyboard = None

APP_NAME = "Kontra AutoJump"
CONFIG_PATH = Path.home() / "AppData" / "Roaming" / "KontraAutoJump" / "settings.json"
DEFAULTS = {"jump_key": "SPACE", "hotkey": "F6", "start_enabled": False}
KEY_CHOICES = ["SPACE", "W", "A", "S", "D", "E", "Q", "F", "R", "SHIFT", "CTRL", "ALT"]
HOTKEY_CHOICES = ["F6", "F7", "F8", "F9", "F10", "F11", "F12"]


def load_settings():
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return {**DEFAULTS, **{k: data[k] for k in DEFAULTS if k in data}}
    except (OSError, ValueError, TypeError):
        return DEFAULTS.copy()


def save_settings(settings):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def pynput_key(name):
    name = name.upper()
    special = {
        "SPACE": keyboard.Key.space, "SHIFT": keyboard.Key.shift,
        "CTRL": keyboard.Key.ctrl, "ALT": keyboard.Key.alt,
    }
    if name in special:
        return special[name]
    if name.startswith("F") and name[1:].isdigit():
        return getattr(keyboard.Key, "f" + name[1:], None)
    return keyboard.KeyCode.from_char(name.lower())


class JumpController:
    def __init__(self, key_name):
        self.controller = keyboard.Controller()
        self.key_name = key_name
        self.active = False
        self.lock = threading.RLock()

    def set_key(self, key_name):
        with self.lock:
            was_active = self.active
            self.release()
            self.key_name = key_name
            if was_active:
                self.hold()

    def hold(self):
        with self.lock:
            if self.active:
                return
            key = pynput_key(self.key_name)
            if key is None:
                raise ValueError("Не удалось распознать клавишу")
            self.controller.press(key)
            self.active = True

    def release(self):
        with self.lock:
            if not self.active:
                return
            try:
                self.controller.release(pynput_key(self.key_name))
            finally:
                self.active = False

    def toggle(self):
        if self.active:
            self.release()
        else:
            self.hold()


class KontraApp:
    BG = "#f4f6f8"
    CARD = "#ffffff"
    TEXT = "#202631"
    MUTED = "#7a8492"
    BLUE = "#3478f6"
    GREEN = "#1d9b65"
    RED = "#d94b4b"

    def __init__(self, root):
        self.root = root
        self.settings = load_settings()
        self.controller = JumpController(self.settings["jump_key"])
        self.listener = None
        self.hotkey_down = False
        self.closing = False
        self.root.title(APP_NAME)
        self.root.geometry("360x330")
        self.root.resizable(False, False)
        self.root.configure(bg=self.BG)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.setup_style()
        self.build_ui()
        self.start_listener()
        self.refresh_status()
        if self.settings.get("start_enabled"):
            self.root.after(250, self.enable)

    def setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TCombobox", padding=6, fieldbackground="white",
                        background="white", foreground=self.TEXT)
        style.map("TCombobox", fieldbackground=[("readonly", "white")])
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 8))
        style.configure("Primary.TButton", background=self.BLUE, foreground="white")
        style.map("Primary.TButton", background=[("active", "#2465dc")],
                  foreground=[("active", "white")])
        style.configure("Secondary.TButton", background="#e9edf3", foreground=self.TEXT)
        style.map("Secondary.TButton", background=[("active", "#dce3ed")])

    def build_ui(self):
        header = tk.Frame(self.root, bg=self.BG)
        header.pack(fill="x", padx=22, pady=(18, 12))
        tk.Label(header, text="Kontra", bg=self.BG, fg=self.TEXT,
                 font=("Segoe UI", 19, "bold")).pack(anchor="w")
        tk.Label(header, text="AUTO JUMP", bg=self.BG, fg=self.MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 2))

        card = tk.Frame(self.root, bg=self.CARD, highlightthickness=1,
                        highlightbackground="#e5e9ef")
        card.pack(fill="x", padx=18, pady=4)
        status_row = tk.Frame(card, bg=self.CARD)
        status_row.pack(fill="x", padx=16, pady=(15, 5))
        tk.Label(status_row, text="Удержание прыжка", bg=self.CARD, fg=self.TEXT,
                 font=("Segoe UI", 11, "bold")).pack(side="left")
        self.status = tk.Label(status_row, text="OFF", bg="#fcecec", fg=self.RED,
                               font=("Segoe UI", 9, "bold"), padx=10, pady=4)
        self.status.pack(side="right")
        self.toggle_button = ttk.Button(card, text="Включить", style="Primary.TButton",
                                        command=self.toggle)
        self.toggle_button.pack(fill="x", padx=16, pady=(8, 15))

        settings = tk.Frame(self.root, bg=self.BG)
        settings.pack(fill="x", padx=22, pady=(14, 4))
        tk.Label(settings, text="Клавиша прыжка", bg=self.BG, fg=self.MUTED,
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
        tk.Label(settings, text="Горячая клавиша", bg=self.BG, fg=self.MUTED,
                 font=("Segoe UI", 9)).grid(row=0, column=1, sticky="w", padx=(18, 0))
        self.jump_var = tk.StringVar(value=self.settings["jump_key"])
        self.hotkey_var = tk.StringVar(value=self.settings["hotkey"])
        jump_box = ttk.Combobox(settings, textvariable=self.jump_var, values=KEY_CHOICES,
                                state="readonly", width=12)
        hotkey_box = ttk.Combobox(settings, textvariable=self.hotkey_var,
                                  values=HOTKEY_CHOICES, state="readonly", width=12)
        jump_box.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        hotkey_box.grid(row=1, column=1, sticky="ew", padx=(18, 0), pady=(5, 0))
        settings.columnconfigure(0, weight=1)
        settings.columnconfigure(1, weight=1)
        jump_box.bind("<<ComboboxSelected>>", self.settings_changed)
        hotkey_box.bind("<<ComboboxSelected>>", self.settings_changed)

        self.hotkey_hint = tk.Label(
            self.root, text=f"{self.settings['hotkey']} — включить / выключить удержание",
            bg=self.BG, fg=self.MUTED, font=("Segoe UI", 8)
        )
        self.hotkey_hint.pack(pady=(12, 0))
        tk.Label(self.root, text="Работает как обычный ввод клавиатуры Windows",
                 bg=self.BG, fg=self.MUTED, font=("Segoe UI", 8)).pack(pady=(3, 0))

    def start_listener(self):
        if keyboard is None:
            messagebox.showerror("Не найдена библиотека", "Установи зависимости командой:\n\npip install -r requirements.txt")
            return
        try:
            self.listener = keyboard.Listener(
                on_press=self.on_global_key, on_release=self.on_global_key_release
            )
            self.listener.start()
        except Exception as exc:
            messagebox.showerror("Ошибка клавиатуры", f"Не удалось запустить горячую клавишу:\n{exc}")

    def on_global_key(self, key):
        try:
            target = pynput_key(self.settings["hotkey"])
            if key == target and not self.hotkey_down:
                self.hotkey_down = True
                self.root.after(0, self.toggle)
        except Exception:
            pass

    def on_global_key_release(self, key):
        try:
            if key == pynput_key(self.settings["hotkey"]):
                self.hotkey_down = False
        except Exception:
            pass

    def settings_changed(self, _event=None):
        jump = self.jump_var.get()
        hotkey = self.hotkey_var.get()
        if jump == hotkey:
            messagebox.showwarning("Настройки", "Клавиша прыжка и горячая клавиша должны отличаться.")
            self.jump_var.set(self.settings["jump_key"])
            self.hotkey_var.set(self.settings["hotkey"])
            return
        try:
            self.controller.set_key(jump)
            self.settings["jump_key"] = jump
            self.settings["hotkey"] = hotkey
            self.hotkey_down = False
            self.hotkey_hint.configure(
                text=f"{hotkey} — включить / выключить удержание"
            )
            save_settings(self.settings)
            self.refresh_status()
        except Exception as exc:
            messagebox.showerror("Ошибка", f"Не удалось применить настройку:\n{exc}")
            self.disable()

    def enable(self):
        try:
            self.controller.hold()
            self.settings["start_enabled"] = False
            self.refresh_status()
        except Exception as exc:
            messagebox.showerror("Ошибка ввода", f"Не удалось удерживать клавишу:\n{exc}")
            self.disable()

    def disable(self):
        self.controller.release()
        self.refresh_status()

    def toggle(self):
        if self.controller.active:
            self.disable()
        else:
            self.enable()

    def refresh_status(self):
        active = self.controller.active
        self.status.configure(text="ON" if active else "OFF",
                               bg="#e8f7ef" if active else "#fcecec",
                               fg=self.GREEN if active else self.RED)
        self.toggle_button.configure(text="Выключить" if active else "Включить")

    def close(self):
        if self.closing:
            return
        self.closing = True
        try:
            self.controller.release()
            self.settings["jump_key"] = self.jump_var.get()
            self.settings["hotkey"] = self.hotkey_var.get()
            self.settings["start_enabled"] = False
            save_settings(self.settings)
        except Exception:
            pass
        if self.listener is not None:
            self.listener.stop()
        self.root.destroy()


def main():
    if sys.platform != "win32":
        print("Kontra AutoJump предназначен для Windows.")
    root = tk.Tk()
    KontraApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
