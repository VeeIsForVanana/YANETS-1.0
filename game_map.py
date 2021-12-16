from __future__ import annotations

from typing import Optional, Iterator, Iterable, TYPE_CHECKING, Generator, Tuple

import numpy as np  # type: ignore
from tcod.console import Console

import exceptions
from entity import Actor, Item
import tile_types

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


class GameMap:
    def __init__(
            self, engine: Engine, width: int, height: int, entities: Iterable[Entity] = ()
    ):
        self.engine = engine
        self.width, self.height = width, height
        self.entities = set(entities)
        self.tiles = np.full((width, height), fill_value = tile_types.wall, order = "F")

        self.visible = np.full(
            (width, height), fill_value = False, order = "F"
        ) # Tiles the player can currently see
        self.explored = np.full(
            (width, height), fill_value = False, order = "F"
        )   # Tiles the player has seen before
        self.tile_exists = np.full(
            (width, height), fill_value = True, order = "F"
        )

        self.entity_ids: dict[int: Entity] = {}

        self.downstairs_location = (0, 0)

    @property
    def gamemap(self) -> GameMap:
        return self

    @property
    def next_open_id(self) -> int:
        for i in range(10000):
            if self.entity_ids.get(i, None) is None:
                return i
        raise exceptions.Impossible("Cannot assign new entity ID")

    @property
    def actors(self) -> Iterator[Actor]:
        """Iterate over this map's living actors"""
        yield from (
            entity
            for entity in self.entities
            if isinstance(entity, Actor) and entity.is_alive
        )

    @property
    def items(self) -> Iterator[Item]:
        yield from(
            entity
            for entity in self.entities
            if isinstance(entity, Item)
        )

    def new_entity_id(self, entity: Entity) -> bool:
        """Assigns entity IDs and dictionary space to an entity and return True, if Impossible return False"""
        try:
            entity.entity_id = self.next_open_id
        except exceptions.Impossible:
            return False
        self.entity_ids[entity.entity_id] = entity
        return True

    def remove_entity_id(self, entity_id: int) -> None:
        """Removes entity from associated entity ID from dictionary."""
        self.entity_ids[entity_id] = None

    def get_blocking_entity_at_location(
            self, location_x: int, location_y: int
    ) -> Optional[Entity]:
        for entity in self.entities:
            if (
                    entity.blocks_movement
                    and entity.x == location_x
                    and entity.y == location_y
            ):
                return entity

        return None

    def get_actor_at_location(self, x: int, y: int) -> Optional[Actor]:
        for actor in self.actors:
            if actor.x == x and actor.y == y:
                return actor

        return None

    def in_bounds(self, x: int, y: int) -> bool:
        """Return True if x and y are inside of the bounds of this map"""
        return 0 <= x < self.width and 0 <= y < self.height

    def render(self, console: Console, debug_mode: bool = False) -> None:
        """
        Renders the map.

        If a tile is in the "visible" array, then draw it with the 'light' colors.
        If it isn't, but it's in the "explored array", then draw it with the 'dark' colors.
        Otherwise, the default is "SHROUD".
        """

        console.rgb[0 : self.width, 0 : self.height] = np.select(
            condlist = ([self.visible, self.explored] if not debug_mode else
                        [self.tile_exists]),
            choicelist = ([self.tiles["light"], self.tiles["dark"]] if not debug_mode else
                          [self.tiles["light"]]),
            default = tile_types.SHROUD,
        )

        entities_sorted_for_rendering = sorted(
            self.entities, key = lambda x: x.render_order.value
        )

        for entity in entities_sorted_for_rendering:
            if self.visible[entity.x, entity.y] or debug_mode:
                console.print(
                    entity.x, entity.y, entity.char, fg = entity.color
                )

class GameWorld:
    """
    Holds the settings for the GameMap, and generates new maps when moving down the stairs.
    """
    def __init__(
            self,
            engine: Engine,
            map_width: int,
            map_height: int,
            max_rooms: int,
            room_min_size: int,
            room_max_size: int,
            current_floor: int = 0
    ):
        self.engine = engine

        self.map_width = map_width
        self.map_height = map_height

        self.max_rooms = max_rooms

        self.room_min_size = room_min_size
        self.room_max_size = room_max_size

        self.current_floor = current_floor

    def generate_floor(self) -> None:
        from procgen import generate_dungeon

        self.current_floor += 1

        self.engine.game_map = generate_dungeon(
            max_rooms=self.max_rooms,
            room_min_size=self.room_min_size,
            room_max_size=self.room_max_size,
            map_width=self.map_width,
            map_height=self.map_height,
            engine=self.engine
        )