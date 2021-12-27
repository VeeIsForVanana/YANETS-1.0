from __future__ import annotations

import random
from typing import Tuple, Iterator, List

import tcod

from game_map import GameMap


def adjacency_iterator(
        x_iteration = (-1, 0, 1), y_iteration = (-1, 0, 1), include_diagonals: bool = False
) -> List[Tuple[int, int]]:
    output = []
    for y in y_iteration:
        for x in x_iteration:
            if not (abs(x) == abs(y) and (not include_diagonals or abs(x) == 0)):
                output.append((x, y))
    return output


# Helper functions for generating paths

def tunnel_between(
        start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """Return an L-shaped tunnel between these two points."""
    x1, y1 = start
    x2, y2 = end
    corner_x, corner_y = x1, y2
    if random.random() < 0.5: # 50% chance.
        # Move horizontally, then vertically.
        corner_x, corner_y = x2, y1

    #Generate the coordinates for this tunnel
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y

def diagonal_between(
        start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """Returns a winding direct tunnel between the two points"""
    x1, y1 = start
    x2, y2 = end
    new_x, new_y = start
    while (x1, y1) != end:
        while not (abs(new_x - x2) < abs(x1 - x2) or abs(new_y - y2) < abs(y2 - y1)):
            neighbors = [(x1 + dx, y1 + dy) for dx, dy in adjacency_iterator()]
            new_x, new_y = random.choice(neighbors)
        x1 = new_x
        y1 = new_y
        yield x1, y1