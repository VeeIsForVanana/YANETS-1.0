from __future__ import annotations

from typing import Tuple, TYPE_CHECKING, Iterable

import color
import textwrap

import render_standards as r_std

if TYPE_CHECKING:
    from tcod import Console
    from engine import Engine
    from debug_engine import DebugEngine
    from game_map import GameMap

def get_names_at_location(x: int, y: int, game_map: GameMap) -> str:
    if not game_map.in_bounds(x, y) or not game_map.visible[x, y]:
        return ""
    names = ", ".join(
        entity.name for entity in game_map.entities if entity.x == x and entity.y == y
    )

    return names.capitalize()

def render_bar(
        console: Console, x: int, y: int, current_value: int, maximum_value: int, total_width: int, name: str = "HP",
) -> None:
    bar_width = int(float(current_value) / maximum_value * total_width)

    console.draw_rect(x = x, y = y + 1, width = total_width, height = 1, ch = 1, bg = color.bar_empty)

    if bar_width > 0 and current_value < maximum_value:
        console.draw_rect(
            x = x, y = y + 1, width = bar_width, height = 1, ch = 1, bg = color.bar_filled
        )

    elif bar_width > 0 and current_value >= maximum_value:
        console.draw_rect(
            x=x, y=y + 1, width=total_width, height=1, ch=1, bg=color.bar_overload
        )

    console.print(
        x = x,
        y = y,
        string = f"{name}: {current_value} / {maximum_value} "
                 f"{'O_O' if current_value > maximum_value else ''}",
        fg = color.bar_text
    )

def render_dungeon_level(
        console: Console, dungeon_level: int, location: Tuple[int, int]
) -> None:
    """
    Render the level the player is currently on, at the given location.
    """
    x, y = location

    console.print(x = x, y = y, string = f"Dungeon level: {dungeon_level}")

def render_names_at_cursor_location(
        console: Console, x: int, y: int, engine: Engine
) -> None:
    mouse_x, mouse_y = engine.cursor_location

    names_at_mouse_location = get_names_at_location(
        x = mouse_x, y = mouse_y, game_map = engine.game_map
    )

    console.print(x = x, y = y, string = names_at_mouse_location)

def render_inventory_screen(
        console: Console, x: int, y: int, width: int, height: int, engine: Engine, in_use: bool = False, title: str = None
) -> None:
    console.draw_frame(
        x = x,
        y = y,
        width = width,
        height = height,
        title = ("access [i]nventory" if title is None else title),
        fg = color.menu_text,
        bg = (color.inactive_window_bg if not in_use else color.black),
    )

    if not in_use:
        inventory_dict = {}
        for instance in engine.player.inventory.items:
            if not engine.player.equipment.item_is_equipped(instance):
                inventory_dict[instance.name] = inventory_dict.get(instance.name, 0) + 1

        for i, instance in enumerate(inventory_dict.keys()):
            text = instance.ljust(r_std.readout_left_width)[:r_std.readout_left_width]
            console.print(
                x = x + r_std.padding_standard,
                y = y + r_std.padding_standard + i,
                string = f"{text}:{str(inventory_dict[instance]).rjust(r_std.data_width)[:r_std.data_width]}",
                fg = color.menu_text,
            )

        console.print(
            x=x + int(width / 2 - len("[d]rop items") / 2),
            y=y + height - 1,
            string="[d]rop items",
            fg=color.inactive_window_bg,
            bg=color.white
        )

def render_character_screen(
        console: Console, x: int, y: int, width: int, height: int, engine: Engine, in_use: bool = False
) -> None:
    console.draw_frame(
        x = x,
        y = y,
        width = width,
        height = (height if not in_use else r_std.screen_height),
        title = "[c]haracter screen",
        fg = color.menu_text,
        bg = (color.inactive_window_bg if not in_use else color.black)
    )
    if not in_use:
        final_spacing: int = 0
        for spacing, attribute in enumerate(engine.player.fighter.attributes):
            render_bar(
                console=console,
                x = x + r_std.padding_standard,
                y = y + r_std.padding_standard + (spacing * 3),
                current_value = attribute.value,
                maximum_value = attribute.max,
                total_width = r_std.character_screen_width - r_std.padding_standard * 2,
                name = attribute.name
            )
            final_spacing = ((spacing + 1) * 3)

        weapon, armor = engine.player.equipment.weapon, engine.player.equipment.armor

        equipment_info_offset = final_spacing
        if weapon or armor:
            console.print(
                x=x + r_std.padding_standard,
                y=(y + r_std.padding_standard) + equipment_info_offset,
                string = "Equipment"
            )

            console.print(
                x=x + r_std.padding_standard + 2,
                y=(y + r_std.padding_standard) + equipment_info_offset + 1,
                string=f"Weapon: {weapon.name if weapon else 'None equipped'}"
            )

            console.print(
                x=x + r_std.padding_standard + 2,
                y=(y + r_std.padding_standard) + equipment_info_offset + 2,
                string=f"Armor: {armor.name if armor else 'None equipped'}"
            )

def render_debug_info_readout(
    console: Console, x: int, y: int, width: int, height: int, engine: DebugEngine, in_use: bool = False,
):

    debug_info = engine.debug_info

    console.draw_frame(
        x = x,
        y = y,
        width = width,
        height = height,
        title = "DEBUG READOUT"
    )

    for index, i in enumerate(debug_info.keys()):
        text: str = i.ljust(r_std.readout_left_width)[:r_std.readout_left_width]
        value: str = str(debug_info.get(i, None))
        console.print(
            x = x + r_std.padding_standard,
            y = y + r_std.padding_standard + index,
            string = f"{text}"
                     f":"
                     f"{value.rjust(r_std.data_width)[:r_std.data_width]}"
        )



def wrap(string: str, width: int) -> Iterable[str]:
    """Return a wrapped text message."""
    for line in string.splitlines():    # Handle newlines in messages.
        yield from textwrap.wrap(
            line, width, expand_tabs = True
        )