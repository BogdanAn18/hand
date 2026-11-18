from PySide6.QtCore import QTimer
from input.provider import InputProvider, PointerState
from app.config import SIMULATOR_STEP


class SimulatedController(InputProvider):
    """Keyboard-driven stand-in for a future motion controller."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.x = 0.5
        self.y = 0.5
        self.drawing = False
        self._keys = set()
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._tick)

    def start(self):
        self.timer.start()
        self.connection_changed.emit(True, "Simulated controller connected")
        self._emit()

    def stop(self):
        self.timer.stop()
        self._keys.clear()
        self.drawing = False
        self.connection_changed.emit(False, "Simulated controller stopped")

    def set_key(self, key, pressed):
        if pressed:
            self._keys.add(key)
        else:
            self._keys.discard(key)

    def toggle_drawing(self):
        self.drawing = not self.drawing
        self._emit()

    def stop_drawing(self):
        self.drawing = False
        self._emit()

    def _tick(self):
        if "A" in self._keys:
            self.x -= SIMULATOR_STEP
        if "D" in self._keys:
            self.x += SIMULATOR_STEP
        if "W" in self._keys:
            self.y -= SIMULATOR_STEP
        if "S" in self._keys:
            self.y += SIMULATOR_STEP
        self.x = max(0.0, min(1.0, self.x))
        self.y = max(0.0, min(1.0, self.y))
        if self._keys:
            self._emit()

    def _emit(self):
        self.pointer_changed.emit(PointerState(self.x, self.y, self.drawing, True))
