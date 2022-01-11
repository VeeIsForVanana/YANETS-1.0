import copy

import render_order
from components.ai import PursuitAI, BaseAI, TargetableAI
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory, PhysicalParts
from components.level import Level
from components.affiliation import Affiliations
from item_factories import organic_matter
from entity import Entity
from actor import Actor
import color

player = Actor(
    char="@",
    color=(255, 255, 255),
    name="Player",
    ai_cls=BaseAI,
    equipment=Equipment(),
    fighter=Fighter(hp=30, base_defense=1, base_power=2),
    inventory=Inventory(capacity=26),
    physical_parts=PhysicalParts(2, [copy.deepcopy(organic_matter)]),
    level=Level(level_up_base=200),
    affiliation=Affiliations.player
)

debug_player = Entity(
    char="@",
    color=color.dark_gray,
    name="Debug Player",
    render_order=render_order.RenderOrder.ACTOR
)

orc = Actor(
    char="o",
    color=(63, 127, 63),
    name="Orc",
    ai_cls=TargetableAI,
    equipment=Equipment(),
    fighter=Fighter(hp=10, base_defense=0, base_power=3),
    inventory=Inventory(capacity=0),
    physical_parts=PhysicalParts(2, [copy.deepcopy(organic_matter)]),
    level=Level(xp_given=35)
)

troll = Actor(
    char="T",
    color=(0, 127, 0),
    name="Troll",
    ai_cls=TargetableAI,
    equipment=Equipment(),
    fighter=Fighter(hp=16, base_defense=1, base_power=4),
    inventory=Inventory(capacity=0),
    physical_parts=PhysicalParts(2, [copy.deepcopy(organic_matter)]),
    level=Level(xp_given=100)
)