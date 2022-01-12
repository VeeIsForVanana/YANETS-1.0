from __future__ import annotations

import random
from typing import List, Optional, Tuple, TYPE_CHECKING

import numpy as np  # type: ignore
import tcod

from actions import Action, BumpAction, MeleeAction, MovementAction, WaitAction


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

class RetreatAI(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)

class TargetableAI(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.PursuitMode = PursuitAI(entity)
        self.WanderMode = WanderAI(entity)

    def potential_targets(self) -> List[Actor]:
        return [actor if actor.affiliation != self.entity.affiliation else None for actor in
                self.entity.vision.visible_actors()]

    def set_target(self) -> Actor:
        return self.potential_targets()[0] if len(self.potential_targets()) != 0 else None

    def perform(self) -> None:
        self.target = self.set_target()
        self.PursuitMode.target = self.target
        if self.PursuitMode.target:
            return self.PursuitMode.perform()
        else:
            self.WanderMode.perform()

class RetreatableAI(TargetableAI):
    def perform(self) -> None: