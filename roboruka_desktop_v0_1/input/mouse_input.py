from input.provider import InputProvider, PointerState


class MouseInput(InputProvider):
    """Marker provider: the canvas receives native Qt mouse events in mouse mode."""

    def start(self):
        self.connection_changed.emit(True, "Mouse input ready")

    def stop(self):
        self.connection_changed.emit(False, "Mouse input stopped")
