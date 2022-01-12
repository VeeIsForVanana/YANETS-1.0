from __future__ import annotations

from typing import Tuple, Type, Optional, List

from components.ai import BaseAI
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory, PhysicalParts
from components.level import Level
from components.affiliation import Affiliations, default_hostilities
from components.vision import Vision, ShortVision
from entity import Entity
from render_order import RenderOrder


class Actor(Entity):
    def __init__(
            self,
            *,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            color: Tuple[int, int, int] = (255, 255, 255),
            name: str = "<Unnamed>",
            vision: Type[Vision] = ShortVision,
            affiliation: Affiliations = Affiliations.generic_hostile,
            physical_parts: PhysicalParts,
            ai_cls: Type[BaseAI],
            equipment: Equipment,
            fighter: Fighter,
            inventory: Inventory,
            level: Level,
    ):
        super().__init__(
            x = x,
            y = y,
            char = char,
            color = color,
            name = name,
            blocks_movement = True,
            render_order = RenderOrder.ACTOR,
        )

        self.ai: Optional[BaseAI] = ai_cls(self)

        if vision:
            self.vision = vision(self)
            self.vision.parent = self

        self.equipment: Equipment = equipment
        self.equipment.parent = self

        self.fighter = fighter
        self.fighter.parent = self

        self.inventory = inventory
        self.inventory.parent = self

        self.physical_parts = physical_parts
        self.physical_parts.parent = self

        self.level = level
        self.level.parent = self

        self.affiliation = affiliation
        self.hostility_set = default_hostilities.get(self.affiliation, None)

    @property
    def attributes(self) -> List:
        return self.fighter.attributes

    @property
    def is_alive(self) -> bool:
        """Returns True as long as this actor can perform actions."""
        return bool(self.ai)