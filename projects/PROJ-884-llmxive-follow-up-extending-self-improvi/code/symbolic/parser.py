"""
Symbolic Parser Module for llmXive BES Pipeline.

This module implements the conversion of puzzle constraints into a formal language
parseable by the symbolic planner. It handles parsing of dataset files, validation
of constraint formats, and conversion to internal formal constraint objects.
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from code.exceptions import PARSE_FAILURE, CONTRADICTION_DETECTED, raise_parse_failure, raise_contradiction
from code.utils.logger import log


class FormalConstraintType(Enum):
    """Enumeration of formal constraint types supported by the planner."""
    EQUALITY = "equality"
    INEQUALITY = "inequality"
    EXISTENCE = "existence"
    UNIQUENESS = "uniqueness"
    ORDERING = "ordering"
    PATH = "path"
    BLOCKING = "blocking"
    VALUE_RANGE = "value_range"


@dataclass
class FormalConstraint:
    """
    Represents a formal constraint in the internal representation.

    Attributes:
        constraint_id: Unique identifier for this constraint instance.
        constraint_type: The type of constraint (equality, inequality, etc.).
        operands: List of operands involved in the constraint (variables, values).
        operator: The logical operator used (==, !=, <, >, etc.).
        metadata: Additional metadata for the constraint (source, confidence, etc.).
        raw_text: The original text representation of this constraint.
    """
    constraint_id: str
    constraint_type: FormalConstraintType
    operands: List[Any] = field(default_factory=list)
    operator: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the constraint to a dictionary representation."""
        return {
            "constraint_id": self.constraint_id,
            "constraint_type": self.constraint_type.value,
            "operands": self.operands,
            "operator": self.operator,
            "metadata": self.metadata,
            "raw_text": self.raw_text
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FormalConstraint":
        """Create a FormalConstraint from a dictionary."""
        return cls(
            constraint_id=data["constraint_id"],
            constraint_type=FormalConstraintType(data["constraint_type"]),
            operands=data.get("operands", []),
            operator=data.get("operator"),
            metadata=data.get("metadata", {}),
            raw_text=data.get("raw_text")
        )


class PuzzleParser:
    """
    Parser for converting puzzle instances into formal constraints.

    This class handles the translation of puzzle data (from JSON schema) into
    a formal language that the symbolic planner can understand and process.
    """

    def __init__(self, constraint_id_prefix: str = "C"):
        """
        Initialize the parser.

        Args:
            constraint_id_prefix: Prefix for generated constraint IDs.
        """
        self.constraint_id_prefix = constraint_id_prefix
        self.constraint_counter = 0
        self._log = log

    def _generate_constraint_id(self) -> str:
        """Generate a unique constraint ID."""
        self.constraint_counter += 1
        return f"{self.constraint_id_prefix}_{self.constraint_counter:04d}"

    def parse_puzzle_constraints(self, puzzle_instance: Dict[str, Any]) -> List[FormalConstraint]:
        """
        Parse constraints from a single puzzle instance.

        Args:
            puzzle_instance: A dictionary representing a puzzle instance
                             with constraints, initial state, and target state.

        Returns:
            A list of FormalConstraint objects representing the parsed constraints.

        Raises:
            PARSE_FAILURE: If the puzzle instance cannot be parsed.
            CONTRADICTION_DETECTED: If contradictory constraints are detected.
        """
        if not isinstance(puzzle_instance, dict):
            raise_parse_failure("Puzzle instance must be a dictionary")

        constraints = []
        raw_constraints = puzzle_instance.get("constraints", [])

        if not isinstance(raw_constraints, list):
            raise_parse_failure("Constraints field must be a list")

        for idx, raw_constraint in enumerate(raw_constraints):
            try:
                constraint = self._parse_single_constraint(raw_constraint, idx)
                if constraint:
                    constraints.append(constraint)
            except (PARSE_FAILURE, CONTRADICTION_DETECTED):
                raise
            except Exception as e:
                raise_parse_failure(f"Failed to parse constraint {idx}: {str(e)}")

        # Validate for contradictions
        self._validate_constraint_set(constraints)

        return constraints

    def _parse_single_constraint(self, raw_constraint: Any, index: int) -> Optional[FormalConstraint]:
        """
        Parse a single constraint from raw data.

        Args:
            raw_constraint: The raw constraint data (dict or string).
            index: The index of the constraint in the list.

        Returns:
            A FormalConstraint object or None if the constraint is empty.
        """
        if isinstance(raw_constraint, str):
            return self._parse_string_constraint(raw_constraint, index)
        elif isinstance(raw_constraint, dict):
            return self._parse_dict_constraint(raw_constraint, index)
        else:
            raise_parse_failure(f"Constraint at index {index} must be string or dict, got {type(raw_constraint)}")

    def _parse_string_constraint(self, constraint_str: str, index: int) -> FormalConstraint:
        """
        Parse a constraint from a string representation.

        Supports formats like:
        - "A == B"
        - "X > 5"
        - "path_from_start_to_end"
        - "unique_row_1"
        """
        constraint_str = constraint_str.strip()
        if not constraint_str:
            raise_parse_failure(f"Empty constraint string at index {index}")

        # Pattern matching for different constraint types
        patterns = {
            FormalConstraintType.EQUALITY: r"(\w+)\s*==\s*(\w+)",
            FormalConstraintType.INEQUALITY: r"(\w+)\s*(!=|<|>|<=|>=)\s*(\w+)",
            FormalConstraintType.VALUE_RANGE: r"(\w+)\s*in\s*\(([^)]+)\)",
            FormalConstraintType.ORDERING: r"(\w+)\s*<\s*(\w+)",  # Overlaps with inequality
        }

        # Check for path constraint
        if constraint_str.startswith("path_"):
            parts = constraint_str.split("_")
            if len(parts) >= 3:
                return FormalConstraint(
                    constraint_id=self._generate_constraint_id(),
                    constraint_type=FormalConstraintType.PATH,
                    operands=parts[1:],
                    operator="path",
                    raw_text=constraint_str
                )

        # Check for uniqueness constraint
        if constraint_str.startswith("unique_"):
            parts = constraint_str.split("_")
            if len(parts) >= 2:
                return FormalConstraint(
                    constraint_id=self._generate_constraint_id(),
                    constraint_type=FormalConstraintType.UNIQUENESS,
                    operands=parts[1:],
                    operator="unique",
                    raw_text=constraint_str
                )

        # Try pattern matching
        for ctype, pattern in patterns.items():
            match = re.match(pattern, constraint_str)
            if match:
                groups = match.groups()
                operator = "==" if ctype == FormalConstraintType.EQUALITY else (groups[1] if len(groups) > 1 else None)
                return FormalConstraint(
                    constraint_id=self._generate_constraint_id(),
                    constraint_type=ctype,
                    operands=list(groups),
                    operator=operator,
                    raw_text=constraint_str
                )

        raise_parse_failure(f"Could not parse constraint string: {constraint_str}")

    def _parse_dict_constraint(self, constraint_dict: Dict[str, Any], index: int) -> FormalConstraint:
        """
        Parse a constraint from a dictionary representation.

        Expected format:
        {
            "type": "equality",
            "operands": ["A", "B"],
            "operator": "==",
            "metadata": {...}
        }
        """
        required_fields = ["type", "operands"]
        for field_name in required_fields:
            if field_name not in constraint_dict:
                raise_parse_failure(f"Constraint at index {index} missing required field: {field_name}")

        try:
            ctype = FormalConstraintType(constraint_dict["type"])
        except ValueError:
            raise_parse_failure(f"Unknown constraint type: {constraint_dict['type']}")

        operands = constraint_dict["operands"]
        if not isinstance(operands, list) or len(operands) < 2:
            raise_parse_failure(f"Constraint operands must be a list with at least 2 elements")

        return FormalConstraint(
            constraint_id=self._generate_constraint_id(),
            constraint_type=ctype,
            operands=operands,
            operator=constraint_dict.get("operator"),
            metadata=constraint_dict.get("metadata", {}),
            raw_text=json.dumps(constraint_dict)
        )

    def _validate_constraint_set(self, constraints: List[FormalConstraint]) -> None:
        """
        Validate a set of constraints for contradictions.

        Args:
            constraints: List of constraints to validate.

        Raises:
            CONTRADICTION_DETECTED: If contradictory constraints are found.
        """
        # Simple contradiction detection for equality constraints
        equality_pairs = {}
        for constraint in constraints:
            if constraint.constraint_type == FormalConstraintType.EQUALITY:
                if len(constraint.operands) >= 2:
                    a, b = constraint.operands[0], constraint.operands[1]
                    # Normalize pair order
                    pair = tuple(sorted([a, b]))
                    if pair in equality_pairs:
                        # Already have this equality, skip
                        pass
                    else:
                        equality_pairs[pair] = constraint

            elif constraint.constraint_type == FormalConstraintType.INEQUALITY:
                if len(constraint.operands) >= 2:
                    a, b = constraint.operands[0], constraint.operands[1]
                    if constraint.operator == "!=":
                        pair = tuple(sorted([a, b]))
                        if pair in equality_pairs:
                            raise_contradiction(
                                f"Contradiction: {a} == {b} and {a} != {b} detected"
                            )

        # Additional validation logic can be added here for more complex contradictions

    def parse_dataset_file(self, dataset_path: Path) -> List[FormalConstraint]:
        """
        Parse all constraints from a dataset file.

        Args:
            dataset_path: Path to the JSON dataset file.

        Returns:
            A flat list of all FormalConstraint objects from all puzzles in the file.

        Raises:
            PARSE_FAILURE: If the file cannot be read or parsed.
        """
        if not dataset_path.exists():
            raise_parse_failure(f"Dataset file not found: {dataset_path}")

        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise_parse_failure(f"Invalid JSON in dataset file: {str(e)}")
        except Exception as e:
            raise_parse_failure(f"Failed to read dataset file: {str(e)}")

        all_constraints = []

        if isinstance(data, list):
            puzzles = data
        elif isinstance(data, dict) and "puzzles" in data:
            puzzles = data["puzzles"]
        else:
            raise_parse_failure("Dataset must be a list of puzzles or a dict with 'puzzles' key")

        for idx, puzzle in enumerate(puzzles):
            try:
                puzzle_constraints = self.parse_puzzle_constraints(puzzle)
                all_constraints.extend(puzzle_constraints)
                log(f"Parsed {len(puzzle_constraints)} constraints from puzzle {idx}")
            except (PARSE_FAILURE, CONTRADICTION_DETECTED) as e:
                log(f"Warning: Failed to parse puzzle {idx}: {str(e)}")
                # Continue with other puzzles rather than failing the entire dataset

        return all_constraints


def parse_dataset_file(dataset_path: str | Path) -> List[FormalConstraint]:
    """
    Convenience function to parse a dataset file.

    Args:
        dataset_path: Path to the dataset file.

    Returns:
        List of FormalConstraint objects.
    """
    parser = PuzzleParser()
    return parser.parse_dataset_file(Path(dataset_path))


def main():
    """
    Main entry point for testing the parser.

    This function demonstrates the parser by loading a sample dataset
    and printing the parsed constraints.
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m code.symbolic.parser <dataset_path>")
        sys.exit(1)

    dataset_path = Path(sys.argv[1])

    if not dataset_path.exists():
        print(f"Error: Dataset file not found: {dataset_path}")
        sys.exit(1)

    try:
        parser = PuzzleParser()
        constraints = parser.parse_dataset_file(dataset_path)

        print(f"Successfully parsed {len(constraints)} constraints:")
        for constraint in constraints:
            print(f"  {constraint.constraint_id}: {constraint.constraint_type.value} "
                  f"{constraint.operands} {constraint.operator}")

    except PARSE_FAILURE as e:
        print(f"Parse failure: {str(e)}")
        sys.exit(1)
    except CONTRADICTION_DETECTED as e:
        print(f"Contradiction detected: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()