from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal


@dataclass
class PointerState:
    x: float
    y: float
    drawing: bool = False
    connected: bool = True
    timestamp_ms: int = 0


class InputProvider(QObject):
    pointer_changed = Signal(object)  # PointerState
    connection_changed = Signal(bool, str)

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError
