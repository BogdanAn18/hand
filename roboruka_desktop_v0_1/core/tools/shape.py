from PySide6.QtCore import QPointF
from core.tools.base import Tool
from core.stroke import DrawObject


class ShapeTool(Tool):
    def __init__(self, kind, color, width):
        super().__init__(color, width)
        self.kind = kind
        self.name = kind.title()

    def begin(self, point: QPointF):
        self.current = DrawObject(self.kind, [QPointF(point), QPointF(point)], self.color, self.width)

    def update(self, point: QPointF):
        if self.current is not None:
            self.current.points[1] = QPointF(point)

    def finish(self, point: QPointF):
        if self.current is None:
            self.begin(point)
        self.update(point)
        result, self.current = self.current, None
        return result
