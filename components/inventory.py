from __future__ import annotations

import random
from typing import List, TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor, Item

class Inventory(BaseComponent):
    parent: Actor

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.items: List[Item] = []

    def drop(self, item: Item) -> None:
        """
        Removes an item from the inventory and restores it to the game map at the player's current location
        """
        self.items.remove(item)
        if item.equippable and self.parent.equipment.item_is_equipped(item):
            self.parent.equipment.toggle_equip(item)
        if self.parent.is_alive:
            item.place(self.parent.x, self.parent.y, self.gamemap)
            self.engine.message_log.add_message(f"{'You' if self.parent.entity_id == 0 else self.parent.name}"
                                                f" dropped {item.name}.")
        else:
            dx, dy = random.randint(-1, 1), random.randint(-1, 1)
            item.place(self.parent.x + dx, self.parent.y + dy, self.gamemap)
            self.engine.message_log.add_message(f"{'You' if self.parent.entity_id == 0 else self.parent.name}"
                                                f" dropped {item.name} randomly about as they died.")
