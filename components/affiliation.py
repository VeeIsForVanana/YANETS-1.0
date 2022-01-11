from __future__ import annotations

import numpy as np  # type: ignore

from enum import Enum, auto

class Affiliations(Enum):
    player = auto()
    einsof = auto()
    nature = auto()
    generic_hostile = auto()