class ExponentialSmoother:
    def __init__(self, alpha: float = 0.35):
        self.alpha = max(0.0, min(1.0, alpha))
        self._value = None

    def reset(self):
        self._value = None

    def update(self, value: float) -> float:
        if self._value is None:
            self._value = value
        else:
            self._value = self.alpha * value + (1.0 - self.alpha) * self._value
        return self._value
