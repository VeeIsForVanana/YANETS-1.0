from __future__ import annotations

import random
from typing import Dict, Tuple, List, TYPE_CHECKING

import entity_factories
import item_factories
from game_map import GameMap, GameWorld
import tile_types
import render_standards as rs

from procgen.helpers import tunnel_between, diagonal_between
from procgen.rectangular_room import RectangularRoom
from procgen.spawn_chances import max_items_by_floor, max_monsters_by_floor, item_chances, enemy_chances
from procgen.structure import Structure

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


def get_max_value_for_floor(
        weighted_chances_by_floor: List[Tuple[int, int]], floor: int
) -> int:
    current_value = 0

    for floor_minimum, value in weighted_chances_by_floor:
        if floor_minimum > floor:
            break
        else:
            current_value = value

    return current_value

def get_entities_at_random(
        weighted_chances_by_floor: Dict[int, List[Tuple[Entity, int]]],
        number_of_entities: int,
        floor: int,
) -> List[Entity]:
    entity_weighted_chances = {}

    for key, values in weighted_chances_by_floor.items():
        if key > floor:
            break
        else:
            for value in values:
                entity = value[0]
                weighted_chance = value[1]

                entity_weighted_chances[entity] = weighted_chance

    entities = list(entity_weighted_chances.keys())
    entity_weighted_chance_value = list(entity_weighted_chances.values())

    chosen_entities = random.choices(
        entities, weights = entity_weighted_chance_value, k = number_of_entities
    )

    return chosen_entities


def place_entities(
        room: RectangularRoom, dungeon: GameMap, floor_number: int,
) -> None:
    number_of_monsters = random.randint(
        0, get_max_value_for_floor(max_monsters_by_floor, floor_number)
    )
    number_of_items = random.randint(
        0, get_max_value_for_floor(max_items_by_floor, floor_number)
    )

    monsters: List[Entity] = get_entities_at_random(
        enemy_chances, number_of_monsters, floor_number
    )
    items: List[Entity] = get_entities_at_random(
        item_chances, number_of_items, floor_number
    )

    for entity in monsters + items:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            entity.spawn(dungeon, x, y)

def generate_dungeon(parent_world: GameWorld, max_rooms: int, room_min_size: int, room_max_size: int, map_width: int,
                     map_height: int, map_tiling: int, engine: Engine) -> GameMap:
    """
    Generate a new dungeon map.
    """
    map_width *= map_tiling
    map_height *= map_tiling
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, map_tiling, entities = [player])
    dungeon.parent = parent_world
    rooms: List[RectangularRoom] = []

    center_of_last_room = (0, 0)

    for r in range(max_rooms):
        valid_room = False
        while not valid_room:
            room_width = random.randint(room_min_size, room_max_size)
            room_height = random.randint(room_min_size, room_max_size)

            x = random.randint(0, dungeon.width - room_width - 1)
            y = random.randint(0, dungeon.height - room_height - 1)

            # "RectangularRoom" class makes rectangles easier to work with
            new_room = RectangularRoom(x, y, room_width, room_height)

            # Run through the other rooms and see if they intersect with this room.
            # Ensure new room center does not sit on the tile edge
            if not (any(new_room.intersects(other_room) for other_room in rooms)
                    or new_room.center[0] in (0, rs.map_width)
                    or new_room.center[1] in (0, rs.map_height)):
                valid_room = True
            # If there are no intersections then the room is valid.

        #Dig out this room's inner area.

        dungeon.tiles[new_room.inner] = tile_types.floor

        if len(rooms) == 0:
            # The first room, where the player starts.
            player.place(new_room.center[0], new_room.center[1], dungeon)
            if parent_world.current_floor == 1:
                item_factories.dagger.spawn(dungeon, new_room.center[0] + 1, new_room.center[1])
                item_factories.leather_armor.spawn(dungeon, new_room.center[0] - 1, new_room.center[1])
        if len(rooms) >= 1: # All rooms after the first.
            # Dig out a tunnel between this room and the next one.
            for x, y in diagonal_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor

        if len(rooms) == max_rooms - 2: # Final room
            center_of_last_room = new_room.center
            dungeon.tiles[center_of_last_room] = tile_types.down_stairs
            dungeon.downstairs_location = center_of_last_room

        place_entities(new_room, dungeon, engine.game_world.current_floor)

        #Finally, append the new room to the list.
        rooms.append(new_room)

    return dungeon

def generate_surface(parent_world: GameWorld, entrance_size: int, map_width: int,
                     map_height: int, map_tiling: int, engine: Engine) -> GameMap:
    """
    Generates surface layer and entrance
    """
    map_width *= map_tiling
    map_height *= map_tiling
    player = engine.player
    surface = GameMap(engine, map_width, map_height, map_tiling, entities=[player], fill_tile=tile_types.surface_floor)
    surface.parent = parent_world

    start_x = random.choice([10, map_width - 10])
    start_y = random.choice([10, map_height - 10])

    player.place(start_x, start_y, surface)

    generate_structure(surface, random.randint(55, map_width - 55), random.randint(55, map_height - 55),
                       random.randint(30, 50), random.randint(30, 50))

    return surface

def generate_structure(game_map: GameMap, corner_x: int, corner_y: int, width: int, height: int) -> None:
    """
    Generates structures of continuous walls
    """
    structure = Structure(game_map, corner_x, corner_y, width, height)
    structure.make_binary_partition(0.8, 0.2, 4, 1)
    structure.generate_outside_connection()
    game_map.tiles[corner_x: corner_x + width, corner_y: corner_y + height] = structure.tiles[0: width, 0: height]
    structure.generate_downstairs()

    return None
