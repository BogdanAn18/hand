from PySide6.QtCore import QObject, Signal
from communication.protocol import parse_message, ProtocolError


class SerialManager(QObject):
    """Serial transport seam. Open/read loop can be enabled when firmware is ready."""
    message_received = Signal(object)
    error = Signal(str)
    connection_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._serial = None

    def connect_port(self, port: str, baudrate: int = 115200):
        try:
            import serial
            self._serial = serial.Serial(port, baudrate=baudrate, timeout=0.1)
            self.connection_changed.emit(True)
        except Exception as exc:
            self.error.emit(str(exc))
            self._serial = None
            self.connection_changed.emit(False)

    def disconnect(self):
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._serial = None
        self.connection_changed.emit(False)

    def poll_once(self):
        """Call from a future worker thread; kept synchronous for a clear integration seam."""
        if not self._serial or not self._serial.is_open:
            return
        line = self._serial.readline()
        if not line:
            return
        try:
            self.message_received.emit(parse_message(line.decode("utf-8").strip()))
        except (UnicodeDecodeError, ProtocolError) as exc:
            self.error.emit(str(exc))

    def send(self, payload: dict):
        if self._serial and self._serial.is_open:
            from communication.protocol import encode_message
            self._serial.write(encode_message(payload))
