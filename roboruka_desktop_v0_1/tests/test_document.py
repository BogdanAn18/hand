from PySide6.QtCore import QPointF
from core.document import Document
from core.stroke import DrawObject
from PySide6.QtGui import QColor


def test_undo_redo():
    doc = Document()
    doc.add(DrawObject("path", [QPointF(1, 2)], QColor("black"), 2))
    assert len(doc.objects) == 1
    assert doc.undo()
    assert len(doc.objects) == 0
    assert doc.redo()
    assert len(doc.objects) == 1
