from PySide6.QtCore import QPointF


class CoordinateMapper:
    """Maps normalized controller coordinates to canvas pixel coordinates."""

    @staticmethod
    def to_canvas(x: float, y: float, width: float, height: float) -> QPointF:
        return QPointF(max(0.0, min(1.0, x)) * width,
                       max(0.0, min(1.0, y)) * height)
