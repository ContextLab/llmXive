"""
code/symbolic/parser.py

Implements the formal language parser to convert puzzle constraints into a
structure parseable by the symbolic planner.

This module defines the grammar for constraints (equality, inequality, adjacency,
etc.) and provides the `PuzzleParser` class to validate and transform raw puzzle
data into formal `FormalConstraint` objects.
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import logging

from code.exceptions import PARSE_FAILURE, raise_parse_failure
from code.symbolic.exclusion_logger import ExclusionLogger, ExclusionEvent

# Configure logging
logger = logging.getLogger(__name__)


class FormalConstraintType(Enum):
    """Enumeration of supported formal constraint types."""
    EQUALITY = "equality"
    INEQUALITY = "inequality"
    ADJACENCY = "adjacency"
    RANGE = "range"
    UNIQUE = "unique"
    EXISTENCE = "existence"
    IMPLICATION = "implication"
    NEGATION = "negation"


@dataclass
class FormalConstraint:
    """
    Represents a parsed formal constraint.

    Attributes:
        type: The type of constraint (e.g., equality, inequality).
        variables: List of variable names involved in the constraint.
        value: The target value or comparison value (optional).
        operator: The comparison operator (e.g., '==', '!=', '<', '>', 'adj').
        metadata: Additional context or parameters for the constraint.
    """
    type: FormalConstraintType
    variables: List[str] = field(default_factory=list)
    value: Optional[Any] = None
    operator: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the constraint to a dictionary for serialization."""
        return {
            "type": self.type.value,
            "variables": self.variables,
            "value": self.value,
            "operator": self.operator,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FormalConstraint":
        """Create a FormalConstraint from a dictionary."""
        return cls(
            type=FormalConstraintType(data["type"]),
            variables=data.get("variables", []),
            value=data.get("value"),
            operator=data.get("operator"),
            metadata=data.get("metadata", {})
        )


class PuzzleParser:
    """
    Parses raw puzzle constraints into formal language structures.

    This class validates constraints against a defined grammar and transforms
    them into `FormalConstraint` objects that the `SymbolicPlanner` can process.
    """

    def __init__(self, exclusion_logger: Optional[ExclusionLogger] = None):
        """
        Initialize the parser.

        Args:
            exclusion_logger: An optional ExclusionLogger instance to log parsing failures.
        """
        self.exclusion_logger = exclusion_logger
        self._compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for constraint parsing."""
        patterns = {
            "variable": re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$'),
            "number": re.compile(r'^-?\d+(\.\d+)?$'),
            "string_literal": re.compile(r'^"[^"]*"$'),
            "comparison_op": re.compile(r'^(==|!=|<=|>=|<|>|adj)$'),
            "range_op": re.compile(r'^(in|between)$'),
        }
        return patterns

    def _validate_variable_name(self, name: str) -> bool:
        """Validate a variable name against the grammar."""
        if not name:
            return False
        return bool(self._compiled_patterns["variable"].match(name))

    def _validate_value(self, value: Any, expected_type: str = "any") -> bool:
        """Validate a constraint value."""
        if expected_type == "number":
            return bool(self._compiled_patterns["number"].match(str(value)))
        if expected_type == "string":
            return bool(self._compiled_patterns["string_literal"].match(str(value)))
        return True

    def _parse_single_constraint(self, constraint_def: Dict[str, Any]) -> FormalConstraint:
        """
        Parse a single constraint definition into a FormalConstraint.

        Args:
            constraint_def: Dictionary containing constraint details.

        Returns:
            A FormalConstraint object.

        Raises:
            PARSE_FAILURE: If the constraint cannot be parsed.
        """
        constraint_type_str = constraint_def.get("type")
        if not constraint_type_str:
            raise_parse_failure("Missing constraint type", constraint_def)

        try:
            constraint_type = FormalConstraintType(constraint_type_str)
        except ValueError:
            raise_parse_failure(f"Unknown constraint type: {constraint_type_str}", constraint_def)

        variables = constraint_def.get("variables", [])
        if not isinstance(variables, list):
            variables = [variables]

        # Validate variables
        for var in variables:
            if not self._validate_variable_name(var):
                raise_parse_failure(f"Invalid variable name: {var}", constraint_def)

        value = constraint_def.get("value")
        operator = constraint_def.get("operator")

        # Validate operator based on type
        if constraint_type in [FormalConstraintType.EQUALITY, FormalConstraintType.INEQUALITY]:
            if not operator or not self._compiled_patterns["comparison_op"].match(operator):
                raise_parse_failure(f"Invalid operator for {constraint_type.value}: {operator}", constraint_def)

        return FormalConstraint(
            type=constraint_type,
            variables=variables,
            value=value,
            operator=operator,
            metadata=constraint_def.get("metadata", {})
        )

    def parse_constraints(self, constraints: List[Dict[str, Any]]) -> List[FormalConstraint]:
        """
        Parse a list of raw constraints into formal constraints.

        Args:
            constraints: List of constraint dictionaries.

        Returns:
            List of FormalConstraint objects.

        Raises:
            PARSE_FAILURE: If any constraint fails to parse and no logger is available.
        """
        formal_constraints = []
        failed_count = 0

        for i, constraint_def in enumerate(constraints):
            try:
                parsed = self._parse_single_constraint(constraint_def)
                formal_constraints.append(parsed)
            except PARSE_FAILURE as e:
                failed_count += 1
                error_msg = str(e)
                logger.warning(f"Failed to parse constraint at index {i}: {error_msg}")

                if self.exclusion_logger:
                    event = ExclusionEvent(
                        reason="PARSE_FAILURE",
                        details={"constraint_index": i, "error": error_msg, "raw_constraint": constraint_def},
                        timestamp=datetime.now().isoformat()
                    )
                    self.exclusion_logger.log(event)

        if failed_count == len(constraints) and not formal_constraints:
            raise_parse_failure("All constraints failed to parse", constraints)

        return formal_constraints

    def parse_puzzle(self, puzzle_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a complete puzzle instance.

        Args:
            puzzle_data: Dictionary containing puzzle details including constraints.

        Returns:
            Dictionary with parsed puzzle structure.
        """
        constraints_raw = puzzle_data.get("constraints", [])
        if not isinstance(constraints_raw, list):
            raise_parse_failure("Constraints must be a list", puzzle_data)

        parsed_constraints = self.parse_constraints(constraints_raw)

        return {
            "id": puzzle_data.get("id"),
            "initial_state": puzzle_data.get("initial_state"),
            "target_state": puzzle_data.get("target_state"),
            "constraints": [c.to_dict() for c in parsed_constraints],
            "metadata": puzzle_data.get("metadata", {}),
            "parsing_status": "success"
        }


def main():
    """
    Command-line interface for testing the parser.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Test the Puzzle Parser")
    parser.add_argument("--input", type=str, required=True, help="Path to JSON file with puzzle data")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Load input data
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    with open(input_path, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in input file: {e}")
            sys.exit(1)

    # Initialize parser and exclusion logger
    exclusion_logger = ExclusionLogger(output_path=Path("data/processed/exclusions.json"))
    puzzle_parser = PuzzleParser(exclusion_logger=exclusion_logger)

    # Parse
    try:
        if isinstance(data, list):
            results = [puzzle_parser.parse_puzzle(p) for p in data]
        else:
            results = [puzzle_parser.parse_puzzle(data)]

        # Save output
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Successfully parsed {len(results)} puzzle(s). Output saved to {output_path}")

        # Log exclusions if any
        exclusion_logger.flush()
        logger.info(f"Exclusion log saved to {exclusion_logger.output_path}")

    except PARSE_FAILURE as e:
        logger.error(f"Parsing failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()