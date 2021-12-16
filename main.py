#!\usr\bin\env python3
import traceback

import tcod

import color
import exceptions
import input_handlers
import setup_game
import render_standards

def save_game(handler: input_handlers.BaseEventHandler, filename: str) -> None:
    """If the current event handler has an active Engine then save it."""
    if isinstance(handler, input_handlers.EventHandler):
        handler.engine.save_as(filename)
        print("Game saved.")

def main() -> None:
    screen_width = render_standards.screen_width
    screen_height = render_standards.screen_height

    tileset = tcod.tileset.load_tilesheet(
        "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    with tcod.context.new_terminal(
        screen_width,
        screen_height,
        tileset = tileset,
        title = "Yet Another Roguelike Tutorial",
        vsync = True,
    ) as context:
        root_console = tcod.Console(screen_width, screen_height, order = "F")

        handler: input_handlers.BaseEventHandler = setup_game.MainMenu(root_console)

        try:
            main_event_counter: int = 0
            while True:
                root_console.clear()
                if isinstance(handler, setup_game.MainMenu):
                    handler.on_render()
                else:
                    handler.on_render(console = root_console)
                context.present(root_console)

                try:
                    for event in tcod.event.wait():
                        context.convert_event(event)
                        handler = handler.handle_events(event)
                        main_event_counter += 1
                except Exception:   # Handle exceptions in game.
                    traceback.print_exc()   # Print error to stderr.
                    # Then print the error to the message log.
                    if isinstance(handler, input_handlers.EventHandler):
                        handler.engine.message_log.add_message(
                            traceback.format_exc(), color.error
                        )
        except exceptions.QuitWithoutSaving:
            raise
        except SystemExit:  # Save and quit.
            save_game(handler, "savegame.sav")
            raise
        except BaseException:   # Save on any other unexpected exception
            save_game(handler, "savegame.sav")
            raise

if __name__ == "__main__":
    main()