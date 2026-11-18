from PySide6.QtWidgets import QMainWindow, QLabel, QMessageBox
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from ui.canvas_widget import CanvasWidget
from ui.toolbar import WhiteboardToolbar
from input.mouse_input import MouseInput
from input.simulator import SimulatedController
from app.config import APP_NAME, APP_VERSION


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1200, 800)
        self.canvas = CanvasWidget()
        self.toolbar = WhiteboardToolbar(self)
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)
        self.setCentralWidget(self.canvas)
        self.mouse_provider = MouseInput(self)
        self.simulator = SimulatedController(self)
        self.active_input = "mouse"
        self._build_menus()
        self._connect_signals()
        self.status = QLabel("Ready | Input: Mouse | Tool: Pen")
        self.statusBar().addWidget(self.status)
        self._update_history(False, False)

    def _build_menus(self):
        file_menu = self.menuBar().addMenu("&File")
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = self.menuBar().addMenu("&Edit")
        undo = QAction("Undo", self)
        undo.setShortcut("Ctrl+Z")
        undo.triggered.connect(self.canvas.undo)
        edit_menu.addAction(undo)
        redo = QAction("Redo", self)
        redo.setShortcut("Ctrl+Y")
        redo.triggered.connect(self.canvas.redo)
        edit_menu.addAction(redo)

        input_menu = self.menuBar().addMenu("&Input")
        self.mouse_action = QAction("Mouse", self, checkable=True)
        self.sim_action = QAction("Simulated controller", self, checkable=True)
        self.mouse_action.setChecked(True)
        self.mouse_action.triggered.connect(lambda: self.set_input("mouse"))
        self.sim_action.triggered.connect(lambda: self.set_input("simulator"))
        input_menu.addAction(self.mouse_action)
        input_menu.addAction(self.sim_action)

        help_menu = self.menuBar().addMenu("&Help")
        about = QAction("About", self)
        about.triggered.connect(self._about)
        help_menu.addAction(about)

    def _connect_signals(self):
        self.toolbar.tool_selected.connect(self._select_tool)
        self.toolbar.color_changed.connect(self.canvas.set_color)
        self.toolbar.width_changed.connect(self.canvas.set_width)
        self.toolbar.undo_requested.connect(self.canvas.undo)
        self.toolbar.redo_requested.connect(self.canvas.redo)
        self.toolbar.clear_requested.connect(self.canvas.clear)
        self.canvas.history_changed.connect(self._update_history)
        self.simulator.pointer_changed.connect(self.canvas.set_simulated_state)
        self.simulator.connection_changed.connect(self._connection_status)

    def _select_tool(self, name):
        self.canvas.set_tool(name)
        self.status.setText(f"Ready | Input: {self.active_input.title()} | Tool: {name.title()}")

    def set_input(self, mode):
        if mode == self.active_input:
            return
        if mode == "simulator":
            self.mouse_provider.stop()
            self.canvas.set_mouse_enabled(False)
            self.simulator.start()
            self.mouse_action.setChecked(False)
            self.sim_action.setChecked(True)
        else:
            self.simulator.stop()
            self.canvas.set_mouse_enabled(True)
            self.mouse_provider.start()
            self.mouse_action.setChecked(True)
            self.sim_action.setChecked(False)
        self.active_input = mode
        self.status.setText(f"Ready | Input: {mode.title()} | Tool: {self.canvas.tool_name.title()}")
        self.canvas.setFocus()

    def _connection_status(self, connected, message):
        self.status.setText(f"{message} | Tool: {self.canvas.tool_name.title()}")

    def _update_history(self, can_undo, can_redo):
        # Toolbar buttons are intentionally always available; the document safely ignores empty history.
        pass

    def keyPressEvent(self, event):
        if self.active_input == "simulator":
            key = event.text().upper()
            if key in ("W", "A", "S", "D"):
                self.simulator.set_key(key, True)
                event.accept()
                return
            if event.key() == Qt.Key_Space and not event.isAutoRepeat():
                self.simulator.toggle_drawing()
                event.accept()
                return
            if event.key() == Qt.Key_Escape:
                self.simulator.stop_drawing()
                event.accept()
                return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if self.active_input == "simulator":
            key = event.text().upper()
            if key in ("W", "A", "S", "D"):
                self.simulator.set_key(key, False)
                event.accept()
                return
        super().keyReleaseEvent(event)

    def closeEvent(self, event):
        self.simulator.stop()
        self.mouse_provider.stop()
        super().closeEvent(event)

    def _about(self):
        QMessageBox.about(self, "About Roboruka", "Roboruka Desktop v0.1\\nA hardware-independent whiteboard prototype.")
