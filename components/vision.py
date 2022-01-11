from __future__ import annotations

from typing import List, Optional, Tuple, TYPE_CHECKING

from components.base_component import BaseComponent
from tcod.map import compute_fov
import tcod
import numpy as np  # type: ignore

from entity import Entity


class Vision(BaseComponent):
    def __init__(self, entity):
        self.vision_grid: np.array = []
        self.entity = entity

    def visible_entities(self) -> List[Entity]:
        """
        Returns a list of all visible entities from the gamemap
        :return: List of visible entities
        """
        return [entity if self.vision_grid[entity.x, entity.y] else None for entity in self.gamemap.entities]

    def update_fov(self):
        raise NotImplementedError("You are using the generic vision class")

class PlayerVision(Vision):
    def update_fov(self):
        self.vision_grid = compute_fov(
            self.engine.game_map.tiles["transparent"],
            (self.parent.x, self.parent.y),
            radius = 9,
            algorithm=tcod.FOV_SYMMETRIC_SHADOWCAST
        )


class ShortVision(Vision):
    def update_fov(self):
        self.vision_grid = compute_fov(
            self.engine.game_map.tiles["transparent"],
            (self.parent.x, self.parent.y),
            radius=5,
            algorithm=tcod.FOV_BASIC
        )

