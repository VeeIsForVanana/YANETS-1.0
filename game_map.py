from __future__ import annotations

from typing import Optional, Iterator, Iterable, TYPE_CHECKING, Generator, Tuple, List

import numpy as np  # type: ignore
from tcod.console import Console

import exceptions
from entity import Actor, Item
import tile_types

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


class GameMap:
    parent: GameWorld

    def __init__(
            self, engine: Engine, width: int, height: int, tiling: int, entities: Iterable[Entity] = (),
            fill_tile = tile_types.wall
    ):
        self.engine = engine
        self.width, self.height, self.tiling = width, height, tiling
        self.tile_width, self.tile_height = self.width // self.tiling, self.height // self.tiling
        self.entities = set(entities)
        self.tiles = np.full((width, height), fill_value = fill_tile, order = "F")

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
        self.upstairs_location = (0, 0)

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

    def update(self):
        """Updates important map locations to stay consistent with their tiles"""
        self.tiles[self.upstairs_location] = tile_types.up_stairs
        self.tiles[self.downstairs_location] = tile_types.down_stairs

    def render(self, console: Console, debug_mode: bool = False) -> None:
        """
        Renders the map.

        If a tile is in the "visible" array, then draw it with the 'light' colors.
        If it isn't, but it's in the "explored array", then draw it with the 'dark' colors.
        Otherwise, the default is "SHROUD".
        """

        self.player_tile = (self.entity_ids[0].x // self.tile_width, self.entity_ids[0].y // self.tile_height)

        console.rgb[0 : self.tile_width, 0 : self.tile_height] = np.select(
            condlist = ([self.visible, self.explored] if not debug_mode else
                        [self.tile_exists]),
            choicelist = ([self.tiles["light"], self.tiles["dark"]] if not debug_mode else
                          [self.tiles["light"]]),
            default = tile_types.SHROUD,
        )[self.player_tile[0] * self.tile_width:
          (self.player_tile[0] + 1) * self.tile_width,
          self.player_tile[1] * self.tile_height:
          (self.player_tile[1] + 1) * self.tile_height]

        entities_sorted_for_rendering = sorted(
            self.entities, key = lambda x: x.render_order.value
        )

        for entity in entities_sorted_for_rendering:
            if (self.visible[entity.x, entity.y] or debug_mode) and \
                    entity.x // self.tile_width in range(self.player_tile[0], self.player_tile[0] + 2) and \
                    entity.y // self.tile_height in range(self.player_tile[1], self.player_tile[1] + 2):
                console.print(
                    entity.x % self.tile_width, entity.y % self.tile_height, entity.char, fg = entity.color
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
            map_tiling: int,
            max_rooms: int,
            room_min_size: int,
            room_max_size: int,
            current_floor: int = 0
    ):
        self.engine = engine

        self.map_width = map_width
        self.map_height = map_height
        self.map_tiling = map_tiling

        self.max_rooms = max_rooms

        self.room_min_size = room_min_size
        self.room_max_size = room_max_size

        self.current_floor = current_floor

        self.floors: List[GameMap] = []

    def generate_floor(self) -> None:
        from procgen import generate_dungeon, generate_surface

        if self.current_floor > 0:
            self.engine.game_map = generate_dungeon(
                self,
                max_rooms=self.max_rooms,
                room_min_size=self.room_min_size,
                room_max_size=self.room_max_size,
                map_width=self.map_width,
                map_height=self.map_height,
                map_tiling=self.map_tiling,
                engine=self.engine)

        else:

            self.engine.game_map = generate_surface(
                self,
                map_width=self.map_width,
                map_height=self.map_height,
                map_tiling=self.map_tiling,
                engine=self.engine,
                entrance_size=20
            )

        self.floors.append(self.engine.game_map)

    def load_floor(self, going_down: bool) -> None:
        self.engine.game_map = self.floors[self.current_floor]
        if going_down:
            new_position = self.engine.game_map.upstairs_location
        else:
            new_position = self.engine.game_map.downstairs_location
        self.engine.player.place(new_position[0], new_position[1], self.engine.game_map)