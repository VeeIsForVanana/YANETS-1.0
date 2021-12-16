from __future__ import annotations

import os

from typing import Callable, Tuple, Optional, TYPE_CHECKING, Union, Iterable

import tcod.event

import actions
import render_functions
from actions import (
    Action,
    BumpAction,
    PickupAction,
    WaitAction,
    DropItem,
    MovementAction
)
import color
import exceptions
import render_standards

if TYPE_CHECKING:
    from engine import Engine
    from entity import Item

MOVE_KEYS = {
    # Arrow keys.
    tcod.event.K_UP: (0, -1),
    tcod.event.K_DOWN: (0, 1),
    tcod.event.K_LEFT: (-1, 0),
    tcod.event.K_RIGHT: (1, 0),
    tcod.event.K_HOME: (-1, -1),
    tcod.event.K_END: (-1, 1),
    tcod.event.K_PAGEUP: (1, -1),
    tcod.event.K_PAGEDOWN: (1, 1),
    # Numpad keys.
    tcod.event.K_KP_1: (-1, 1),
    tcod.event.K_KP_2: (0, 1),
    tcod.event.K_KP_3: (1, 1),
    tcod.event.K_KP_4: (-1, 0),
    tcod.event.K_KP_6: (1, 0),
    tcod.event.K_KP_7: (-1, -1),
    tcod.event.K_KP_8: (0, -1),
    tcod.event.K_KP_9: (1, -1),
    # Vi keys
    tcod.event.K_h: (-1, 0),
    tcod.event.K_j: (0, 1),
    tcod.event.K_k: (0, -1),
    tcod.event.K_l: (1, 0),
    tcod.event.K_y: (-1, -1),
    tcod.event.K_u: (1, -1),
    tcod.event.K_b: (-1, 1),
    tcod.event.K_n: (1, 1),
}

WAIT_KEYS = {
    tcod.event.K_PERIOD,
    tcod.event.K_KP_5,
    tcod.event.K_CLEAR
}

CONFIRM_KEYS = {
    tcod.event.K_RETURN,
    tcod.event.K_KP_ENTER
}

CURSOR_Y_KEYS = {
    tcod.event.K_UP: -1,
    tcod.event.K_DOWN: 1,
    tcod.event.K_PAGEUP: -10,
    tcod.event.K_PAGEDOWN: 10
}

ActionOrHandler = Union[Action, "BaseEventHandler"]
"""
An event handler return value which can trigger an action or switch active handlers

If a handler is returned then it will become the active handler for future events.
If an action is returned it will be attempted and if it's valid then
MainGameEventHandler will become the active handler.
"""


