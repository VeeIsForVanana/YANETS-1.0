from components.base_component import BaseComponent

class Attribute():
    """General class for all attributes (numerical stats with maxima and minima attached to entity components)"""
    parent: BaseComponent

    def __init__(self, current: int, max: int = 100000, min: int = 0):
        self._current = current
        self._max = max
        self._min = min

    @property
    def value(self) -> int:
        return self._current

    def new_value(self, new_value: int) -> None:
        self._current = min(self._max, max(self._min, new_value))

    def add_to_value(self, amount: int):
        self.new_value(self._current + amount)

    @property
    def max(self) -> int:
        return self._max

    @max.setter
    def max(self, new_max: int, match_current: bool = False) -> None:
        self._max = max(self.value, new_max)
        if match_current:
            self.new_value(new_max)

    @property
    def min(self) -> int:
        return self._min

    @min.setter
    def min(self, new_min: int) -> None:
        self._min = min(self.value, new_min)


class HealthAttribute(Attribute):

    parent: BaseComponent

    name = "HP"

    def __init__(self, value: int):
        super().__init__(value, value)

class DefenseAttribute(Attribute):

    parent: BaseComponent

    name = "Defense"

class PowerAttribute(Attribute):

    parent: BaseComponent

    name = "Power"
