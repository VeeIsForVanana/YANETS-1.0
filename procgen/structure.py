import random
from typing import List, Optional, Dict

import numpy as np

import game_map
import tile_types

import procgen.helpers as help
from procgen.rectangular_room import RectangularRoom

import tcod

class Structure:
    """General class for multi-room objects"""
    def __init__(self, parent: game_map.GameMap, struct_x: int, struct_y: int, struct_width: int, struct_height: int, fill_tile = tile_types.wall):
        self.parent = parent
        self.rooms: Dict[tcod.bsp.BSP: RectangularRoom] = {}
        self.x = struct_x
        self.y = struct_y
        self.width = struct_width
        self.height = struct_height
        self.tiles = np.full((self.width, self.height), fill_value = fill_tile, order = "F")

    def make_binary_partition(self, percent_floor: float, percent_variation: float, partition_depth: int,
                              partition_runs: int = 1, deeper_partitions: bool = False) -> None:
        self.blueprint = tcod.bsp.BSP(0, 0, self.width, self.height)
        self.blueprint.split_recursive(partition_depth, 5, 5, 1.5, 1.5)

        # Generate rooms and connections
        for node in self.blueprint.post_order():
            if node.children and self.rooms.get(node.children[0], None) and self.rooms.get(node.children[1], None):
                node1, node2 = node.children
                self.rooms[node] = random.choice([self.rooms[node1], self.rooms[node2]])
                for x, y in help.tunnel_between(self.rooms[node1].center, self.rooms[node2].center):
                    self.tiles[x, y] = tile_types.floor
            if not node.children:
                percent_room = max(percent_floor + percent_variation,
                                   min(random.random(), percent_floor - percent_variation))
                self.rooms[node] = RectangularRoom(node.x, node.y,
                                            int(percent_room * node.width), int(percent_room * node.height))
                self.tiles[self.rooms[node].inner] = tile_types.floor

    def generate_outside_connection(self):
        invalid_door = True
        door = (0, 0)
        while invalid_door:
            door = random.choice([(0, random.randint(0, self.height)), (random.randint(0, self.width), 0),
                                  (self.width - 1, random.randint(0, self.height)),
                                  (random.randint(0, self.width), self.height - 1)])
            try:
                floor_checker = [self.tiles[door[0] + dx, door[1] + dy] for dx, dy in help.adjacency_iterator()]
            except IndexError:
                continue
            if tile_types.floor in floor_checker:
                invalid_door = False
        self.tiles[door] = tile_types.floor

    def generate_downstairs(self):
        if isinstance(self.blueprint, tcod.bsp.BSP):
            node = list(self.blueprint.post_order())[0]
            self.parent.downstairs_location = (self.rooms[node].center[0] + self.x, self.rooms[node].center[1] + self.y)
            self.parent.update()
