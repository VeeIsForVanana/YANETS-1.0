from __future__ import annotations

import copy
import math
from typing import Optional, Tuple, TypeVar, TYPE_CHECKING, Union

from render_order import RenderOrder

if TYPE_CHECKING:
    from components.consumable import Consumable
    from components.equippable import Equippable
    from components.inventory import Inventory
    from game_map import GameMap

T = TypeVar("T", bound = "Entity")

class Entity:
    """
    A generic object to represent players, enemies, items, etc.
    """

    parent: Union[GameMap, Inventory]

    def __init__(
            self,
            parent: Optional[GameMap] = None,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            color: Tuple[int, int, int] = (256, 256, 256),
            name: str = "<Unnamed>",
            blocks_movement: bool = False,
            render_order: RenderOrder = RenderOrder.CORPSE,
    ):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks_movement = blocks_movement
        self.render_order = render_order
        if parent:
            # If parent isn't provided now then it will be set later.
            self.parent = parent
            parent.entities.add(self)
        self.entity_id = None

    @property
    def gamemap(self) -> GameMap:
        return self.parent.gamemap

    def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
        """Spawns a copy of this instance at the given location"""
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.parent = gamemap
        gamemap.entities.add(clone)
        gamemap.new_entity_id(self)

        return clone

    def place(self, x: int, y: int, gamemap: Optional[GameMap] = None) -> None:
        """Places this entity at a new location. Handles moving across GameMaps. Does not generate new entity."""
        self.x = x
        self.y = y
        if gamemap:
            if hasattr(self, "parent"):    # Possibly uninitialized.
                if self.parent is self.gamemap:
                    self.gamemap.entities.remove(self)
                    self.gamemap.remove_entity_id(self.entity_id)
            self.parent = gamemap
            gamemap.entities.add(self)
            gamemap.new_entity_id(self)

    def distance(self, x: int, y: int) -> float:
        """
        Return the distance between the current entity and the given (x, y) coordinate.
        """
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def move(self, dx: int, dy: int) -> None:
        # Move the entity by a given amount
        self.x += dx
        self.y += dy


class Item(Entity):
    def __init__(
            self,
            *,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            color: Tuple[int, int, int] = (255, 255, 255),
            name: str = "<Unnamed>",
            consumable: Optional[Consumable] = None,
            equippable: Optional[Equippable] = None,
    ):
        super().__init__(
            x = x,
            y = y,
            char = char,
            color = color,
            name = name,
            blocks_movement = False,
            render_order = RenderOrder.ITEM
        )

        self.consumable = consumable

        if self.consumable:
            self.consumable.parent = self

        self.equippable = equippable

        if self.equippable:
            self.equippable.parent = self