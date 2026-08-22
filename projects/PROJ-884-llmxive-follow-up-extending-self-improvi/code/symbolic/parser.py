"""
Parser module for converting puzzle constraints into a formal language
parseable by the symbolic planner.

This module implements the transformation from high-level puzzle descriptions
(Sudoku variants, pathfinding constraints) to a formal constraint language
that the planner can reason about.
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from code.exceptions import raise_parse_failure, PARSE_FAILURE
from code.symbolic.exclusion_logger import ExclusionLogger, ExclusionEvent


class FormalConstraintType(Enum):
    """Types of formal constraints supported by the parser."""
    EQUALITY = "equality"
    INEQUALITY = "inequality"
    IN_RANGE = "in_range"
    NOT_EQUAL = "not_equal"
    PATH_CONTINUITY = "path_continuity"
    PATH_START = "path_start"
    PATH_END = "path_end"
    BLOCK_CONSTRAINT = "block_constraint"
    ROW_CONSTRAINT = "row_constraint"
    COL_CONSTRAINT = "col_constraint"
    UNIQUE_VALUE = "unique_value"
    ADJACENCY = "adjacency"
    DISTANCE = "distance"
    IMPLICATION = "implication"
    DISJUNCTION = "disjunction"


@dataclass
class FormalConstraint:
    """A single formal constraint in the planner's language."""
    constraint_type: FormalConstraintType
    variables: List[str]
    value: Optional[Any] = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    operator: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert constraint to dictionary representation."""
        result = {
            "type": self.constraint_type.value,
            "variables": self.variables,
        }
        if self.value is not None:
            result["value"] = self.value
        if self.min_val is not None:
            result["min"] = self.min_val
        if self.max_val is not None:
            result["max"] = self.max_val
        if self.operator is not None:
            result["operator"] = self.operator
        if self.metadata:
            result["metadata"] = self.metadata
        return result


class PuzzleParser:
    """
    Parser for converting puzzle instances into formal constraints.

    This class handles the transformation from high-level puzzle descriptions
    to a formal constraint language that the symbolic planner can process.
    """

    def __init__(self, exclusion_logger: Optional[ExclusionLogger] = None):
        """
        Initialize the parser.

        Args:
            exclusion_logger: Optional logger for exclusion events. If not provided,
                             a default logger will be created.
        """
        self.exclusion_logger = exclusion_logger or ExclusionLogger()
        self._parse_errors: List[str] = []

    def parse_puzzle(self, puzzle_instance: Dict[str, Any]) -> Tuple[List[FormalConstraint], Dict[str, Any]]:
        """
        Parse a puzzle instance into formal constraints.

        Args:
            puzzle_instance: Dictionary containing puzzle data with keys:
                - type: 'sudoku' or 'pathfinding'
                - constraints: List of constraint descriptions
                - initial_state: Initial configuration
                - target_state: Target configuration (if applicable)

        Returns:
            Tuple of (list of FormalConstraint objects, metadata dict)

        Raises:
            PARSE_FAILURE: If parsing fails and fail_loudly is True
        """
        self._parse_errors = []
        puzzle_type = puzzle_instance.get("type", "unknown")
        constraints = puzzle_instance.get("constraints", [])
        initial_state = puzzle_instance.get("initial_state", {})
        target_state = puzzle_instance.get("target_state", {})

        formal_constraints = []
        metadata = {
            "puzzle_type": puzzle_type,
            "num_constraints": len(constraints),
            "has_initial_state": bool(initial_state),
            "has_target_state": bool(target_state),
        }

        try:
            if puzzle_type == "sudoku":
                formal_constraints.extend(self._parse_sudoku_constraints(
                    constraints, initial_state, target_state
                ))
            elif puzzle_type == "pathfinding":
                formal_constraints.extend(self._parse_pathfinding_constraints(
                    constraints, initial_state, target_state
                ))
            else:
                error_msg = f"Unknown puzzle type: {puzzle_type}"
                self._log_exclusion(
                    puzzle_instance.get("id", "unknown"),
                    "PARSE_FAILURE",
                    error_msg,
                    puzzle_instance
                )
                raise_parse_failure(error_msg)

            # Validate that we have at least some constraints
            if not formal_constraints:
                error_msg = "No constraints could be parsed from puzzle instance"
                self._log_exclusion(
                    puzzle_instance.get("id", "unknown"),
                    "PARSE_FAILURE",
                    error_msg,
                    puzzle_instance
                )
                raise_parse_failure(error_msg)

        except Exception as e:
            error_msg = f"Error parsing puzzle: {str(e)}"
            self._log_exclusion(
                puzzle_instance.get("id", "unknown"),
                "PARSE_FAILURE",
                error_msg,
                puzzle_instance
            )
            raise_parse_failure(error_msg)

        return formal_constraints, metadata

    def _parse_sudoku_constraints(
        self,
        constraints: List[Dict[str, Any]],
        initial_state: Dict[str, Any],
        target_state: Dict[str, Any]
    ) -> List[FormalConstraint]:
        """Parse Sudoku-specific constraints."""
        formal_constraints = []
        grid_size = initial_state.get("grid_size", 9)
        grid = initial_state.get("grid", [])

        # Parse fixed values from initial state
        for row_idx, row in enumerate(grid):
            for col_idx, value in enumerate(row):
                if value != 0 and value is not None:
                    var_name = f"cell_{row_idx}_{col_idx}"
                    formal_constraints.append(
                        FormalConstraint(
                            constraint_type=FormalConstraintType.EQUALITY,
                            variables=[var_name],
                            value=value,
                            metadata={"row": row_idx, "col": col_idx}
                        )
                    )

        # Parse row constraints (unique values)
        for row_idx in range(grid_size):
            row_vars = [f"cell_{row_idx}_{col}" for col in range(grid_size)]
            formal_constraints.append(
                FormalConstraint(
                    constraint_type=FormalConstraintType.ROW_CONSTRAINT,
                    variables=row_vars,
                    metadata={"row": row_idx}
                )
            )

        # Parse column constraints (unique values)
        for col_idx in range(grid_size):
            col_vars = [f"cell_{row}_{col_idx}" for row in range(grid_size)]
            formal_constraints.append(
                FormalConstraint(
                    constraint_type=FormalConstraintType.COL_CONSTRAINT,
                    variables=col_vars,
                    metadata={"col": col_idx}
                )
            )

        # Parse block constraints (3x3 subgrids for standard Sudoku)
        block_size = int(grid_size ** 0.5)
        for block_row in range(block_size):
            for block_col in range(block_size):
                block_vars = []
                for row_offset in range(block_size):
                    for col_offset in range(block_size):
                        row = block_row * block_size + row_offset
                        col = block_col * block_size + col_offset
                        block_vars.append(f"cell_{row}_{col}")
                formal_constraints.append(
                    FormalConstraint(
                        constraint_type=FormalConstraintType.BLOCK_CONSTRAINT,
                        variables=block_vars,
                        metadata={"block_row": block_row, "block_col": block_col}
                    )
                )

        # Parse explicit constraints from the constraints list
        for constraint in constraints:
            parsed = self._parse_constraint_description(constraint, "sudoku")
            if parsed:
                formal_constraints.append(parsed)

        return formal_constraints

    def _parse_pathfinding_constraints(
        self,
        constraints: List[Dict[str, Any]],
        initial_state: Dict[str, Any],
        target_state: Dict[str, Any]
    ) -> List[FormalConstraint]:
        """Parse pathfinding-specific constraints."""
        formal_constraints = []
        grid_size = initial_state.get("grid_size", 10)
        start_pos = initial_state.get("start", [0, 0])
        end_pos = target_state.get("end", [grid_size-1, grid_size-1])
        obstacles = initial_state.get("obstacles", [])

        # Parse start position constraint
        formal_constraints.append(
            FormalConstraint(
                constraint_type=FormalConstraintType.PATH_START,
                variables=["current_pos"],
                value=start_pos,
                metadata={"type": "start"}
            )
        )

        # Parse end position constraint
        formal_constraints.append(
            FormalConstraint(
                constraint_type=FormalConstraintType.PATH_END,
                variables=["current_pos"],
                value=end_pos,
                metadata={"type": "end"}
            )
        )

        # Parse obstacle constraints (cannot visit these cells)
        for obstacle in obstacles:
            formal_constraints.append(
                FormalConstraint(
                    constraint_type=FormalConstraintType.INEQUALITY,
                    variables=["current_pos"],
                    value=obstacle,
                    metadata={"type": "obstacle"}
                )
            )

        # Parse path continuity constraint
        formal_constraints.append(
            FormalConstraint(
                constraint_type=FormalConstraintType.PATH_CONTINUITY,
                variables=["prev_pos", "current_pos"],
                metadata={"type": "continuity"}
            )
        )

        # Parse explicit constraints from the constraints list
        for constraint in constraints:
            parsed = self._parse_constraint_description(constraint, "pathfinding")
            if parsed:
                formal_constraints.append(parsed)

        return formal_constraints

    def _parse_constraint_description(
        self,
        constraint: Dict[str, Any],
        puzzle_type: str
    ) -> Optional[FormalConstraint]:
        """Parse a single constraint description into a formal constraint."""
        constraint_type_str = constraint.get("type", "")
        variables = constraint.get("variables", [])
        value = constraint.get("value")
        min_val = constraint.get("min")
        max_val = constraint.get("max")
        operator = constraint.get("operator")

        try:
            constraint_type = FormalConstraintType(constraint_type_str)
        except ValueError:
            # Try to infer from context
            if "equal" in constraint_type_str.lower():
                constraint_type = FormalConstraintType.EQUALITY
            elif "not_equal" in constraint_type_str.lower():
                constraint_type = FormalConstraintType.NOT_EQUAL
            elif "range" in constraint_type_str.lower():
                constraint_type = FormalConstraintType.IN_RANGE
            elif "adjacent" in constraint_type_str.lower():
                constraint_type = FormalConstraintType.ADJACENCY
            elif "distance" in constraint_type_str.lower():
                constraint_type = FormalConstraintType.DISTANCE
            else:
                return None

        return FormalConstraint(
            constraint_type=constraint_type,
            variables=variables,
            value=value,
            min_val=min_val,
            max_val=max_val,
            operator=operator,
            metadata=constraint.get("metadata", {})
        )

    def _log_exclusion(
        self,
        puzzle_id: str,
        error_type: str,
        error_msg: str,
        puzzle_data: Dict[str, Any]
    ) -> None:
        """Log an exclusion event for the parser."""
        event = ExclusionEvent(
            puzzle_id=puzzle_id,
            error_type=error_type,
            error_message=error_msg,
            source_module="parser",
            puzzle_data=puzzle_data
        )
        self.exclusion_logger.log_exclusion(event)

    def parse_constraints_from_file(
        self,
        file_path: str,
        output_path: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parse constraints from a JSON file containing multiple puzzle instances.

        Args:
            file_path: Path to the JSON file containing puzzle instances
            output_path: Optional path to write parsed constraints

        Returns:
            Dictionary mapping puzzle IDs to their formal constraints
        """
        with open(file_path, 'r') as f:
            puzzles = json.load(f)

        if not isinstance(puzzles, list):
            puzzles = [puzzles]

        results = {}
        for puzzle in puzzles:
            puzzle_id = puzzle.get("id", f"puzzle_{len(results)}")
            try:
                constraints, metadata = self.parse_puzzle(puzzle)
                results[puzzle_id] = {
                    "constraints": [c.to_dict() for c in constraints],
                    "metadata": metadata
                }
            except Exception as e:
                results[puzzle_id] = {
                    "error": str(e),
                    "metadata": {"puzzle_type": puzzle.get("type", "unknown")}
                }

        if output_path:
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)

        return results


