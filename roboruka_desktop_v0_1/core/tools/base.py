from abc import ABC, abstractmethod
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
from core.stroke import DrawObject


class Tool(ABC):
    name = "Tool"

    def __init__(self, color: QColor, width: float):
        self.color = QColor(color)
        self.width = width
        self.current = None

    @abstractmethod
    def begin(self, point: QPointF): ...

    @abstractmethod
    def update(self, point: QPointF): ...

    @abstractmethod
    def finish(self, point: QPointF): ...

    def cancel(self):
        self.current = None
