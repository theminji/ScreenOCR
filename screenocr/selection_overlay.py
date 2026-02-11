import ctypes
import tkinter as tk


class SelectionOverlay:
    def __init__(self, root: tk.Tk, on_complete, on_cancel):
        self.root = root
        self.on_complete = on_complete
        self.on_cancel = on_cancel
        self.start_x = 0
        self.start_y = 0
        self.rect_id = None
        self.virtual_left, self.virtual_top, self.virtual_width, self.virtual_height = self.get_virtual_screen_rect()

        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.attributes("-alpha", 0.22)
        self.window.configure(bg="black")
        self.window.geometry(
            f"{self.virtual_width}x{self.virtual_height}+{self.virtual_left}+{self.virtual_top}"
        )
        self.window.focus_force()

        self.canvas = tk.Canvas(
            self.window,
            cursor="cross",
            highlightthickness=0,
            bg="black",
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.window.bind("<Escape>", self.cancel)

    @staticmethod
    def get_virtual_screen_rect():
        user32 = ctypes.windll.user32
        left = user32.GetSystemMetrics(76)   # SM_XVIRTUALSCREEN
        top = user32.GetSystemMetrics(77)    # SM_YVIRTUALSCREEN
        width = user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
        height = user32.GetSystemMetrics(79) # SM_CYVIRTUALSCREEN
        return left, top, width, height

    def on_mouse_down(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect_id is not None:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.start_x,
            self.start_y,
            outline="#58a6ff",
            width=2,
        )

    def on_mouse_drag(self, event):
        if self.rect_id is None:
            return
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def on_mouse_up(self, event):
        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)
        self.window.destroy()

        if x2 - x1 < 5 or y2 - y1 < 5:
            self.on_cancel("Selection too small.")
            return

        absolute_bbox = (
            x1 + self.virtual_left,
            y1 + self.virtual_top,
            x2 + self.virtual_left,
            y2 + self.virtual_top,
        )
        self.root.after(80, lambda: self.on_complete(absolute_bbox))

    def cancel(self, _event=None):
        self.window.destroy()
        self.on_cancel("Selection canceled.")

