"""
Symbolic Parser Module for BES Pipeline.

Parses puzzle constraints into a formal language for the symbolic planner.
Implements robust handling for non-linear or too-complex constraints.
"""
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

import sys
import os

# Add project root to path for imports if running as script
if __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from exceptions import PARSE_FAILURE, raise_parse_failure
else:
    from code.exceptions import PARSE_FAILURE, raise_parse_failure

@dataclass
class FormalConstraintType(Enum):
    """Enumeration of supported constraint types."""
    LINEAR = "linear"
    BOUNDARY = "boundary"
    CONNECTIVITY = "connectivity"
    SEQUENCE = "sequence"
    EXCLUSION = "exclusion"
    COMPLEX = "complex"  # Represents constraints too complex for direct decomposition

@dataclass
class FormalConstraint:
    """Represents a parsed formal constraint."""
    constraint_type: FormalConstraintType
    raw_text: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    is_decomposable: bool = True
    complexity_score: float = 0.0

class PuzzleParser:
    """
    Parses puzzle constraints from raw data into formal constraints.

    Implements logic to detect non-linear or overly complex constraints
    that cannot be decomposed by the symbolic planner, raising PARSE_FAILURE
    and logging exclusions as required by T043.
    """

    # Thresholds for complexity detection
    MAX_DEPTH_THRESHOLD = 5
    MAX_BRANCH_FACTOR = 4
    NON_LINEAR_PATTERNS = [
        r"if.*else.*if",  # Nested conditionals
        r"while.*for",    # Nested loops
        r"recursive",     # Explicit recursion keywords
        r"backtrack.*depth.*>\d+", # Deep backtracking
    ]

    def __init__(self, exclusion_logger_path: Optional[Path] = None):
        """
        Initialize the parser.

        Args:
            exclusion_logger_path: Path to the exclusion logger file.
        """
        self.exclusion_logger_path = exclusion_logger_path
        self._exclusion_logger = None
        if exclusion_logger_path:
            self._load_exclusion_logger()

    def _load_exclusion_logger(self):
        """Lazy load the exclusion logger module."""
        try:
            # Dynamically import to avoid circular dependency issues if any
            from code.symbolic.exclusion_logger import ExclusionLogger
            self._exclusion_logger = ExclusionLogger(self.exclusion_logger_path)
        except ImportError as e:
            # Fallback if module not yet available, but log warning
            print(f"Warning: Could not load ExclusionLogger: {e}")

    def _log_exclusion(self, puzzle_id: str, reason: str, details: str = ""):
        """Log an exclusion event if the logger is available."""
        if self._exclusion_logger:
            self._exclusion_logger.log_exclusion(
                puzzle_id=puzzle_id,
                reason_code=reason,
                details=details
            )
        else:
            # If logger isn't loaded, we still raise the exception to fail loudly
            # as per T043 requirements.
            pass

    def _detect_non_linear(self, constraint_text: str) -> bool:
        """
        Detect if a constraint is non-linear or too complex.

        Checks for patterns indicative of non-linear dependencies,
        deep nesting, or recursive structures that the planner cannot handle.
        """
        # Check for explicit non-linear patterns
        for pattern in self.NON_LINEAR_PATTERNS:
            if re.search(pattern, constraint_text, re.IGNORECASE):
                return True

        # Heuristic: Count nesting depth (simplified)
        # Count occurrences of 'if', 'while', 'for' and check for nesting
        nesting_score = 0
        current_depth = 0
        for char in constraint_text:
            if char == '(':
                current_depth += 1
            elif char == ')':
                current_depth = max(0, current_depth - 1)
            if current_depth > self.MAX_DEPTH_THRESHOLD:
                return True

        # Check for complex logical operators that imply non-linearity
        if "and" in constraint_text and "or" in constraint_text:
            # Complex boolean logic often implies non-linear dependencies
            if constraint_text.count("and") > 3 or constraint_text.count("or") > 3:
                return True

        return False

    def _calculate_complexity(self, constraint_text: str) -> float:
        """
        Estimate the complexity score of a constraint.

        Returns a float representing the estimated difficulty of decomposition.
        """
        score = 1.0
        # Length factor
        score += len(constraint_text) / 100.0
        # Operator count
        score += constraint_text.count("and") * 0.5
        score += constraint_text.count("or") * 0.5
        score += constraint_text.count("not") * 0.2
        # Nesting depth
        depth = 0
        max_depth = 0
        for char in constraint_text:
            if char == '(':
                depth += 1
                max_depth = max(max_depth, depth)
            elif char == ')':
                depth = max(0, depth - 1)
        score += max_depth * 2.0

        return score

    def parse_constraint(self, constraint_text: str, puzzle_id: str) -> FormalConstraint:
        """
        Parse a single constraint string into a FormalConstraint.

        Args:
            constraint_text: The raw constraint text.
            puzzle_id: The ID of the puzzle for logging purposes.

        Returns:
            A FormalConstraint object.

        Raises:
            PARSE_FAILURE: If the constraint is non-linear or too complex.
        """
        if not constraint_text or not isinstance(constraint_text, str):
            raise_parse_failure(f"Invalid constraint text: {constraint_text}", puzzle_id)

        # Check for non-linear or too complex constraints
        if self._detect_non_linear(constraint_text):
            reason = "NON_LINEAR_CONSTRAINT"
            details = f"Constraint detected as non-linear or too complex: {constraint_text[:100]}..."
            self._log_exclusion(puzzle_id, reason, details)
            raise_parse_failure(
                f"Constraint is non-linear or too complex to decompose: {constraint_text}",
                puzzle_id,
                reason_code=reason
            )

        complexity = self._calculate_complexity(constraint_text)

        # Determine constraint type based on keywords
        constraint_type = FormalConstraintType.COMPLEX
        if "boundary" in constraint_text.lower():
            constraint_type = FormalConstraintType.BOUNDARY
        elif "connect" in constraint_text.lower() or "path" in constraint_text.lower():
            constraint_type = FormalConstraintType.CONNECTIVITY
        elif "sequence" in constraint_text.lower() or "order" in constraint_text.lower():
            constraint_type = FormalConstraintType.SEQUENCE
        elif "not" in constraint_text.lower() and "equal" in constraint_text.lower():
            constraint_type = FormalConstraintType.EXCLUSION
        elif complexity < 3.0:
            constraint_type = FormalConstraintType.LINEAR
        else:
            # If complexity is high but not explicitly non-linear, flag as complex
            # but still attempt to parse (decomposable=False)
            constraint_type = FormalConstraintType.COMPLEX

        is_decomposable = constraint_type != FormalConstraintType.COMPLEX or complexity < 5.0

        if not is_decomposable:
            reason = "TOO_COMPLEX"
            details = f"Constraint complexity score {complexity} exceeds threshold for decomposition."
            self._log_exclusion(puzzle_id, reason, details)
            raise_parse_failure(
                f"Constraint is too complex to decompose (score: {complexity}): {constraint_text}",
                puzzle_id,
                reason_code=reason
            )

        return FormalConstraint(
            constraint_type=constraint_type,
            raw_text=constraint_text,
            parameters={"puzzle_id": puzzle_id, "complexity": complexity},
            is_decomposable=is_decomposable,
            complexity_score=complexity
        )

    def parse_dataset_file(self, dataset_path: Path) -> List[FormalConstraint]:
        """
        Parse a dataset file containing multiple puzzle constraints.

        Args:
            dataset_path: Path to the JSON dataset file.

        Returns:
            A list of FormalConstraint objects.

        Raises:
            PARSE_FAILURE: If any constraint in the dataset is non-linear or too complex.
        """
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

        with open(dataset_path, 'r') as f:
            data = json.load(f)

        constraints = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and "puzzles" in data:
            items = data["puzzles"]
        else:
            raise_parse_failure("Invalid dataset format: expected list or dict with 'puzzles' key", "unknown")

        for item in items:
            puzzle_id = item.get("id", "unknown")
            if "constraints" in item:
                for constraint_text in item["constraints"]:
                    parsed = self.parse_constraint(constraint_text, puzzle_id)
                    constraints.append(parsed)
            elif "constraint" in item:
                parsed = self.parse_constraint(item["constraint"], puzzle_id)
                constraints.append(parsed)

        return constraints


def main():
    """Main entry point for testing the parser."""
    import argparse

    parser = argparse.ArgumentParser(description="Parse puzzle constraints")
    parser.add_argument("--input", type=str, required=True, help="Path to input dataset JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON file")
    parser.add_argument("--exclusion-log", type=str, default=None, help="Path to exclusion log file")

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    exclusion_path = Path(args.exclusion_log) if args.exclusion_log else None

    try:
        puzzle_parser = PuzzleParser(exclusion_logger_path=exclusion_path)
        constraints = puzzle_parser.parse_dataset_file(input_path)

        output_data = {
            "parsed_constraints": [
                {
                    "type": c.constraint_type.value,
                    "raw": c.raw_text,
                    "decomposable": c.is_decomposable,
                    "complexity": c.complexity_score
                }
                for c in constraints
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"Successfully parsed {len(constraints)} constraints to {output_path}")

    except PARSE_FAILURE as e:
        print(f"Parse failure: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
