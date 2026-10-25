"""
Puzzle Verifier Module for llmXive
Validates puzzle instances and solutions with deterministic logic.
Implements T066: Data Provenance metadata validation.
Updated to expose a tuple‑based API that conforms to the dataset schema.
Additionally records verification timing to a log file.
"""

import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path

# llmxive toolkit for path handling
from llmxive_toolkit import paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ErrorCodes(Enum):
    """Error codes for verification failures (internal representation)."""
    VALID = "VALID"
    INVALID_SOLUTION = "INVALID_SOLUTION"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"
    DUPLICATE_ROW = "DUPLICATE_ROW"
    INVALID_PATH = "INVALID_PATH"
    MISSING_METADATA = "MISSING_METADATA"
    PARSE_FAILURE = "PARSE_FAILURE"
    VERIFIER_ERROR = "VERIFIER_ERROR"
    TIMEOUT = "TIMEOUT"
    CONTRADICTION_DETECTED = "CONTRADICTION_DETECTED"

class VerifierError(Exception):
    """Raised for unexpected internal verification failures."""
    pass

# Alias used by legacy tests
class DataVerificationError(VerifierError):
    """Compatibility alias for older test suites."""
    pass

@dataclass
class SolutionResult:
    """Result of solution verification."""
    is_valid: bool
    error_code: Optional[ErrorCodes] = None
    error_message: Optional[str] = None
    verification_time_ms: Optional[float] = None

