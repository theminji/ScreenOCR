import sys
from pathlib import Path

class EditorAPI:
    def __init__(self, initial_text: str):
        self.initial_text = initial_text

    def get_initial_text(self):
        return self.initial_text

    def save_text(self, text: str):
        import webview

        window = webview.windows[0]
        file_paths = window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename="ocr.txt",
            file_types=("Text files (*.txt)", "All files (*.*)"),
        )
        if not file_paths:
            return False
        Path(file_paths[0]).write_text(text, encoding="utf-8")
        return True

    def close_window(self):
        import webview

        webview.windows[0].destroy()
        return True


def run_editor_window(text_file: str):
    import webview

    text_path = Path(text_file)
    text = text_path.read_text(encoding="utf-8") if text_path.exists() else ""
    try:
        if text_path.exists():
            text_path.unlink()
    except OSError:
        pass

    api = EditorAPI(text)
    ui_file = Path(__file__).resolve().parent / "ui" / "editor.html"
    webview.create_window(
        "Screen OCR Result",
        url=ui_file.as_uri(),
        js_api=api,
        width=1200,
        height=900,
        min_size=(720, 480),
    )
    webview.start()


def main():
    if len(sys.argv) < 2:
        return
    run_editor_window(sys.argv[1])


if __name__ == "__main__":
    main()
