from __future__ import annotations

import numpy as np  # type: ignore

from enum import Enum, auto

class Affiliations(Enum):
    player = auto()
    einsof = auto()
    neutral = auto()
    plants = auto()             # Plants under the nature faction.
    tier1_consumer = auto()     # Consumers under the nature faction. Eat plants.
    tier2_consumer = auto()     # Consumers under the nature faction. Eat tier 1.
    tier3_consumer = auto()     # Consumers under the nature faction. Eat tier 1 and tier 2.
    generic_hostile = auto()