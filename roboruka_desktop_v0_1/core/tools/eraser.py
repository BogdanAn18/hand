from PySide6.QtCore import QPointF
from core.tools.base import Tool


class EraserTool(Tool):
    name = "Eraser"

    def begin(self, point: QPointF):
        self.current = point

    def update(self, point: QPointF):
        self.current = point

    def finish(self, point: QPointF):
        self.current = None
        return None
