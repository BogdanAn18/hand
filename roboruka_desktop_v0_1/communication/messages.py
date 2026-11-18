from dataclasses import dataclass
from typing import Optional


@dataclass
class DeviceMessage:
    version: int
    type: str
    seq: Optional[int] = None
    timestamp_ms: Optional[int] = None
    position: Optional[dict] = None
    orientation: Optional[dict] = None
    buttons: Optional[dict] = None
