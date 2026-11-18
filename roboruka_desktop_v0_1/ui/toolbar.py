from PySide6.QtWidgets import QToolBar, QColorDialog, QSpinBox, QLabel
from PySide6.QtGui import QAction, QColor
from PySide6.QtCore import Signal


class WhiteboardToolbar(QToolBar):
    tool_selected = Signal(str)
    color_changed = Signal(QColor)
    width_changed = Signal(float)
    undo_requested = Signal()
    redo_requested = Signal()
    clear_requested = Signal()

    def __init__(self, parent=None):
        super().__init__("Tools", parent)
        self.setMovable(False)
        for name in ("Pen", "Line", "Rectangle", "Ellipse", "Eraser"):
            action = QAction(name, self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked=False, n=name: self._select(n))
            self.addAction(action)
            if name == "Pen":
                action.setChecked(True)
        self.addSeparator()
        self.color_action = QAction("Color", self)
        self.color_action.triggered.connect(self._choose_color)
        self.addAction(self.color_action)
        self.addWidget(QLabel(" Width "))
        self.width_box = QSpinBox()
        self.width_box.setRange(1, 40)
        self.width_box.setValue(3)
        self.width_box.valueChanged.connect(lambda v: self.width_changed.emit(float(v)))
        self.addWidget(self.width_box)
        self.addSeparator()
        undo = QAction("Undo", self)
        undo.setShortcut("Ctrl+Z")
        undo.triggered.connect(self.undo_requested)
        self.addAction(undo)
        redo = QAction("Redo", self)
        redo.setShortcut("Ctrl+Y")
        redo.triggered.connect(self.redo_requested)
        self.addAction(redo)
        clear = QAction("Clear", self)
        clear.triggered.connect(self.clear_requested)
        self.addAction(clear)

    def _select(self, name):
        for action in self.actions():
            if action.isCheckable():
                action.setChecked(action.text() == name)
        self.tool_selected.emit(name.lower())

    def _choose_color(self):
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self.color_changed.emit(color)
