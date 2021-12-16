from __future__ import annotations

from engine import Engine
from tcod import Console
from entity import Actor, Entity
import render_standards
import render_functions

import lzma, pickle

class DebugEngine(Engine):
    """
    Special handler for debug mode allowing the player to see all tiles and place any and all objects.
    Essentially, godmode.
    """
    def __init__(self, player: Entity):
        super().__init__(player)

    def update_fov(self) -> None:
        """Updates fov by making no tiles visible"""

    def save_as(self, filename: str = "savegame.sav") -> None:
        """Overrides super().save_as(), forces saving to 'debug.sav'"""
        super().save_as("debug.sav")

    def render(self, console: Console) -> None:

        self.debug_info: dict = {
            "Turn Count": self.turn_counter,
            "Player Position": (self.player.x, self.player.y),
            "Entities on Game Map": len(self.game_map.entities),
            "Actors on Game Map": len(list(self.game_map.actors)),
            "Cursor Location": self.cursor_location
        }

        self.game_map.render(console, debug_mode = True)

        self.message_log.render(
            console=console,
            x=render_standards.message_log_x,
            y=render_standards.message_log_y,
            width=render_standards.message_log_width,
            height=render_standards.message_log_height,
        )

        render_functions.render_dungeon_level(
            console=console,
            dungeon_level=self.game_world.current_floor,
            location=(1, 1)
        )

        render_functions.render_debug_info_readout(
            console=console,
            x=render_standards.map_width,
            y = 0,
            width = render_standards.inventory_width,
            height = render_standards.screen_height,
            engine = self,
        )

    def save_as(self, filename: str = "savegame.sav") -> None:
        """Save this Engine instance as a compressed file."""
        save_data = lzma.compress(pickle.dumps(self))
        with open(filename, "wb") as f:
            f.write(save_data)