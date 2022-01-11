from __future__ import annotations

import random
from typing import List, Optional, Tuple, TYPE_CHECKING

import numpy as np  # type: ignore
import tcod

from base_component import BaseComponent
from enum import Enum, auto

class Affiliations(Enum):
    player = auto()
    einsof = auto()
    nature = auto()
    generic_hostile = auto()