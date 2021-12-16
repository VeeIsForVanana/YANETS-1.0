from __future__ import annotations

import lzma
import pickle
from typing import TYPE_CHECKING

from tcod.console import Console
from tcod.map import compute_fov

import exceptions
import render_standards
from message_log import MessageLog
import render_functions

if TYPE_CHECKING:
    from entity import Actor
    from game_map import GameMap, GameWorld

class Engine:
    game_map: GameMap
    game_world: GameWorld

    def __init__(self, player: Actor):
        self.message_log = MessageLog()
        self.cursor_location = (0, 0)
        self.player = player
        self.turn_counter = 0

    turn_counter: int

    def handle_entity_turns(self) -> None:
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai:
                try:
                    entity.ai.perform()
                except exceptions.Impossible:
                    pass # Ignore impossible action exceptions from AI.

    def update_fov(self) -> None:
        """Recompute the visible area based on the player's point of view."""
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x, self.player.y),
            radius = 8,
        )
        # If a tile is visible, it should be added to "explored"

        self.game_map.explored |= self.game_map.visible

    def render(self, console: Console) -> None:
        self.game_map.render(console)

        self.message_log.render(
            console = console,
            x = render_standards.message_log_x,
            y = render_standards.message_log_y,
            width = render_standards.message_log_width,
            height = render_standards.message_log_height,
        )

        render_functions.render_dungeon_level(
            console = console,
            dungeon_level = self.game_world.current_floor,
            location = (1, 1)
        )

        render_functions.render_inventory_screen(
            console = console,
            engine = self,
            x = render_standards.inventory_x,
            y = render_standards.inventory_y,
            width = render_standards.inventory_width,
            height = render_standards.inventory_height,
        )

        render_functions.render_character_screen(
            console = console,
            engine = self,
            x = render_standards.character_screen_x,
            y = render_standards.character_screen_y,
            width = render_standards.character_screen_width,
            height = render_standards.character_screen_height
        )

    def save_as(self, filename: str = "savegame.sav") -> None:
        """Save this Engine instance as a compressed file."""
        save_data = lzma.compress(pickle.dumps(self))
        with open(filename, "wb") as f:
            f.write(save_data)