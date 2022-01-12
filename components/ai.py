from __future__ import annotations

import random
from typing import List, Optional, Tuple, TYPE_CHECKING, Set

import numpy as np  # type: ignore
import tcod

from actions import Action, BumpAction, MeleeAction, MovementAction, WaitAction
from components.attribute import Attribute

if TYPE_CHECKING:
    from actor import Actor


class BaseAI(Action):
    entity: Actor
    target: Optional[Actor] = None

    def perform(self) -> None:
        raise NotImplementedError()

    def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        """Compute and return a path to the target position

        If there is no valid path then returns an empty list."""
        # Copy the walkable array
        cost = np.array(self.entity.gamemap.tiles["walkable"], dtype = np.int8)

        for entity in self.entity.gamemap.entities:
            # Check that an entity blocks movement and the cost isn't zero (blocking).
            if entity.blocks_movement and cost[entity.x, entity.y]:
                # Add to the cost of a blocked position
                # A lower number means more enemies will crowd behind each other in hallways
                # A higher number means entities will take longer paths in order to surround the player
                cost[entity.x, entity.y] += 10

        # Create a graph from the cost array and pass that graph to a new pathfinder
        graph = tcod.path.SimpleGraph(cost = cost, cardinal = 2, diagonal = 3)
        pathfinder = tcod.path.Pathfinder(graph)

        pathfinder.add_root((self.entity.x, self.entity.y)) # Start positions

        # Compute the path to the destination and remove the starting point.
        path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        # Convert from List[List[int]] to List[Tuple[int, int]].
        return [(index[0], index[1]) for index in path]


class ConfusedEnemy(BaseAI):
    """
    A confused enemy will stumble around aimlessly for a given number of turns, then revert back to its previous AI.
    If an actor occupies a tile it is randomly moving into, it will attack
    """

    def __init__(
            self, entity: Actor, previous_ai: Optional[BaseAI], turns_remaining: int
    ):
        super().__init__(entity)

        self.previous_ai = previous_ai
        self.turns_remaining = turns_remaining

    def perform(self) -> None:
        # Revert the AI to the original state if the effect has run its course.
        if self.turns_remaining <= 0:
            self.engine.message_log.add_message(
                f"The {self.entity.name} is no longer confused."
            )
            self.entity.ai = self.previous_ai
        else:
            # Pick a random direction
            direction_x, direction_y = random.choice(
                [
                    (-1, -1),
                    (0, -1),
                    (1, -1),
                    (-1, 0),
                    (1, 0),
                    (-1, 1),
                    (0, 1),
                    (1, 1)
                ]
            )

            self.turns_remaining -= 1

            # The actor will either try to move or attack in the chosen random direction.
            # It's possible the actor will just bump into the wall, wasting a turn.
            return BumpAction(self.entity, direction_x, direction_y,).perform()

