from dataclasses import dataclass, field
from typing import List
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor


@dataclass
class DrawObject:
    kind: str
    points: List[QPointF] = field(default_factory=list)
    color: QColor = field(default_factory=lambda: QColor("#202124"))
    width: float = 3.0
