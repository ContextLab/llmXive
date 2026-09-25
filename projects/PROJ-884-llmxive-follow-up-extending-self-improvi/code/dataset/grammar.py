"""
Grammar Definition and Validation for Puzzle Constraints.
Defines the formal language for puzzle constraints and provides validation logic.
"""

import re
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


class ConstraintType(Enum):
    """Types of constraints supported by the grammar."""
    EQUALITY = "equality"
    INEQUALITY = "inequality"
    ADJACENCY = "adjacency"
    ORDERING = "ordering"
    EXISTENCE = "existence"
    PATH = "path"


@dataclass
class GrammarRule:
    """Represents a rule in the grammar."""
    name: str
    pattern: str
    validator: callable
    description: str


class GrammarValidator:
    """
    Validates solutions against the defined puzzle grammar.
    Ensures syntactic validity of constraints and solution steps.
    """

    def __init__(self):
        """Initialize the grammar validator with standard rules."""
        self.rules = self._initialize_rules()

    def _initialize_rules(self) -> Dict[str, GrammarRule]:
        """Initialize the set of grammar rules."""
        return {
            "equality": GrammarRule(
                name="equality",
                pattern=r"^\s*\w+\s*==\s*\w+\s*$",
                validator=self._validate_equality,
                description="Equality constraint between two variables"
            ),
            "inequality": GrammarRule(
                name="inequality",
                pattern=r"^\s*\w+\s*!=\s*\w+\s*$",
                validator=self._validate_inequality,
                description="Inequality constraint between two variables"
            ),
            "adjacency": GrammarRule(
                name="adjacency",
                pattern=r"^\s*adjacent\s*\(\s*\w+\s*,\s*\w+\s*\)\s*$",
                validator=self._validate_adjacency,
                description="Adjacency constraint between two elements"
            ),
            "ordering": GrammarRule(
                name="ordering",
                pattern=r"^\s*\w+\s*<\s*\w+\s*$|^\s*\w+\s*>\s*\w+\s*$",
                validator=self._validate_ordering,
                description="Ordering constraint between two variables"
            ),
            "path": GrammarRule(
                name="path",
                pattern=r"^\s*path\s*\(\s*\w+\s*,\s*\w+\s*\)\s*$",
                validator=self._validate_path,
                description="Path existence constraint"
            )
        }

    def _validate_equality(self, constraint: str) -> Tuple[bool, Optional[str]]:
        """Validate an equality constraint."""
        # Basic structure check
        parts = constraint.split("==")
        if len(parts) != 2:
            return False, "Invalid equality format"
        var1 = parts[0].strip()
        var2 = parts[1].strip()
        if not var1.isidentifier() or not var2.isidentifier():
            return False, "Variables must be valid identifiers"
        return True, None

    def _validate_inequality(self, constraint: str) -> Tuple[bool, Optional[str]]:
        """Validate an inequality constraint."""
        parts = constraint.split("!=")
        if len(parts) != 2:
            return False, "Invalid inequality format"
        var1 = parts[0].strip()
        var2 = parts[1].strip()
        if not var1.isidentifier() or not var2.isidentifier():
            return False, "Variables must be valid identifiers"
        return True, None

    def _validate_adjacency(self, constraint: str) -> Tuple[bool, Optional[str]]:
        """Validate an adjacency constraint."""
        match = re.match(r"adjacent\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)", constraint)
        if not match:
            return False, "Invalid adjacency format"
        return True, None

    def _validate_ordering(self, constraint: str) -> Tuple[bool, Optional[str]]:
        """Validate an ordering constraint."""
        if "<" in constraint:
            parts = constraint.split("<")
        elif ">" in constraint:
            parts = constraint.split(">")
        else:
            return False, "Invalid ordering operator"

        if len(parts) != 2:
            return False, "Invalid ordering format"
        var1 = parts[0].strip()
        var2 = parts[1].strip()
        if not var1.isidentifier() or not var2.isidentifier():
            return False, "Variables must be valid identifiers"
        return True, None

    def _validate_path(self, constraint: str) -> Tuple[bool, Optional[str]]:
        """Validate a path constraint."""
        match = re.match(r"path\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)", constraint)
        if not match:
            return False, "Invalid path format"
        return True, None

    def validate_constraint(self, constraint: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a single constraint string.

        Args:
            constraint: The constraint string to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        for rule_name, rule in self.rules.items():
            if re.match(rule.pattern, constraint):
                return rule.validator(constraint)

        return False, f"Constraint does not match any known grammar rule: {constraint}"

    def validate_solution(self, solution: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate a complete solution against the grammar.

        Args:
            solution: The solution dictionary to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        # Check required fields
        if "steps" not in solution:
            return False, "Solution must contain 'steps' field"

        if not isinstance(solution["steps"], list):
            return False, "'steps' must be a list"

        # Validate each step
        for i, step in enumerate(solution["steps"]):
            if not isinstance(step, dict):
                return False, f"Step {i} must be a dictionary"

            if "action" not in step:
                return False, f"Step {i} missing 'action' field"

            if not isinstance(step["action"], str):
                return False, f"Step {i} 'action' must be a string"

            # Check for valid action types (simplified)
            valid_actions = ["move", "swap", "insert", "delete", "substitute", "reorder"]
            if step["action"] not in valid_actions:
                return False, f"Step {i} has invalid action: {step['action']}"

        # Validate puzzle_id if present
        if "puzzle_id" in solution:
            if not isinstance(solution["puzzle_id"], str):
                return False, "'puzzle_id' must be a string"

        return True, None

    def get_supported_types(self) -> List[str]:
        """Return list of supported constraint types."""
        return list(self.rules.keys())

def main():
    """Main entry point for testing the grammar validator."""
    validator = GrammarValidator()

    # Test constraints
    test_constraints = [
        "x == y",
        "a != b",
        "adjacent(A, B)",
        "x < y",
        "path(start, end)",
        "invalid constraint"
    ]

    print("Testing constraint validation:")
    for c in test_constraints:
        valid, error = validator.validate_constraint(c)
        print(f"  '{c}' -> {valid} ({error})")

    # Test solution validation
    test_solution = {
        "puzzle_id": "test_123",
        "steps": [
            {"action": "move", "target": "A"},
            {"action": "swap", "target": "B"},
            {"action": "move", "target": "C"}
        ]
    }

    valid, error = validator.validate_solution(test_solution)
    print(f"\nSolution validation: {valid} ({error})")

if __name__ == "__main__":
    main()