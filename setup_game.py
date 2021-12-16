"""Handle the loading and initialization of game sessions."""
from __future__ import annotations

import copy
import lzma
import pickle
import traceback
from typing import Optional, List

import tcod
import color
import render_standards
from engine import Engine
from debug_engine import DebugEngine
import entity_factories
from game_map import GameWorld
import input_handlers
import render_functions

# Load the background image and remove the alpha channel.
background_image = tcod.image.load("menu_background.png")[:, :, :3]


def new_game(debug: bool = False) -> Engine:
    """Return a brand new game session as an Engine instance."""
    map_width = render_standards.map_width
    map_height = render_standards.map_height

    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    tileset = tcod.tileset.load_tilesheet(
        "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    player = copy.deepcopy(entity_factories.player)

    engine = (Engine(player=player) if not debug else
              DebugEngine(player=entity_factories.debug_player))

    engine.game_world = GameWorld(
        engine=engine,
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        map_width=map_width,
        map_height=map_height,
    )

    engine.game_world.generate_floor()
    engine.update_fov()

    engine.message_log.add_message(
        "Hello and welcome, adventurer, to yet another dungeon!", color.welcome_text
    )

    return engine

def load_game(filename: str) -> Engine:
    """Load an Engine instance from a file."""
    with open(filename, "rb") as f:
        engine = pickle.loads(lzma.decompress(f.read()))
    assert isinstance(engine, Engine)
    return engine

class MainMenu(input_handlers.BaseEventHandler):
    """Handle the main menu rendering and input."""

    def __init__(self, console: tcod.Console):
        """Initializes the MainMenu with a console and cursor position"""
        self.console = console
        self.selection = list(enumerate(["New Game", "Continue Game", "Quit", "DEBUG MODE", "LOAD DEBUG"]))
        self.present_selection = 0

    def on_render(self) -> None:
        """Render the main menu on a background image."""
        self.console.draw_semigraphics(background_image, 0, 0)

        self.console.print(
            self.console.width // 2,
            self.console.height // 2 - 4,
            "TOMBS OF THE ANCIENT KINGS",
            fg = color.menu_title,
            alignment = tcod.CENTER
        )
        self.console.print(
            self.console.width // 2,
            self.console.height // 2 - 2,
            "By VEE"
        )

        menu_width = 24
        for i, text in self.selection:
            self.console.print(
                self.console.width // 2,
                self.console.height // 2 - 2 + i,
                text.ljust(menu_width),
                fg = (color.menu_text if i != self.present_selection else color.selection),
                bg = (color.white if i == self.present_selection else None),
                alignment = tcod.CENTER,
                bg_blend = tcod.BKGND_ALPHA(64),
            )

    def ev_keydown(
            self, event: tcod.event.KeyDown
    ) -> Optional[input_handlers.BaseEventHandler]:
        if event.sym == tcod.event.K_ESCAPE:
            raise SystemExit()
        elif event.sym == tcod.event.K_n:
            return input_handlers.MainGameEventHandler(new_game())
        elif event.sym == tcod.event.K_UP:
            self.present_selection = max(self.present_selection - 1, 0)
        elif event.sym == tcod.event.K_DOWN:
            self.present_selection = min(self.present_selection + 1, len(self.selection) - 1)
        elif event.sym == tcod.event.K_RETURN or event.sym == tcod.event.K_KP_ENTER:
            if self.present_selection == 0:
                return input_handlers.MainGameEventHandler(new_game())
            elif self.present_selection == 1:
                try:
                    return input_handlers.MainGameEventHandler(load_game("savegame.sav"))
                except FileNotFoundError:
                    return input_handlers.PopupMessage(self, "No saved game to load.")
                except Exception as exc:
                    traceback.print_exc()   # Print to stderr.
                    return input_handlers.PopupMessage(self, f"Failed to load save:\n{exc}")
            elif self.present_selection == 2:
                raise SystemExit()
            elif self.present_selection == 3:
                return input_handlers.DebugModeEventHandler(new_game(debug=True))
            elif self.present_selection == 4:
                try:
                    return input_handlers.DebugModeEventHandler(load_game("debug.sav"))
                except FileNotFoundError:
                    return input_handlers.PopupMessage(self, "No saved game to load.")
                except Exception as exc:
                    traceback.print_exc()   # Print to stderr.
                    return input_handlers.PopupMessage(self, f"Failed to load save:\n{exc}")