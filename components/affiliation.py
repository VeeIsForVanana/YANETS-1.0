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



default_hostilities = {
    Affiliations.einsof : {i if i != Affiliations.einsof else None for i in Affiliations},
    Affiliations.generic_hostile : {i if i != Affiliations.generic_hostile else None for i in Affiliations},
    Affiliations.tier1_consumer : {Affiliations.einsof, Affiliations.plants, Affiliations.generic_hostile},
    Affiliations.tier2_consumer : {Affiliations.einsof, Affiliations.tier1_consumer, Affiliations.generic_hostile},
    Affiliations.tier3_consumer : {Affiliations.einsof, Affiliations.tier2_consumer, Affiliations.generic_hostile},
}