class PuzzleVerifier:
    """
    Validates puzzle instances and solutions.
    Implements T066: Validates provenance metadata before processing.
    """

    # Schema‑compatible error codes (the allowed enum in contracts/dataset.schema.yaml)
    _SCHEMA_ERROR_CODES = {
        "NONE",
        "DUPLICATE_ROW",
        "INVALID_PATH",
        "CONSTRAINT_VIOLATION",
        "PARSE_FAILURE",
        "CONTRADICTION_DETECTED",
        "VERIFIER_ERROR",
    }

    def __init__(self, timeout_ms: int = 100):
        self.timeout_ms = timeout_ms
        self.logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Metadata validation (shared)
    # ------------------------------------------------------------------
    def validate_metadata(self, puzzle_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that puzzle instance has required provenance metadata.
        Returns (is_valid, error_message).
        """
        required_fields = [
            "source_id",
            "generation_seed",
            "timestamp",
            "generator_version"
        ]

        if "metadata" not in puzzle_data:
            return False, "Missing metadata field"

        metadata = puzzle_data["metadata"]

        for field_name in required_fields:
            if field_name not in metadata:
                return False, f"Missing metadata field: {field_name}"

        # Validate complexity_metric
        if "complexity_metric" not in metadata:
            return False, "Missing complexity_metric in metadata"

        complexity = metadata["complexity_metric"]
        if "constraint_count" not in complexity:
            return False, "Missing constraint_count in complexity_metric"
        if "variable_domain_size" not in complexity:
            return False, "Missing variable_domain_size in complexity_metric"

        return True, None

    # ------------------------------------------------------------------
    # Helper: map internal ErrorCodes to schema‑compatible strings
    # ------------------------------------------------------------------
    def _map_error_code(self, code: Optional[ErrorCodes]) -> str:
        """
        Convert an internal ErrorCodes value to a string that is allowed by the
        dataset schema. Unknown or None values become 'VERIFIER_ERROR'.
        """
        if code is None:
            return "NONE"
        if code == ErrorCodes.VALID:
            return "NONE"
        # Direct mapping for codes that already match the schema
        if code.value in self._SCHEMA_ERROR_CODES:
            return code.value
        # Map internal codes that are not part of the schema to a generic one
        if code in {
            ErrorCodes.INVALID_SOLUTION,
            ErrorCodes.MISSING_METADATA,
            ErrorCodes.TIMEOUT,
        }:
            return "VERIFIER_ERROR"
        # Fallback – should never happen but keeps the function total
        return "VERIFIER_ERROR"

    # ------------------------------------------------------------------
    # Sudoku verification
    # ------------------------------------------------------------------
    def verify_sudoku(
        self,
        puzzle_instance: Dict[str, Any],
        solution: Dict[str, Any]
    ) -> SolutionResult:
        start_time = time.time()
        try:
            # Metadata check
            is_valid, err_msg = self.validate_metadata(puzzle_instance)
            if not is_valid:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.MISSING_METADATA,
                    error_message=err_msg,
                    verification_time_ms=(time.time() - start_time) * 1000
                )

            grid_size = puzzle_instance["initial_state"]["size"]
            solution_grid = solution["solution"]

            # Basic shape checks
            if len(solution_grid) != grid_size:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.INVALID_SOLUTION,
                    error_message=f"Grid size mismatch: expected {grid_size}",
                    verification_time_ms=(time.time() - start_time) * 1000
                )

            # Row checks
            for row_idx, row in enumerate(solution_grid):
                if len(row) != grid_size:
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.INVALID_SOLUTION,
                        error_message=f"Row {row_idx} length mismatch",
                        verification_time_ms=(time.time() - start_time) * 1000
                    )
                if sorted(row) != list(range(1, grid_size + 1)):
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.DUPLICATE_ROW,
                        error_message=f"Row {row_idx} contains duplicates",
                        verification_time_ms=(time.time() - start_time) * 1000
                    )

            # Column checks
            for col_idx in range(grid_size):
                column = [solution_grid[r][col_idx] for r in range(grid_size)]
                if sorted(column) != list(range(1, grid_size + 1)):
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.DUPLICATE_ROW,
                        error_message=f"Column {col_idx} contains duplicates",
                        verification_time_ms=(time.time() - start_time) * 1000
                    )

            # Box checks
            box_size = int(grid_size ** 0.5)
            for box_row in range(0, grid_size, box_size):
                for box_col in range(0, grid_size, box_size):
                    box_vals = []
                    for r in range(box_row, box_row + box_size):
                        for c in range(box_col, box_col + box_size):
                            box_vals.append(solution_grid[r][c])
                    if sorted(box_vals) != list(range(1, grid_size + 1)):
                        return SolutionResult(
                            is_valid=False,
                            error_code=ErrorCodes.CONSTRAINT_VIOLATION,
                            error_message=f"Box ({box_row},{box_col}) invalid",
                            verification_time_ms=(time.time() - start_time) * 1000
                        )

            return SolutionResult(
                is_valid=True,
                verification_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            self.logger.error(f"Sudoku verification error: {e}")
            raise VerifierError(str(e))

    # ------------------------------------------------------------------
    # Pathfinding verification
    # ------------------------------------------------------------------
    def verify_pathfinding(
        self,
        puzzle_instance: Dict[str, Any],
        solution: Dict[str, Any]
    ) -> SolutionResult:
        start_time = time.time()
        try:
            is_valid, err_msg = self.validate_metadata(puzzle_instance)
            if not is_valid:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.MISSING_METADATA,
                    error_message=err_msg,
                    verification_time_ms=(time.time() - start_time) * 1000
                )

            grid_size = puzzle_instance["initial_state"]["size"]
            start = tuple(puzzle_instance["initial_state"]["start"])
            end = tuple(puzzle_instance["initial_state"]["end"])
            obstacles = {
                tuple(o) for o in puzzle_instance["initial_state"]["obstacles"]
            }
            path = [tuple(p) for p in solution["path"]]

            if not path:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.INVALID_PATH,
                    error_message="Empty path",
                    verification_time_ms=(time.time() - start_time) * 1000
                )
            if path[0] != start:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.INVALID_PATH,
                    error_message="Path does not start at the defined start",
                    verification_time_ms=(time.time() - start_time) * 1000
                )
            if path[-1] != end:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.INVALID_PATH,
                    error_message="Path does not end at the defined end",
                    verification_time_ms=(time.time() - start_time) * 1000
                )

            for i, (r, c) in enumerate(path):
                if not (0 <= r < grid_size and 0 <= c < grid_size):
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.INVALID_PATH,
                        error_message=f"Out‑of‑bounds at step {i}",
                        verification_time_ms=(time.time() - start_time) * 1000
                    )
                if (r, c) in obstacles:
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.INVALID_PATH,
                        error_message=f"Obstacle hit at step {i}",
                        verification_time_ms=(time.time() - start_time) * 1000
                    )
                if i > 0:
                    prev = path[i - 1]
                    if abs(r - prev[0]) + abs(c - prev[1]) != 1:
                        return SolutionResult(
                            is_valid=False,
                            error_code=ErrorCodes.INVALID_PATH,
                            error_message=f"Non‑adjacent move at step {i}",
                            verification_time_ms=(time.time() - start_time) * 1000
                        )

            return SolutionResult(
                is_valid=True,
                verification_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            self.logger.error(f"Pathfinding verification error: {e}")
            raise VerifierError(str(e))

    # ------------------------------------------------------------------
    # Logic grid verification (structure only)
    # ------------------------------------------------------------------
    def verify_logic_grid(
        self,
        puzzle_instance: Dict[str, Any],
        solution: Dict[str, Any]
    ) -> SolutionResult:
        start_time = time.time()
        try:
            is_valid, err_msg = self.validate_metadata(puzzle_instance)
            if not is_valid:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.MISSING_METADATA,
                    error_message=err_msg,
                    verification_time_ms=(time.time() - start_time) * 1000
                )

            categories = puzzle_instance["initial_state"]["categories"]
            solution_data = solution["solution"]

            if not isinstance(solution_data, dict):
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.INVALID_SOLUTION,
                    error_message="Solution must be a dict",
                    verification_time_ms=(time.time() - start_time) * 1000
                )

            for cat in categories:
                if cat not in solution_data:
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.INVALID_SOLUTION,
                        error_message=f"Missing category {cat}",
                        verification_time_ms=(time.time() - start_time) * 1000
                    )
            return SolutionResult(
                is_valid=True,
                verification_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            self.logger.error(f"Logic grid verification error: {e}")
            raise VerifierError(str(e))

    # ------------------------------------------------------------------
    # Arithmetic verification
    # ------------------------------------------------------------------
    def verify_arithmetic(
        self,
        puzzle_instance: Dict[str, Any],
        solution: Dict[str, Any]
    ) -> SolutionResult:
        start_time = time.time()
        try:
            is_valid, err_msg = self.validate_metadata(puzzle_instance)
            if not is_valid:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.MISSING_METADATA,
                    error_message=err_msg,
                    verification_time_ms=(time.time() - start_time) * 1000
                )

            target = puzzle_instance["initial_state"]["target"]
            solution_expr = solution["solution"]

            try:
                result = eval(solution_expr, {"__builtins__": {}})
            except Exception as e:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.INVALID_SOLUTION,
                    error_message=f"Eval error: {e}",
                    verification_time_ms=(time.time() - start_time) * 1000
                )

            if abs(result - target) < 1e-6:
                return SolutionResult(
                    is_valid=True,
                    verification_time_ms=(time.time() - start_time) * 1000
                )
            else:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.INVALID_SOLUTION,
                    error_message=f"Result {result} != target {target}",
                    verification_time_ms=(time.time() - start_time) * 1000
                )
        except Exception as e:
            self.logger.error(f"Arithmetic verification error: {e}")
            raise VerifierError(str(e))

    # ------------------------------------------------------------------
    # Dispatcher
    # ------------------------------------------------------------------
    def verify_solution(
        self,
        puzzle_instance: Dict[str, Any],
        solution: Optional[Dict[str, Any]] = None
    ) -> SolutionResult:
        """
        Main entry point. Determines puzzle type and routes to the
        appropriate verifier. Returns a SolutionResult.
        """
        p_type = puzzle_instance.get("puzzle_type")
        if not solution:
            solution = puzzle_instance.get("solution")

        if not solution:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INVALID_SOLUTION,
                error_message="No solution supplied"
            )

        if p_type == "sudoku":
            return self.verify_sudoku(puzzle_instance, solution)
        elif p_type == "pathfinding":
            return self.verify_pathfinding(puzzle_instance, solution)
        elif p_type == "logic_grid":
            return self.verify_logic_grid(puzzle_instance, solution)
        elif p_type == "arithmetic":
            return self.verify_arithmetic(puzzle_instance, solution)
        else:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.PARSE_FAILURE,
                error_message=f"Unknown puzzle type: {p_type}"
            )

    # ------------------------------------------------------------------
    # Simple tuple‑based API required by the task spec (schema‑compatible)
    # ------------------------------------------------------------------
    def verify(
        self,
        puzzle_instance: Dict[str, Any],
        solution: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Returns (is_valid, error_code_str) where error_code_str conforms to the
        dataset schema enum. Raises VerifierError on unexpected internal failures.
        Also logs the verification duration to `data/processed/verifier_timing.log`.
        """
        start_ms = time.time() * 1000
        result = self.verify_solution(puzzle_instance, solution)
        elapsed_ms = time.time() * 1000 - start_ms

        # Record timing
        try:
            log_path = paths.data("processed", "verifier_timing.log")
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"{time.time()},{elapsed_ms:.3f}\\n")
        except Exception as log_err:
            self.logger.error(f"Failed to write verifier timing log: {log_err}")

        mapped_code = self._map_error_code(result.error_code)
        return result.is_valid, mapped_code

def main():
    """CLI entry point for batch verification."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify puzzle instances and solutions"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input JSON file containing puzzles"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output JSON file for verification results"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=100,
        help="Timeout per verification in ms"
    )

    args = parser.parse_args()
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)

        puzzles = data.get("puzzles", data) if isinstance(data, dict) else data

        verifier = PuzzleVerifier(timeout_ms=args.timeout)
        results = []

        for i, puzzle in enumerate(puzzles):
            is_valid, err_code = verifier.verify(puzzle)
            results.append({
                "puzzle_index": i,
                "puzzle_type": puzzle.get("puzzle_type"),
                "is_valid": is_valid,
                "error_code": err_code
            })

        output_data = {
            "total_verified": len(results),
            "valid_count": sum(1 for r in results if r["is_valid"]),
            "invalid_count": sum(1 for r in results if not r["is_valid"]),
            "results": results
        }

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)

        print(f"Verification complete. Results saved to {args.output}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