def main():
    """Main entry point for the parser module."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Parse puzzle constraints into formal language"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input file containing puzzle instances (JSON)"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output file for parsed constraints (JSON)"
    )
    parser.add_argument(
        "--fail-loudly",
        action="store_true",
        help="Fail immediately on parsing errors"
    )

    args = parser.parse_args()

    exclusion_logger = ExclusionLogger()
    puzzle_parser = PuzzleParser(exclusion_logger=exclusion_logger)

    try:
        results = puzzle_parser.parse_constraints_from_file(
            args.input,
            args.output
        )

        # Report summary
        success_count = sum(1 for r in results.values() if "error" not in r)
        error_count = len(results) - success_count

        print(f"Parsed {success_count} puzzles successfully")
        if error_count > 0:
            print(f"Failed to parse {error_count} puzzles")
            for pid, result in results.items():
                if "error" in result:
                    print(f"  {pid}: {result['error']}")

        # Write exclusion log
        exclusion_log_path = Path(args.output).parent / "exclusions.json"
        exclusion_logger.save_to_file(str(exclusion_log_path))

    except Exception as e:
        print(f"Parser failed: {e}")
        if args.fail_loudly:
            raise
        else:
            # Log the error and continue
            exclusion_logger.log_exclusion(
                ExclusionEvent(
                    puzzle_id="global",
                    error_type="PARSE_FAILURE",
                    error_message=str(e),
                    source_module="parser",
                    puzzle_data={}
                )
            )
            exclusion_log_path = Path(args.output).parent / "exclusions.json"
            exclusion_logger.save_to_file(str(exclusion_log_path))
            exit(1)


if __name__ == "__main__":
    main()
