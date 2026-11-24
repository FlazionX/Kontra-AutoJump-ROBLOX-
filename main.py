import json
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

try:
    from pynput import keyboard
except ImportError:
    keyboard = None

APP_NAME = "Kontra AutoJump"
CONFIG_PATH = Path.home() / "AppData" / "Roaming" / "KontraAutoJump" / "settings.json"
DEFAULTS = {"interval_ms": 450}
MIN_INTERVAL_MS = 100
MAX_INTERVAL_MS = 1500
PRESS_DURATION = 0.045


def load_settings():
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        value = int(data.get("interval_ms", DEFAULTS["interval_ms"]))
        return {"interval_ms": max(MIN_INTERVAL_MS, min(MAX_INTERVAL_MS, value))}
    except (OSError, ValueError, TypeError):
        return DEFAULTS.copy()


def save_settings(settings):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(settings, indent=2), encoding="utf-8")


class AutoJump:
    """Tap Space at a fixed interval only while the user physically holds Space."""

    def __init__(self, interval_ms=450, on_state=None):
        self.interval_ms = max(MIN_INTERVAL_MS, min(MAX_INTERVAL_MS, int(interval_ms)))
        self.on_state = on_state or (lambda _text: None)
        self.enabled = False
        self.space_held = False
        self._closed = False
        self._lock = threading.RLock()
        self._wake = threading.Event()
        self._synthetic_until = 0.0
        self._controller = keyboard.Controller()
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def set_interval(self, interval_ms):
        with self._lock:
            self.interval_ms = max(MIN_INTERVAL_MS, min(MAX_INTERVAL_MS, int(interval_ms)))
        self._wake.set()

    def set_enabled(self, enabled):
        with self._lock:
            self.enabled = bool(enabled)
            if not self.enabled:
                self.space_held = False
        self._wake.set()
        self.on_state("Ожидание Space" if enabled else "Выключено")

    def physical_press(self):
        with self._lock:
            if self._closed or not self.enabled or self.space_held:
                return
            self.space_held = True
        self._wake.set()
        self.on_state("AutoJump активен")

    def physical_release(self):
        with self._lock:
            self.space_held = False
        self._wake.set()
        if self.enabled:
            self.on_state("Ожидание Space")

    def handle_press(self, key):
        if key == keyboard.Key.space and time.monotonic() > self._synthetic_until:
            self.physical_press()

    def handle_release(self, key):
        if key == keyboard.Key.space and time.monotonic() > self._synthetic_until:
            self.physical_release()

    def _tap(self):
        # Ignore our own generated keyboard events in the global listener.
        self._synthetic_until = time.monotonic() + PRESS_DURATION + 0.08
        self._controller.press(keyboard.Key.space)
        try:
            time.sleep(PRESS_DURATION)
        finally:
            self._controller.release(keyboard.Key.space)

    def _run(self):
        while True:
            with self._lock:
                if self._closed:
                    return
                should_tap = self.enabled and self.space_held
                interval = self.interval_ms / 1000.0
            if not should_tap:
                self._wake.wait(0.1)
                self._wake.clear()
                continue
            started = time.monotonic()
            self._tap()
            remaining = max(0.0, interval - (time.monotonic() - started))
            self._wake.wait(remaining)
            self._wake.clear()

    def close(self):
        with self._lock:
            self.enabled = False
            self.space_held = False
            self._closed = True
        self._wake.set()
        self._worker.join(timeout=1.0)


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
        self.closing = False
        self.listener = None
        self.root.title(APP_NAME)
        self.root.geometry("360x290")
        self.root.resizable(False, False)
        self.root.configure(bg=self.BG)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.setup_style()
        self.build_ui()
        self.autojump = AutoJump(self.settings["interval_ms"], self.set_status)
        self.start_listener()

    def setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 9))
        style.configure("Primary.TButton", background=self.BLUE, foreground="white")
        style.map("Primary.TButton", background=[("active", "#2465dc")])
        style.configure("TEntry", padding=6)

    def build_ui(self):
        header = tk.Frame(self.root, bg=self.BG)
        header.pack(fill="x", padx=22, pady=(17, 10))
        tk.Label(header, text="Kontra", bg=self.BG, fg=self.TEXT,
                 font=("Segoe UI", 19, "bold")).pack(anchor="w")
        tk.Label(header, text="ROBLOX AUTO JUMP", bg=self.BG, fg=self.MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")

        card = tk.Frame(self.root, bg=self.CARD, highlightthickness=1,
                        highlightbackground="#e5e9ef")
        card.pack(fill="x", padx=18, pady=3)
        tk.Label(card, text="Автоматические нажатия Space", bg=self.CARD,
                 fg=self.TEXT, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=15, pady=(13, 4))
        self.status = tk.Label(card, text="Выключено", bg=self.CARD, fg=self.RED,
                               font=("Segoe UI", 9))
        self.status.pack(anchor="w", padx=15, pady=(0, 9))
        self.toggle_button = ttk.Button(card, text="Начать", style="Primary.TButton",
                                        command=self.toggle)
        self.toggle_button.pack(fill="x", padx=15, pady=(0, 14))

        settings = tk.Frame(self.root, bg=self.BG)
        settings.pack(fill="x", padx=22, pady=(13, 3))
        tk.Label(settings, text="Интервал между нажатиями (мс)", bg=self.BG,
                 fg=self.MUTED, font=("Segoe UI", 9)).pack(anchor="w")
        row = tk.Frame(settings, bg=self.BG)
        row.pack(fill="x", pady=(5, 0))
        self.interval_var = tk.StringVar(value=str(self.settings["interval_ms"]))
        self.interval_entry = ttk.Entry(row, textvariable=self.interval_var, width=10)
        self.interval_entry.pack(side="left")
        ttk.Button(row, text="Применить", command=self.apply_interval).pack(side="left", padx=8)
        tk.Label(self.root, text="Нажми «Начать», затем зажми Space в Roblox.",
                 bg=self.BG, fg=self.MUTED, font=("Segoe UI", 8)).pack(pady=(9, 0))
        tk.Label(self.root, text="Отпусти Space — автопрыжки остановятся.",
                 bg=self.BG, fg=self.MUTED, font=("Segoe UI", 8)).pack(pady=(2, 0))

    def start_listener(self):
        if keyboard is None:
            messagebox.showerror("Ошибка", "Установи зависимости: py -m pip install -r requirements.txt")
            return
        try:
            self.listener = keyboard.Listener(
                on_press=self.autojump.handle_press,
                on_release=self.autojump.handle_release,
            )
            self.listener.start()
        except Exception as exc:
            messagebox.showerror("Ошибка клавиатуры", str(exc))

    def set_status(self, text):
        if self.closing:
            return
        def update():
            if self.closing:
                return
            active = self.autojump.enabled
            self.status.configure(
                text=text,
                fg=self.GREEN if active and self.autojump.space_held else
                   (self.BLUE if active else self.RED),
            )
        try:
            self.root.after(0, update)
        except tk.TclError:
            pass

    def apply_interval(self):
        try:
            value = int(self.interval_var.get().strip())
            if not MIN_INTERVAL_MS <= value <= MAX_INTERVAL_MS:
                raise ValueError
            self.autojump.set_interval(value)
            self.settings["interval_ms"] = value
            save_settings(self.settings)
        except ValueError:
            messagebox.showwarning("Интервал", f"Укажи число от {MIN_INTERVAL_MS} до {MAX_INTERVAL_MS} мс.")

    def toggle(self):
        enabled = not self.autojump.enabled
        self.autojump.set_enabled(enabled)
        self.toggle_button.configure(text="Остановить" if enabled else "Начать")

    def close(self):
        if self.closing:
            return
        self.closing = True
        try:
            self.settings["interval_ms"] = self.autojump.interval_ms
            save_settings(self.settings)
            self.autojump.close()
            if self.listener is not None:
                self.listener.stop()
        finally:
            self.root.destroy()


def main():
    if sys.platform != "win32":
        print("Kontra AutoJump предназначен для Windows.")
    root = tk.Tk()
    KontraApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
