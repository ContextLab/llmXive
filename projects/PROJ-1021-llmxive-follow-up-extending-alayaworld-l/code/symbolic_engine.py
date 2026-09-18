"""
Symbolic Engine for AlayaWorld Hybrid Logic Integration.

This module implements a pure Python, rule-based state tracker for object states
(HP, inventory, position) based on action inputs. It is designed to be deterministic
and serves as the ground truth reference for calculating Semantic Drift Scores
against the visual output of the generative model.

Rules implemented:
- Hit: Reduces HP by a moderate amount (fixed value: 15).
- Summon: Creates a new object with default HP (100) and initial position.
- Move: Updates object position.
- Kill: Sets object HP to 0 and marks as dead.
- Heal: Increases HP (capped at max HP).
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import json


class ActionType(Enum):
    HIT = "hit"
    SUMMON = "summon"
    MOVE = "move"
    KILL = "kill"
    HEAL = "heal"
    NONE = "none"


@dataclass
class ObjectState:
    """Represents the state of a single object in the symbolic world."""
    object_id: str
    hp: int
    max_hp: int = 100
    is_alive: bool = True
    position_x: float = 0.0
    position_y: float = 0.0
    inventory: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ActionLogEntry:
    """Log entry for a single action execution."""
    action_type: str
    target_id: Optional[str]
    parameters: Dict[str, Any]
    resulting_state: Dict[str, Any]
    timestamp: int  # Frame index or logical tick

class SymbolicEngine:
    """
    Pure Python rule-based state tracker.

    Maintains a deterministic world state based on a sequence of actions.
    Implements specific rules for HP reduction, summoning, and movement.
    """

    # Rule constants
    HIT_HP_REDUCTION = 15
    SUMMON_DEFAULT_HP = 100
    HEAL_AMOUNT = 20
    MAX_HP_CAP = 100

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the symbolic engine.

        Args:
            seed: Random seed (not used for state logic, but for reproducibility
                  if any stochastic elements were introduced later).
        """
        self.objects: Dict[str, ObjectState] = {}
        self.action_log: List[ActionLogEntry] = []
        self.current_tick: int = 0
        self.seed = seed

    def get_state(self) -> Dict[str, Any]:
        """Return a snapshot of the current world state."""
        return {
            "objects": {k: v.to_dict() for k, v in self.objects.items()},
            "tick": self.current_tick
        }

    def apply_action(self, action_type: str, target_id: Optional[str], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply an action to the world state and return the resulting state of the target.

        Args:
            action_type: Type of action (hit, summon, move, kill, heal).
            target_id: ID of the object to act upon (or None for summon).
            params: Action-specific parameters (e.g., damage amount, new coordinates).

        Returns:
            Dictionary representing the resulting state of the affected object(s).
        """
        self.current_tick += 1
        action_enum = ActionType(action_type.lower())
        result_state = {}

        if action_enum == ActionType.HIT:
            if target_id is None:
                raise ValueError("Hit action requires a target_id.")
            if target_id not in self.objects:
                raise ValueError(f"Target {target_id} does not exist.")
            
            obj = self.objects[target_id]
            damage = params.get("damage", self.HIT_HP_REDUCTION)
            
            obj.hp = max(0, obj.hp - damage)
            if obj.hp == 0:
                obj.is_alive = False
            
            result_state = obj.to_dict()

        elif action_enum == ActionType.SUMMON:
            if target_id is None:
                # Generate a simple ID if not provided
                target_id = f"obj_{len(self.objects):03d}"
            if target_id in self.objects:
                raise ValueError(f"Object {target_id} already exists.")

            pos_x = params.get("x", 0.0)
            pos_y = params.get("y", 0.0)
            
            new_obj = ObjectState(
                object_id=target_id,
                hp=self.SUMMON_DEFAULT_HP,
                position_x=pos_x,
                position_y=pos_y,
                is_alive=True
            )
            self.objects[target_id] = new_obj
            result_state = new_obj.to_dict()

        elif action_enum == ActionType.MOVE:
            if target_id is None:
                raise ValueError("Move action requires a target_id.")
            if target_id not in self.objects:
                raise ValueError(f"Target {target_id} does not exist.")
            
            obj = self.objects[target_id]
            obj.position_x = params.get("x", obj.position_x)
            obj.position_y = params.get("y", obj.position_y)
            result_state = obj.to_dict()

        elif action_enum == ActionType.KILL:
            if target_id is None:
                raise ValueError("Kill action requires a target_id.")
            if target_id not in self.objects:
                raise ValueError(f"Target {target_id} does not exist.")
            
            obj = self.objects[target_id]
            obj.hp = 0
            obj.is_alive = False
            result_state = obj.to_dict()

        elif action_enum == ActionType.HEAL:
            if target_id is None:
                raise ValueError("Heal action requires a target_id.")
            if target_id not in self.objects:
                raise ValueError(f"Target {target_id} does not exist.")
            
            obj = self.objects[target_id]
            heal_val = params.get("amount", self.HEAL_AMOUNT)
            obj.hp = min(self.MAX_HP_CAP, obj.hp + heal_val)
            if obj.hp > 0:
                obj.is_alive = True
            result_state = obj.to_dict()

        else:
            raise ValueError(f"Unknown action type: {action_type}")

        # Log the action
        self.action_log.append(ActionLogEntry(
            action_type=action_type,
            target_id=target_id,
            parameters=params,
            resulting_state=result_state,
            timestamp=self.current_tick
        ))

        return result_state

    def execute_sequence(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute a sequence of actions and return the log of resulting states.

        Args:
            actions: List of dicts with keys: 'type', 'target_id', 'params'.

        Returns:
            List of resulting state dictionaries for each action.
        """
        results = []
        for action in actions:
            action_type = action.get("type")
            target_id = action.get("target_id")
            params = action.get("params", {})
            
            result = self.apply_action(action_type, target_id, params)
            results.append(result)
        return results

    def to_json(self) -> str:
        """Serialize the current state and log to JSON string."""
        data = {
            "state": self.get_state(),
            "log": [asdict(entry) for entry in self.action_log]
        }
        return json.dumps(data, indent=2)

    def save_log(self, filepath: str) -> None:
        """Save the action log to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump([asdict(entry) for entry in self.action_log], f, indent=2)


def main():
    """
    CLI entry point for testing the symbolic engine.
    Runs a simple sequence of actions and prints the resulting state log.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Symbolic Engine CLI")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="data/symbolic_log.json", 
                        help="Output path for the JSON log")
    args = parser.parse_args()

    engine = SymbolicEngine(seed=args.seed)

    # Define a sample sequence of actions
    actions = [
        {"type": "summon", "target_id": "hero", "params": {"x": 0, "y": 0}},
        {"type": "summon", "target_id": "enemy", "params": {"x": 5, "y": 5}},
        {"type": "hit", "target_id": "enemy", "params": {"damage": 15}},
        {"type": "move", "target_id": "hero", "params": {"x": 1, "y": 1}},
        {"type": "hit", "target_id": "enemy", "params": {"damage": 15}},
        {"type": "heal", "target_id": "hero", "params": {"amount": 20}},
        {"type": "kill", "target_id": "enemy", "params": {}},
    ]

    results = engine.execute_sequence(actions)
    
    print(f"Executed {len(results)} actions.")
    print("Final State:")
    print(engine.get_state())
    
    engine.save_log(args.output)
    print(f"Log saved to {args.output}")

if __name__ == "__main__":
    main()