class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle an event and return the next active event handler."""
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        assert not isinstance(state, Action), f"{self!r} can not handle actions."
        return self

    def on_render(self, console: tcod.Console) -> None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> Optional[ActionOrHandler]:
        raise SystemExit()


class PopupMessage(BaseEventHandler):
    """Display a popup text window."""

    def __init__(self, parent_handler: BaseEventHandler, text: str):
        self.parent = parent_handler
        self.text = text

    def on_render(self, console: tcod.Console) -> None:
        """Render the parent and dim the result, then print the message on top."""
        try:
            self.parent.on_render(console)
        except TypeError:
            self.parent.on_render()
        console.tiles_rgb["fg"] //= 8
        console.tiles_rgb["bg"] //= 8

        console.print(
            console.width // 2,
            console.height // 2,
            self.text,
            fg = color.white,
            bg = color.black,
            alignment = tcod.CENTER
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        """Any key returns to the parent handler."""
        return self.parent


class EventHandler(BaseEventHandler):
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle events for input handlers with an engine."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if self.handle_action(action_or_state):
            self.engine.turn_counter += 1
            # A valid action was performed.
            if not self.engine.player.is_alive:
                # THe player was killed sometime during or after the action.
                return GameOverEventHandler(self.engine)
            elif self.engine.player.level.requires_level_up:
                return LevelUpEventHandler(self.engine)
            return MainGameEventHandler(self.engine)   # Return to the main handler.
        return self

    def handle_action(self, action: Optional[ActionOrHandler]) -> bool:
        """
        Handle actions returned from event methods.

        Returns True if the action will advance a turn
        """
        if action is None:
            return False

        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return False    # Skip enemy turn on exceptions

        self.engine.handle_entity_turns()

        self.engine.update_fov()

        return True

    def on_render(self, console: tcod.Console) -> None:
        self.engine.render(console)

    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        return None


class MainGameEventHandler(EventHandler):

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        action: Optional[ActionOrHandler] = None

        key = event.sym
        modifier = event.mod

        player = self.engine.player

        if key == tcod.event.K_PERIOD and modifier & (
            tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT
        ):
            return actions.TakeStairsAction(player)

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)
        elif key in WAIT_KEYS:
            action = WaitAction(player)

        elif key == tcod.event.K_ESCAPE:
            raise SystemExit
        elif key == tcod.event.K_v:
            return HistoryViewer(self.engine, self)
        elif key == tcod.event.K_g:
            action = PickupAction(player)

        elif key == tcod.event.K_i:
            return InventoryActivateHandler(self.engine)
        elif key == tcod.event.K_d:
            return InventoryDropHandler(self.engine)
        elif key == tcod.event.K_c:
            return CharacterScreenEventHandler(self.engine)
        elif key == tcod.event.K_SLASH:
            return LookHandler(self.engine)

        # No valid keypress
        return action

class DebugModeEventHandler(EventHandler):

    def __init__(self, engine: Engine):
        super().__init__(engine)

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle events for input handlers with an engine."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if self.handle_action(action_or_state):
            self.engine.turn_counter += 1
            return self
        return self

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:

        action: Optional[ActionOrHandler] = None

        key = event.sym
        modifier = event.mod

        player = self.engine.player

        if key == tcod.event.K_PERIOD and modifier & (
            tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT
        ):
            return actions.TakeStairsAction(player)

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = MovementAction(player, dx, dy)
        elif key in WAIT_KEYS:
            action = WaitAction(player)
        elif key == tcod.event.K_ESCAPE:
            raise SystemExit
        elif key == tcod.event.K_SLASH:
            return LookHandler(self.engine)

        if key == tcod.event.K_PERIOD and modifier & (
            tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT
        ):
            return actions.TakeStairsAction(player)

        # No valid keypress
        return action

class GameOverEventHandler(EventHandler):

    def on_quit(self) -> None:
        """Handle exiting out of a finished game"""
        if os.path.exists("savegame.sav"):
            os.remove("savegame.sav")   # Deletes the active save file
        print("Save Deleted.")
        raise exceptions.QuitWithoutSaving()    # Avoid saving a finished game


    def ev_quit(self, event: tcod.event.Quit) -> None:
        self.on_quit()

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        if event.sym == tcod.event.K_ESCAPE:
            self.on_quit()
        elif event.sym == tcod.event.K_v:
            return HistoryViewer(self.engine, self)
        elif event.sym == tcod.event.K_SLASH:
            return LookHandler(self.engine)


class HistoryViewer(EventHandler):
    """Print the history on a larger window which can be navigated."""

    def __init__(self, engine: Engine, previous_handler: EventHandler):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1
        self.previous_handler = previous_handler

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console) # Draw the main state as the background.

        log_console = tcod.Console(console.width - 6, console.height - 6)

        # Draw a frame with a custom banner title.
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0, 0, log_console.width, 1, "~|Message History|~", alignment = tcod.CENTER
        )

        # Render the message log using the cursor parameter.
        self.engine.message_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 2,
            self.engine.message_log.messages[: self.cursor + 1],
        )
        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        # Fancy conditional movement to make it feel right.
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]
            if adjust < 0 and self.cursor == 0:
                # Only move from the top to the bottom when you're on the edge.
                self.cursor = self.log_length - 1
            elif adjust > 0 and self.cursor == self.log_length - 1:
                # Same with bottom to top movement.
                self.cursor = 0
            else:
                # Otherwise move while staying clamped to the bounds of the history log
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
        elif event.sym == tcod.event.K_HOME:
            self.cursor = 0 # Move directly to the top message
        elif event.sym == tcod.event.K_END:
            self.cursor = self.log_length - 1 # Move directly to the last message.
        else: # Any other key moves back to the last state.
            return self.previous_handler


class AskUserEventHandler(EventHandler):
    """Handles user input for actions which require special input."""

    def handle_action(self, action: Optional[ActionOrHandler]) -> bool:
        """Return to the main even handler when a valid action was performed."""
        if super().handle_action(action):
            return True
        return False

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """By default any key exists this input handler."""
        if event.sym in {    # Ignore modifier keys
            tcod.event.K_LSHIFT,
            tcod.event.K_RSHIFT,
            tcod.event.K_LCTRL,
            tcod.event.K_RCTRL,
            tcod.event.K_LALT,
            tcod.event.K_RALT,
        }:
            return None
        return self.on_exit()

    def on_exit(self) -> Optional[ActionOrHandler]:
        """
        Called when the user is trying to exit or cancel an action.

        By default this returns to the main event handler.
        """
        return MainGameEventHandler(self.engine)


class CharacterScreenEventHandler(AskUserEventHandler):
    TITLE = "character"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        x = render_standards.character_screen_x
        y = 0

        render_functions.render_character_screen(
            console=console,
            engine=self.engine,
            x=x,
            y=y,
            width=render_standards.character_screen_width,
            height=render_standards.character_screen_height,
            in_use=True
        )

        console.print(
            x = x + render_standards.padding_standard,
            y = y + render_standards.padding_standard,
            string = f"Level: {self.engine.player.level.current_level}"
        )
        console.print(
            x = x + render_standards.padding_standard,
            y = y + render_standards.padding_standard + 1,
            string = f"XP: {self.engine.player.level.current_xp}"
        )
        console.print(
            x = x + render_standards.padding_standard,
            y = y + render_standards.padding_standard + 2,
            string = f"XP for next level: {self.engine.player.level.experience_to_next_level}"
        )
        console.print(
            x = x + render_standards.padding_standard,
            y = y + render_standards.padding_standard + 4,
            string = f"Attack: {self.engine.player.fighter.base_power} + "
                     f"{self.engine.player.equipment.power_bonus}"
        )
        console.print(
            x = x + render_standards.padding_standard,
            y = y + render_standards.padding_standard + 5,
            string = f"Defense: {self.engine.player.fighter.base_defense} + "
                     f"{self.engine.player.equipment.power_bonus}"
        )


class SelectScreenIndexHandler(AskUserEventHandler):
    """Handles asking the user for an index on the map."""

    def __init__(self, engine: Engine):
        """Sets the cursor to the player when this handler is constructed."""
        super().__init__(engine)
        player = self.engine.player
        engine.cursor_location = player.x, player.y

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)
        x, y = self.engine.cursor_location
        console.tiles_rgb["bg"][x, y] = color.white
        console.tiles_rgb["fg"][x, y] = color.black

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """Check for key movement or confirmation keys."""
        key = event.sym
        if key in MOVE_KEYS:
            modifier = 1    # Holding modifier keys will speed up key movement.
            if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                modifier *= 5
            if event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL):
                modifier *= 10
            if event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_RALT):
                modifier *= 20

            x, y = self.engine.cursor_location
            dx, dy = MOVE_KEYS[key]
            x += dx * modifier
            y += dy * modifier
            # Clamp the cursor index to the map size.
            x = max(0, min(x, self.engine.game_map.width - 1))
            y = max(0, min(y, self.engine.game_map.height - 1))
            self.engine.cursor_location = x, y
            return None
        elif key in CONFIRM_KEYS:
            return self.on_index_selected(*self.engine.cursor_location)
        return super().ev_keydown(event)

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        """Called when an index is selected."""
        raise NotImplementedError()


class OptionSelectionHandler(AskUserEventHandler):
    """
    Handles the creation of an iterable selection object, an iterator for the present selection
    along with a method for the selection confirm through the enter key and moving the present
    selection.
    Subclasses are expected to implement how the selection is confirmed in the first place,
    and the selection itself.
    """
    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.selection: Iterable = []
        self.present_selection: int = 0
        self.option_visual_base_height: int = 0

    def confirm_selection(self):
        """
        If you're seeing this something has gone wrong and this function is not
        overridden for the subclass. Will return NotImplementedError.
        """
        raise NotImplementedError()

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        key = event.sym
        if key == tcod.event.K_UP:
            self.present_selection = max(0, self.present_selection - 1)
        elif key == tcod.event.K_DOWN:
            self.present_selection = min(len(self.selection) - 1, self.present_selection + 1)
        elif key in CONFIRM_KEYS:
            return self.confirm_selection()
        else:
            return super().ev_keydown(event)


class LevelUpEventHandler(OptionSelectionHandler):
    TITLE = "Level Up"

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.option_visual_base_height = 4

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        self.selection = list(enumerate([
            ["Max HP", 20, self.engine.player.fighter.hp_attr],
            ["Base Attack", 1, self.engine.player.fighter.base_power],
            ["Base Defense", 1, self.engine.player.fighter.base_defense],
        ]))

        if self.engine.player.x <= 30:
            x = 30
        else:
            x = 0

        console.draw_frame(
            x = x,
            y = 0,
            width = 45,
            height = 8,
            title = self.TITLE,
            clear = True,
            fg = (255, 255, 255),
            bg = (0, 0, 0),
        )

        console.print(x = x + 1, y = 1, string = f"You are now level "
                                                 f"{self.engine.player.level.current_level + 1}")
        console.print(x = x + 1, y = 2, string = "Select a bonus.")

        for i, option in self.selection:
            console.print(
                x = x + 1,
                y = self.option_visual_base_height + i,
                string = f"+{option[1]} {option[0]} "
                         f"(from the current value {option[2].max if option[0] == 'Max HP' else option[2].value})",
                fg = (color.selection if i is self.present_selection else color.menu_text),
                bg = (color.white if i is self.present_selection else None)
            )

    def confirm_selection(self):
        player = self.engine.player

        if self.present_selection == 0:
            player.level.increase_max_hp()
            player.fighter.hp_attr.max(20, True)
        elif self.present_selection == 1:
            player.level.increase_power()
            player.fighter.attributes[self.present_selection].add_to_value(1)
        else:
            player.level.increase_defense()
            player.fighter.attributes[self.present_selection].add_to_value(1)

        if not player.level.requires_level_up:
            return self.on_exit()


class LookHandler(SelectScreenIndexHandler):
    """Lets the player look around using the keyboard."""

    def __init__(self, engine: Engine, parent_handler: Optional[BaseEventHandler] = None):
        super().__init__(engine)
        if parent_handler is None:
            parent_handler = MainGameEventHandler(engine)

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)
        render_functions.render_names_at_cursor_location(
            console=console,
            x=1,
            y=2,
            engine=self.engine
        )

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        """Return to main handler."""
        return parent_handler


class SingleRangedAttackHandler(SelectScreenIndexHandler):
    """Handles targeting a single enemy. Only the enemy selected will be affected"""

    def __init__(
            self, engine: Engine, callback: Callable[[Tuple[int, int]], Optional[ActionOrHandler]]
    ):
        super().__init__(engine)

        self.callback = callback

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        return self.callback((x, y))


class AreaRangedAttackHandler(SelectScreenIndexHandler):
    """Handles targeting an area within a given radius. Any entity within the area will be affected."""

    def __init__(
            self,
            engine: Engine,
            radius: int,
            callback: Callable[[Tuple[int, int]], Optional[ActionOrHandler]],
    ):
        super().__init__(engine)

        self.radius = radius
        self.callback = callback

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)

        x, y = self.engine.cursor_location

        # Draw a rectangle around the targeted area, so the player can see the affected tiles.
        console.draw_frame(
            x = x - self.radius - 1,
            y = y - self.radius - 1,
            width = self.radius ** 2,
            height = self.radius ** 2,
            fg = color.red,
            clear = False,
        )

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        return self.callback((x, y))


class InventoryEventHandler(OptionSelectionHandler):
    """
    This handler lets the user select an item.

    What happens then depends on the subclass
    """

    title = "<missing title>"

    def on_render(self, console: tcod.Console) -> None:
        """
        Render an inventory menu, which displays the items in the inventory.
        Will move to a different position based on where the player is located, they are.
        """

        self.selection = list(enumerate(self.engine.player.inventory.items))

        super().on_render(console)
        number_of_items_in_inventory = len(self.selection)

        x = render_standards.inventory_x
        y = render_standards.inventory_y

        render_functions.render_inventory_screen(
            x = x,
            y = y,
            width = render_standards.inventory_width,
            height = render_standards.screen_height,
            title = self.title,
            engine = self.engine,
            in_use = True,
            console = console
        )

        if number_of_items_in_inventory > 0:
            for i, item in self.selection:
                is_equipped = self.engine.player.equipment.item_is_equipped(item)

                item_string = f"{item.name}"

                if is_equipped:
                    item_string = f"{item_string} (E)"

                console.print(
                    x + render_standards.padding_standard,
                    y + i + render_standards.padding_standard,
                    item_string,
                    fg = (color.maroon if i == self.present_selection else color.menu_text),
                    bg = (color.white if i == self.present_selection else color.black)
                )

        else:
            console.print(x + render_standards.padding_standard, y + render_standards.padding_standard, "(Empty)")

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Called when the user selects a valid item"""
        raise NotImplementedError

    def confirm_selection(self):
        return self.on_item_selected(self.engine.player.inventory.items[self.present_selection])


class InventoryActivateHandler(InventoryEventHandler):
    """Handle using an inventory item."""

    title = "accessing items"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Return the action for the selected item."""
        if item.consumable:
            return item.consumable.get_action(self.engine.player)
        elif item.equippable:
            return actions.EquipAction(self.engine.player, item)
        else:
            return None


class InventoryDropHandler(InventoryEventHandler):
    """Handle dropping an inventory item"""

    title = "dropping item"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Drop this item."""
        return DropItem(self.engine.player, item)