class PursuitAI(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []
        self.target = None

    def perform(self) -> None:
        if self.target is not None:
            target = self.target
            dx = target.x - self.entity.x
            dy = target.y - self.entity.y
            distance = max(abs(dx), abs(dy)) # Chebyshev distance.

            if distance <= 1:
                return MeleeAction(self.entity, dx, dy).perform()

            self.path = self.get_path_to(target.x, target.y)

            if self.path:
                dest_x, dest_y = self.path.pop(0)
                return MovementAction(
                    self.entity, dest_x - self.entity.x, dest_y - self.entity.y
                ).perform()

        return WaitAction(self.entity).perform()

class WanderAI(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)

    def perform(self):
        movement_chance = random.random()
        if movement_chance > 0.5:
            return WaitAction(self.entity)
        else:
            direction_x, direction_y = random.choice(
                [
                    (-1, -1),
                    (0, -1),
                    (1, -1),
                    (-1, 0),
                    (1, 0),
                    (-1, 1),
                    (0, 1),
                    (1, 1)
                ]
            )
        return MovementAction(self.entity, direction_x, direction_y).perform()

class PathableAI(BaseAI):
    """
    An AI with a target designated by its self.target point that paths to said target without attacking.
    """
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.target = None
        self.path = None

    def perform(self) -> None:
        if self.target is not None:
            target = self.target
            dx = target[0] - self.entity.x
            dy = target[1] - self.entity.y
            distance = min(abs(dx), abs(dy))

            self.path = self.get_path_to(target[0], target[1])

            if self.path:
                if distance == 0:
                    self.path = None    # Deletes the path when at destination
                else:
                    dest_x, dest_y = self.path.pop(0)
                    return MovementAction(
                        self.entity, dest_x - self.entity.x, dest_y - self.entity.y
                    ).perform()

        return WaitAction(self.entity).perform()


class TargetableAI(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.pursuit_mode = PursuitAI(entity)
        self.wander_mode = WanderAI(entity)

    def potential_targets(self) -> Optional[Set[Actor]]:
        from actor import Actor
        from components.affiliation import Affiliations
        potential_targets: set = set()
        if not self.entity.hostility_set is None:
            hostiles = self.entity.hostility_set
            hostile_affiliations: set = set()
            hostile_entities: set = set()

            for i in hostiles:
                if isinstance(i, Actor):
                    hostile_entities.add(i)
                elif isinstance(i, Affiliations):
                    hostile_affiliations.add(i)
            for i in self.entity.vision.visible_actors():
                if i.affiliation in hostile_affiliations or i in hostile_entities:
                    potential_targets.add(i)
        return potential_targets

    def set_target(self) -> Actor:
        return list(self.potential_targets())[0] if len(self.potential_targets()) != 0 else None

    def perform(self) -> None:
        self.target = self.set_target()
        self.pursuit_mode.target = self.target
        if self.pursuit_mode.target:
            return self.pursuit_mode.perform()
        else:
            return self.wander_mode.perform()

class RetreatableAI(TargetableAI):
    def __init__(self, entity, retreat_threshold: float = 0.5):
        """
        Creates an AI capable of attacking and retreating when their health reaches the retreat_threshold
        :param entity: Parent entity
        :param retreat_threshold: Float representing the fraction of health required before retreat mode kicks in
        """
        super().__init__(entity)
        self.retreat_mode = PathableAI(entity)
        self.retreat_cooldown: int = 0
        self.retreat_threshold = retreat_threshold

    def find_retreat_point(self, retreat_from):
        retreatable = False
        dx = self.entity.x - retreat_from[0]
        dy = self.entity.y - retreat_from[1]
        own_x = self.entity.x
        own_y = self.entity.y
        max_x = self.entity.gamemap.width - 1
        max_y = self.entity.gamemap.height - 1
        while not retreatable:
            random_x = (random.randint(own_x, max_x) if dx < 0 else
                        random.randint(0, max_x) if dx == 0 else
                        random.randint(0, own_x))
            random_y = (random.randint(own_y, max_y) if dy < 0 else
                        random.randint(0, max_y) if dy == 0 else
                        random.randint(0, own_y))
            retreatable = self.entity.gamemap.tiles["walkable"][random_x, random_y]
        print(f"{self.entity.name} is retreating from {retreat_from} to {(random_x, random_y)}")
        return random_x, random_y

    def perform(self) -> None:
        entity_health_attribute: Attribute = self.entity.fighter.hp_attr
        self.target = self.set_target()
        self.pursuit_mode.target = self.target
        if entity_health_attribute.value <= entity_health_attribute.max * self.retreat_threshold:
            # When the entity is at a fourth of its health or less, enter retreat mode
            if (not self.retreat_mode.path or self.entity.last_attacker in self.entity.vision.visible_actors()) and self.retreat_cooldown == 0:
                self.retreat_mode.target = self.find_retreat_point((self.entity.last_attacker.x,
                                                                    self.entity.last_attacker.y))
                self.retreat_cooldown = 10
            self.retreat_cooldown -= 1
            return self.retreat_mode.perform()
        elif self.pursuit_mode.target:
            return self.pursuit_mode.perform()
        else:
            return self.wander_mode.perform()