from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath
from core.document import Document
from core.tools.pen import PenTool
from core.tools.shape import ShapeTool
from core.tools.eraser import EraserTool
from motion.processor import MotionProcessor


class CanvasWidget(QWidget):
    history_changed = Signal(bool, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 420)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setStyleSheet("background: white;")
        self.document = Document()
        self.color = QColor("#202124")
        self.width = 3.0
        self.tool_name = "pen"
        self.tool = PenTool(self.color, self.width)
        self.mouse_enabled = True
        self.sim_state = None
        self.sim_pointer = QPointF(0.5, 0.5)
        self.sim_drawing = False
        self.processor = MotionProcessor()
        self._mouse_drawing = False

    def set_tool(self, name):
        self.tool_name = name
        if name == "pen":
            self.tool = PenTool(self.color, self.width)
        elif name == "eraser":
            self.tool = EraserTool(self.color, self.width)
        else:
            self.tool = ShapeTool(name, self.color, self.width)
        self.update()

    def set_color(self, color):
        self.color = QColor(color)
        self.set_tool(self.tool_name)

    def set_width(self, width):
        self.width = float(width)
        self.set_tool(self.tool_name)

    def set_mouse_enabled(self, enabled):
        self.mouse_enabled = enabled
        self._mouse_drawing = False
        self.update()

    def set_simulated_state(self, state):
        self.sim_pointer = self.processor.process(state.x, state.y, self.width_px(), self.height_px())
        self.sim_drawing = state.drawing
        if self.sim_drawing:
            if self.tool_name == "eraser":
                self.document.erase_at(self.sim_pointer, max(12.0, self.width * 3))
                self._notify_history()
            elif not getattr(self, "_sim_active", False):
                self.tool.begin(self.sim_pointer)
                self._sim_active = True
            else:
                self.tool.update(self.sim_pointer)
        elif getattr(self, "_sim_active", False):
            result = self.tool.finish(self.sim_pointer)
            if result:
                self.document.add(result)
            self._sim_active = False
            self._notify_history()
        self.update()

    def width_px(self):
        return max(1, self.width())

    def height_px(self):
        return max(1, self.height())

    def _notify_history(self):
        self.history_changed.emit(self.document.can_undo, self.document.can_redo)

    def undo(self):
        if self.document.undo():
            self._notify_history()
            self.update()

    def redo(self):
        if self.document.redo():
            self._notify_history()
            self.update()

    def clear(self):
        self.document.clear()
        self._notify_history()
        self.update()

    def _point(self, pos):
        return QPointF(pos.x(), pos.y())

    def mousePressEvent(self, event):
        if not self.mouse_enabled or event.button() != Qt.LeftButton:
            return
        point = self._point(event.position())
        self._mouse_drawing = True
        if self.tool_name == "eraser":
            self.document.erase_at(point, max(12.0, self.width * 3))
            self._notify_history()
        else:
            self.tool.begin(point)
        self.update()

    def mouseMoveEvent(self, event):
        if not self.mouse_enabled:
            return
        point = self._point(event.position())
        if self._mouse_drawing:
            if self.tool_name == "eraser":
                self.document.erase_at(point, max(12.0, self.width * 3))
                self._notify_history()
            else:
                self.tool.update(point)
        self.update()

    def mouseReleaseEvent(self, event):
        if not self.mouse_enabled or event.button() != Qt.LeftButton or not self._mouse_drawing:
            return
        point = self._point(event.position())
        if self.tool_name != "eraser":
            result = self.tool.finish(point)
            if result:
                self.document.add(result)
        self._mouse_drawing = False
        self._notify_history()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("white"))
        for obj in self.document.objects:
            self._draw_object(painter, obj)
        current = getattr(self.tool, "current", None)
        if current is not None and self.tool_name != "eraser":
            self._draw_object(painter, current)
        if not self.mouse_enabled:
            painter.setPen(QPen(QColor("#1976D2"), 2, Qt.DashLine))
            x, y = self.sim_pointer.x(), self.sim_pointer.y()
            painter.drawLine(QPointF(x - 10, y), QPointF(x + 10, y))
            painter.drawLine(QPointF(x, y - 10), QPointF(x, y + 10))
            painter.setBrush(QColor("#1976D2"))
            painter.drawEllipse(QPointF(x, y), 3, 3)

    def _draw_object(self, painter, obj):
        if not obj.points:
            return
        pen = QPen(obj.color, obj.width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        if obj.kind == "path":
            path = QPainterPath(obj.points[0])
            for point in obj.points[1:]:
                path.lineTo(point)
            if len(obj.points) == 1:
                painter.drawPoint(obj.points[0])
            else:
                painter.drawPath(path)
        elif len(obj.points) >= 2:
            from PySide6.QtCore import QRectF
            rect = QRectF(obj.points[0], obj.points[1]).normalized()
            if obj.kind == "line":
                painter.drawLine(obj.points[0], obj.points[1])
            elif obj.kind == "rectangle":
                painter.drawRect(rect)
            elif obj.kind == "ellipse":
                painter.drawEllipse(rect)
