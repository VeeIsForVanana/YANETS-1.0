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
        visible_entities: List[Entity] = []
        for i in self.gamemap.entities:
            try:
                if self.vision_grid[i.x][i.y] and i is not self.parent:
                    visible_entities.append(i)
            except IndexError:
                print(f"Index Error for {i}, at {i.x}, {i.y}")
        return visible_entities

    def visible_actors(self) -> List[Entity]:
        from actor import Actor
        """
        Returns a list of all visible actors from the gamemap
        :return:
        """
        visible_actors: List[Actor] = []
        for i in self.gamemap.actors:
            try:
                if self.vision_grid[i.x][i.y] and i is not self.parent:
                    visible_actors.append(i)
            except IndexError:
                print(f"Index Error for {i}, at {i.x}, {i.y}")
        return visible_actors

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
        return self.vision_grid


class ShortVision(Vision):
    def update_fov(self):
        self.vision_grid = compute_fov(
            self.engine.game_map.tiles["transparent"],
            (self.parent.x, self.parent.y),
            radius=5,
            algorithm=tcod.FOV_BASIC
        )

