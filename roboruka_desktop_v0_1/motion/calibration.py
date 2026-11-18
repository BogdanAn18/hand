from dataclasses import dataclass


@dataclass
class Calibration:
    """Placeholder for future multi-point calibration parameters."""
    x_scale: float = 1.0
    x_offset: float = 0.0
    y_scale: float = 1.0
    y_offset: float = 0.0

    def apply(self, x: float, y: float):
        return (x * self.x_scale + self.x_offset,
                y * self.y_scale + self.y_offset)
