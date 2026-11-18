from dataclasses import dataclass
from PySide6.QtCore import QPointF


@dataclass(frozen=True)
class PointerPoint:
    x: float
    y: float

    def to_qpoint(self) -> QPointF:
        return QPointF(self.x, self.y)
