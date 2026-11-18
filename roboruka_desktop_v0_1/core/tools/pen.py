from PySide6.QtCore import QPointF
from core.tools.base import Tool
from core.stroke import DrawObject


class PenTool(Tool):
    name = "Pen"

    def begin(self, point: QPointF):
        self.current = DrawObject("path", [QPointF(point)], self.color, self.width)

    def update(self, point: QPointF):
        if self.current is not None:
            self.current.points.append(QPointF(point))

    def finish(self, point: QPointF):
        if self.current is None:
            self.begin(point)
        elif not self.current.points or self.current.points[-1] != point:
            self.current.points.append(QPointF(point))
        result, self.current = self.current, None
        return result
