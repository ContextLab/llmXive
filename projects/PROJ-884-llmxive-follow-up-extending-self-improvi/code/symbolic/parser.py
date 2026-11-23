"""
Symbolic parser for puzzle constraints.

This module provides:
- Data structures representing formal constraints.
- A lightweight ``PuzzleParser`` that can turn simple textual
  constraints into ``FormalConstraint`` objects.
- ``parse_dataset_file`` that reads a JSON dataset file and returns a list of puzzle dictionaries (used by the pilot run).
"""

import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from llmxive_toolkit import get_logger

# Import the custom exception raising helper
from code.exceptions import raise_parse_failure

log = get_logger(__name__)

class FormalConstraintType(Enum):
    """Enumeration of supported constraint types."""
    EQUALITY = "equality"            # A = B
    INEQUALITY = "inequality"        # A != B
    VALUE_ASSIGNMENT = "value_assignment"  # A = 5
    ALL_DIFFERENT = "all_different"  # ALLDIFF A B C

@dataclass
class FormalConstraint:
    """A parsed, formal representation of a single constraint."""
    constraint_type: FormalConstraintType
    variables: List[str]
    value: Optional[Any] = None  # Only used for VALUE_ASSIGNMENT

class PuzzleParser:
    """
    Minimal parser that understands a small subset of constraint syntax.

    Supported patterns:
    - Equality:      ``X = Y``
    - Inequality:    ``X != Y``
    - Value assign:  ``X = 5`` (integer or float)
    - All-different: ``ALLDIFF X Y Z`` (case‑insensitive)
    """

    _equality_pat = re.compile(r"^\s*([A-Za-z]\w*)\s*=\s*([A-Za-z]\w*)\s*$")
    _inequality_pat = re.compile(r"^\s*([A-Za-z]\w*)\s*!=\s*([A-Za-z]\w*)\s*$")
    _value_assign_pat = re.compile(r"^\s*([A-Za-z]\w*)\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*$")
    _alldiff_pat = re.compile(r"^\s*ALLDIFF\s+([A-Za-z]\w*(?:\s+[A-Za-z]\w*)+)\s*$", re.IGNORECASE)

    def __init__(self, *args, **kwargs):
        log.debug("PuzzleParser instantiated (real implementation).")

    def parse(self, constraint_str: str) -> FormalConstraint:
        """
        Parse a single constraint string into a ``FormalConstraint``.
        Raises ``ParseFailure`` if the string does not match any supported pattern.
        """
        log.debug(f"Parsing constraint: {constraint_str!r}")

        # Equality (variable = variable)
        m = self._equality_pat.match(constraint_str)
        if m:
            var1, var2 = m.group(1), m.group(2)
            return FormalConstraint(
                constraint_type=FormalConstraintType.EQUALITY,
                variables=[var1, var2]
            )

        # Inequality (variable != variable)
        m = self._inequality_pat.match(constraint_str)
        if m:
            var1, var2 = m.group(1), m.group(2)
            return FormalConstraint(
                constraint_type=FormalConstraintType.INEQUALITY,
                variables=[var1, var2]
            )

        # Value assignment (variable = number)
        m = self._value_assign_pat.match(constraint_str)
        if m:
            var, val_str = m.group(1), m.group(2)
            # Convert to int if possible, else float
            value: Any = int(val_str) if val_str.isdigit() else float(val_str)
            return FormalConstraint(
                constraint_type=FormalConstraintType.VALUE_ASSIGNMENT,
                variables=[var],
                value=value
            )

        # All‑different
        m = self._alldiff_pat.match(constraint_str)
        if m:
            vars_part = m.group(1)
            vars_list = vars_part.split()
            return FormalConstraint(
                constraint_type=FormalConstraintType.ALL_DIFFERENT,
                variables=vars_list
            )

        # If none matched, raise a parse failure
        raise_parse_failure(f"Unable to parse constraint: {constraint_str}")

    def parse_constraints(self, constraints: List[str]) -> List[FormalConstraint]:
        """
        Parse a list of constraint strings.
        Returns a list of ``FormalConstraint`` objects.
        If any constraint cannot be parsed, a ``PARSE_FAILURE`` is raised.
        """
        parsed: List[FormalConstraint] = []
        for c in constraints:
            parsed.append(self.parse(c))
        return parsed

def parse_dataset_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load a JSON dataset file containing puzzle definitions.

    The function expects the file to have a top‑level ``puzzles`` key
    (as produced by the pilot dataset generator).  It returns the list
    of puzzle dictionaries.

    Args:
        file_path: Path to the JSON file.

    Returns:
        List of puzzle dictionaries.
    """
    if not file_path.exists():
        log.error(f"Dataset file not found: {file_path}")
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    log.info(f"Loading puzzle dataset from {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    puzzles = data.get("puzzles")
    if puzzles is None:
        log.error("Dataset JSON does not contain a 'puzzles' field.")
        raise ValueError("Invalid dataset format: missing 'puzzles' key.")

    log.info(f"Loaded {len(puzzles)} puzzles.")
    return puzzles

def main() -> None:
    """
    CLI entry point for manual testing of the parser.

    It loads a dataset file, parses each puzzle's constraints and
    optionally writes the parsed representation to an output JSON file.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Parse puzzle constraints from a dataset")
    parser.add_argument("--input", type=str, required=True, help="Path to input puzzle JSON file")
    parser.add_argument("--output", type=str, default=None, help="Path to write parsed constraints (optional)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    # Load puzzles
    puzzles = parse_dataset_file(Path(args.input))

    puzzle_parser = PuzzleParser()
    results = []

    for puzzle in puzzles:
        puzzle_id = puzzle.get("metadata", {}).get("source_id", "unknown")
        constraints_raw = puzzle.get("constraints", [])
        try:
            formal = puzzle_parser.parse_constraints(constraints_raw)
            # Convert FormalConstraint objects to simple dicts for JSON serialisation
            formal_dicts = [
                {
                    "type": fc.constraint_type.value,
                    "variables": fc.variables,
                    "value": fc.value if hasattr(fc, "value") else None,
                }
                for fc in formal
            ]
            results.append({"puzzle_id": puzzle_id, "parsed_constraints": formal_dicts})
        except Exception as e:
            results.append({"puzzle_id": puzzle_id, "error": str(e)})

    if args.output:
        with open(args.output, "w", encoding="utf-8") as out_f:
            json.dump(results, out_f, indent=2)
        log.info(f"Parsed constraints written to {args.output}")
    else:
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()