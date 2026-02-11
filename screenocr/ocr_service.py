import threading
from pathlib import Path

from paddleocr import PaddleOCR
from PIL import Image

from .config import TEMP_CAPTURE_FILE


class OCRService:
    def __init__(self):
        self._model = None
        self._model_lock = threading.Lock()
        self._ready_event = threading.Event()
        self._load_error = None
        self._preload_started = False
        self._preload_lock = threading.Lock()

    @property
    def load_error(self):
        return self._load_error

    @property
    def is_ready(self):
        return self._ready_event.is_set() and self._load_error is None

    def preload_async(self):
        with self._preload_lock:
            if self._preload_started:
                return
            self._preload_started = True
        threading.Thread(target=self._preload_worker, daemon=True).start()

    def _preload_worker(self):
        try:
            self._get_model()
            self._ready_event.set()
        except Exception as exc:
            self._load_error = str(exc)

    def _get_model(self):
        if self._model is not None:
            return self._model

        with self._model_lock:
            if self._model is None:
                self._model = PaddleOCR(
                    text_detection_model_name="PP-OCRv5_mobile_det",
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=True,
                )
        return self._model

    def predict_text_from_image(self, image: Image.Image):
        tmp_file = Path(TEMP_CAPTURE_FILE)
        try:
            image.save(tmp_file)
            model = self._get_model()
            result = model.predict(str(tmp_file))
            text_lines = []
            for row in result:
                text_lines.extend(row.get("rec_texts", []))
            text = "\n".join(text_lines).strip()
            return text or "[No text detected]"
        finally:
            try:
                if tmp_file.exists():
                    tmp_file.unlink()
            except OSError:
                pass

