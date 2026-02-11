import subprocess
import sys
import threading
import tkinter as tk
from queue import Empty, Queue
from tempfile import NamedTemporaryFile

import pystray
from PIL import Image, ImageDraw, ImageGrab
from pynput import keyboard
from tkinter import messagebox

from .config import HOTKEY
from .ocr_service import OCRService
from .selection_overlay import SelectionOverlay


class ScreenOCRApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.queue: Queue = Queue()
        self.running_capture = False
        self.tray_icon = None
        self.hotkey_listener = None
        self.ocr_service = OCRService()
        self.ocr_service.preload_async()

        self.root.after(50, self.process_queue)

    def build_tray_icon(self):
        icon_img = Image.new("RGB", (64, 64), color=(13, 17, 23))
        draw = ImageDraw.Draw(icon_img)
        draw.rectangle((10, 10, 54, 54), outline=(201, 209, 217), width=3)
        draw.text((22, 20), "OCR", fill=(88, 166, 255))

        menu = pystray.Menu(
            pystray.MenuItem("Capture OCR", self.on_tray_capture),
            pystray.MenuItem("Exit", self.on_tray_exit),
        )
        self.tray_icon = pystray.Icon("screenocr", icon_img, "Screen OCR", menu)

    def start(self):
        self.build_tray_icon()
        self.start_hotkey_listener()
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
        self.root.mainloop()

    def start_hotkey_listener(self):
        self.hotkey_listener = keyboard.GlobalHotKeys({HOTKEY: self.request_capture})
        self.hotkey_listener.start()

    def request_capture(self):
        self.queue.put(("capture", None))

    def on_tray_capture(self, icon=None, item=None):
        self.request_capture()

    def on_tray_exit(self, icon=None, item=None):
        self.queue.put(("exit", None))

    def process_queue(self):
        try:
            while True:
                event, payload = self.queue.get_nowait()
                if event == "capture":
                    self.begin_capture_flow()
                elif event == "show_text":
                    self.open_editor_window(payload)
                elif event == "error":
                    messagebox.showerror("Screen OCR", payload)
                elif event == "info":
                    messagebox.showinfo("Screen OCR", payload)
                elif event == "exit":
                    self.shutdown()
        except Empty:
            pass
        self.root.after(50, self.process_queue)

    def begin_capture_flow(self):
        if self.running_capture:
            self.queue.put(("info", "OCR is already running."))
            return

        if self.ocr_service.load_error is not None:
            self.queue.put(("error", f"Model loading failed:\n{self.ocr_service.load_error}"))
            return

        if not self.ocr_service.is_ready:
            self.queue.put(("info", "OCR models are still loading. Try again in a moment."))
            return

        self.running_capture = True
        SelectionOverlay(
            self.root,
            on_complete=self.capture_region,
            on_cancel=self.on_capture_canceled,
        )

    def on_capture_canceled(self, _message):
        self.running_capture = False

    def capture_region(self, bbox):
        try:
            image = ImageGrab.grab(bbox=bbox, all_screens=True)
        except Exception as exc:
            self.running_capture = False
            self.queue.put(("error", f"Failed to capture screen region:\n{exc}"))
            return
        threading.Thread(target=self.run_ocr_worker, args=(image,), daemon=True).start()

    def run_ocr_worker(self, image):
        try:
            text = self.ocr_service.predict_text_from_image(image)
            self.queue.put(("show_text", text))
        except Exception as exc:
            self.queue.put(("error", f"OCR failed:\n{exc}"))
        finally:
            self.running_capture = False

    def open_editor_window(self, text: str):
        with NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".txt", delete=False) as tmp:
            tmp.write(text)
            temp_path = tmp.name
        if getattr(sys, "frozen", False):
            cmd = [sys.executable, "--editor", temp_path]
        else:
            cmd = [sys.executable, "-m", "screenocr.cli", "--editor", temp_path]
        subprocess.Popen(cmd, close_fds=True)

    def shutdown(self):
        try:
            if self.hotkey_listener is not None:
                self.hotkey_listener.stop()
        finally:
            if self.tray_icon is not None:
                self.tray_icon.stop()
            self.root.quit()
            self.root.destroy()


def main():
    app = ScreenOCRApp()
    app.start()
