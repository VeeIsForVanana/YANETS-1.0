from typing import Tuple

import numpy as np # type: ignore

# Tile graphics structured type compatible with Console.tiles_rgb.
graphics_dt = np.dtype(
    [
        ("ch", np.int32),   # Unicode codepoint.
        ("fg", "3B"),   # 3 unsigned bytes, for RGB colors.
        ("bg", "3B"),
    ]
)

# Tile struct used for statically defined tile data.
tile_dt = np.dtype(
    [
        ("walkable", np.bool), # True if this tile can be walked over
        ("transparent", np.bool), # True if this tile doesn't block FOV.
        ("dark", graphics_dt), # Graphics for when this tile is not in FOV
        ("light", graphics_dt), #Graphics for when this tile is in FOV
    ]
)

def new_tile(
        *, # Enforce the use of keywords so that parameter order doesn't matter.
        walkable: int,
        transparent: int,
        dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
        light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
) -> np.array:
    """Helper function for defining individual tile types"""
    return np.array((walkable, transparent, dark, light), dtype=tile_dt)

# SHROUD represents unexplored, unseen tiles
SHROUD = np.array(((ord(" ")), (255, 255, 255), (0, 0, 0)), dtype = graphics_dt)

floor = new_tile(
    walkable = True,
    transparent = True,
    dark = (ord(" "), (255, 255, 255), (184, 94, 130)),
    light = (ord(" "), (255, 255, 255), (255, 169, 198)),
)
wall = new_tile(
    walkable = False,
    transparent = False,
    dark = (ord(" "), (255, 255, 255), (143, 0, 31)),
    light = (ord(" "), (255, 255, 255), (255, 33, 81)),
)
down_stairs = new_tile(
    walkable = True,
    transparent = True,
    dark = (ord(">"), (0, 0, 100), (50, 50, 150)),
    light = (ord(">"), (255, 255, 255), (200, 180, 50)),
)
up_stairs = new_tile(
    walkable = True,
    transparent = True,
    dark = (ord("<"), (0, 0, 100), (50, 50, 150)),
    light = (ord("<"), (255, 255, 255), (200, 180, 50)),
)
surface_floor = new_tile(
    walkable = True,
    transparent = True,
    dark = (ord(" "), (255, 255, 255), (3, 33, 0)),
    light = (ord(" "), (255, 255, 255), (9, 94, 0))
)