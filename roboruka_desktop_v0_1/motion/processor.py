from motion.coordinate_mapper import CoordinateMapper
from motion.filters import ExponentialSmoother
from motion.calibration import Calibration


class MotionProcessor:
    """Hardware-neutral processing pipeline for future ESP32 measurements."""

    def __init__(self):
        self.calibration = Calibration()
        self.smooth_x = ExponentialSmoother()
        self.smooth_y = ExponentialSmoother()

    def process(self, x: float, y: float, width: float, height: float):
        x, y = self.calibration.apply(x, y)
        x = self.smooth_x.update(x)
        y = self.smooth_y.update(y)
        return CoordinateMapper.to_canvas(x, y, width, height)
