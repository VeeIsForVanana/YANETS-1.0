from __future__ import annotations

from typing import TYPE_CHECKING

import color
import exceptions
from components.base_component import BaseComponent
from components.attribute import Attribute, HealthAttribute, DefenseAttribute, PowerAttribute
from render_order import RenderOrder

if TYPE_CHECKING:
    from entity import Actor

class Fighter(BaseComponent):
    parent: Actor

    def __init__(self, hp: int, base_defense: int, base_power: int):
        self.hp_attr = HealthAttribute(hp)
        self.base_defense = DefenseAttribute(base_defense)
        self.base_power = PowerAttribute(base_power)
        self.attributes = [self.hp_attr, self.base_defense, self.base_power]

    @property
    def power(self) -> int:
        return self.base_power.value + self.power_bonus

    @property
    def defense(self) -> int:
        return self.base_defense.value + self.defense_bonus

    @property
    def power_bonus(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.defense_bonus
        else:
            return 0

    @property
    def defense_bonus(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.power_bonus
        else:
            return 0

    def die(self) -> None:
        if self.engine.player is self.parent:
            death_message = "You died!"
            death_message_color = color.player_die
        else:
            death_message = f"{self.parent.name} is dead!"
            death_message_color = color.enemy_die
        self.parent.char = "%"
        self.parent.color = (191, 0, 0)
        self.parent.blocks_movement = False
        self.parent.ai = None

        if self.parent.inventory.items:
            for i in range(len(self.parent.inventory.items)):
                self.parent.inventory.drop(self.parent.inventory.items[0])
        self.parent.name = f"Remains of {self.parent.name}"
        self.parent.render_order = RenderOrder.CORPSE
        self.parent.gamemap.remove_entity_id(self.parent.entity_id)
        self.parent.gamemap.new_entity_id(self.parent)

        self.engine.message_log.add_message(death_message, death_message_color)

        self.engine.player.level.add_xp(self.parent.level.xp_given)

    def heal(self, amount: int) -> int:
        if self.hp_attr.value == self.hp_attr.max:
            return 0

        new_hp_value = self.hp_attr.value + amount

        if new_hp_value > self.hp_attr.max:
            new_hp_value = self.hp_attr.max

        amount_recovered = new_hp_value - self.hp_attr.value

        if amount_recovered > 0:
            self.hp_attr.add_to_value(amount_recovered)

        return amount_recovered

    def take_damage(self, amount: int) -> None:
        self.hp_attr.add_to_value(-1 * amount)
        if self.hp_attr.value <= 0:
            self.die()

