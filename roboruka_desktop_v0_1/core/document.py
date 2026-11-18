from dataclasses import dataclass
from typing import List, Optional
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
from core.stroke import DrawObject


class Document:
    """Simple command-history document. Objects are stored in canvas pixel coordinates."""

    def __init__(self):
        self.objects: List[DrawObject] = []
        self._undo: List[list] = []
        self._redo: List[list] = []

    def _snapshot(self):
        # DrawObject and QPointF are copied to avoid later mutation of history.
        copied = []
        for obj in self.objects:
            copied.append(DrawObject(
                obj.kind,
                [QPointF(p) for p in obj.points],
                QColor(obj.color),
                obj.width,
            ))
        return copied

    def _commit(self):
        self._undo.append(self._snapshot())
        self._redo.clear()

    def add(self, obj: DrawObject):
        self._commit()
        self.objects.append(obj)

    def erase_at(self, point: QPointF, radius: float = 14.0):
        kept = []
        changed = False
        for obj in self.objects:
            if any((p - point).manhattanLength() <= radius for p in obj.points):
                changed = True
            else:
                kept.append(obj)
        if changed:
            self._commit()
            self.objects = kept

    def clear(self):
        if self.objects:
            self._commit()
            self.objects = []

    def undo(self) -> bool:
        if not self._undo:
            return False
        self._redo.append(self._snapshot())
        self.objects = self._undo.pop()
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        self._undo.append(self._snapshot())
        self.objects = self._redo.pop()
        return True

    @property
    def can_undo(self):
        return bool(self._undo)

    @property
    def can_redo(self):
        return bool(self._redo)
