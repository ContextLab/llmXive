"""
Puzzle Verifier Module for llmXive
Validates puzzle instances and solutions with deterministic logic.
Implements T066: Data Provenance metadata validation.
"""

import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ErrorCodes(Enum):
    """Error codes for verification failures"""
    VALID = "VALID"
    INVALID_SOLUTION = "INVALID_SOLUTION"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"
    DUPLICATE_ROW = "DUPLICATE_ROW"
    INVALID_PATH = "INVALID_PATH"
    MISSING_METADATA = "MISSING_METADATA"
    PARSE_FAILURE = "PARSE_FAILURE"
    VERIFIER_ERROR = "VERIFIER_ERROR"
    TIMEOUT = "TIMEOUT"

@dataclass
class SolutionResult:
    """Result of solution verification"""
    is_valid: bool
    error_code: Optional[ErrorCodes] = None
    error_message: Optional[str] = None
    verification_time_ms: Optional[float] = None

class DataVerificationError(Exception):
    """Custom exception for data verification failures"""
    pass

class PuzzleVerifier:
    """
    Validates puzzle instances and solutions.
    Implements T066: Validates provenance metadata before processing.
    """

    def __init__(self, timeout_ms: int = 100):
        self.timeout_ms = timeout_ms
        self.logger = logging.getLogger(__name__)

    def validate_metadata(self, puzzle_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that puzzle instance has required provenance metadata.
        T066 Requirement: Every puzzle must have:
        - source_id
        - generation_seed
        - timestamp
        - generator_version
        - complexity_metric (with constraint_count and variable_domain_size)
        
        Returns: (is_valid, error_message)
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

    def verify_sudoku(
        self,
        puzzle_instance: Dict[str, Any],
        solution: Dict[str, Any]
    ) -> SolutionResult:
        """Verify Sudoku solution"""
        start_time = time.time()
        
        try:
            # Validate metadata first
            is_valid, error_msg = self.validate_metadata(puzzle_instance)
            if not is_valid:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.MISSING_METADATA,
                    error_message=error_msg,
                    verification_time_ms=(time.time() - start_time) * 1000
                )
            
            grid_size = puzzle_instance["initial_state"]["size"]
            solution_grid = solution["solution"]
            
            # Check grid dimensions
            if len(solution_grid) != grid_size:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.INVALID_SOLUTION,
                    error_message=f"Grid size mismatch: expected {grid_size}, got {len(solution_grid)}",
                    verification_time_ms=(time.time() - start_time) * 1000
                )
            
            # Check each row
            for row_idx, row in enumerate(solution_grid):
                if len(row) != grid_size:
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.DUPLICATE_ROW,
                        error_message=f"Row {row_idx} has incorrect length",
                        verification_time_ms=(time.time() - start_time) * 1000
                    )
                
                if sorted(row) != list(range(1, grid_size + 1)):
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.DUPLICATE_ROW,
                        error_message=f"Row {row_idx} contains duplicates or missing values",
                        verification_time_ms=(time.time() - start_time) * 1000
                    )
            
            # Check each column
            for col_idx in range(grid_size):
                column = [solution_grid[row_idx][col_idx] for row_idx in range(grid_size)]
                if sorted(column) != list(range(1, grid_size + 1)):
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.DUPLICATE_ROW,
                        error_message=f"Column {col_idx} contains duplicates or missing values",
                        verification_time_ms=(time.time() - start_time) * 1000
                    )
            
            # Check boxes
            box_size = int(grid_size ** 0.5)
            for box_row in range(0, grid_size, box_size):
                for box_col in range(0, grid_size, box_size):
                    box_values = []
                    for r in range(box_row, box_row + box_size):
                        for c in range(box_col, box_col + box_size):
                            box_values.append(solution_grid[r][c])
                    
                    if sorted(box_values) != list(range(1, grid_size + 1)):
                        return SolutionResult(
                            is_valid=False,
                            error_code=ErrorCodes.DUPLICATE_ROW,
                            error_message=f"Box at ({box_row}, {box_col}) contains duplicates or missing values",
                            verification_time_ms=(time.time() - start_time) * 1000
                        )
            
            return SolutionResult(
                is_valid=True,
                verification_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            self.logger.error(f"Error verifying sudoku: {e}")
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.VERIFIER_ERROR,
                error_message=str(e),
                verification_time_ms=(time.time() - start_time) * 1000
            )

    def verify_pathfinding(
        self,
        puzzle_instance: Dict[str, Any],
        solution: Dict[str, Any]
    ) -> SolutionResult:
        """Verify pathfinding solution"""
        start_time = time.time()
        
        try:
            # Validate metadata first
            is_valid, error_msg = self.validate_metadata(puzzle_instance)
            if not is_valid:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.MISSING_METADATA,
                    error_message=error_msg,
                    verification_time_ms=(time.time() - start_time) * 1000
                )
            
            grid_size = puzzle_instance["initial_state"]["size"]
            start = tuple(puzzle_instance["initial_state"]["start"])
            end = tuple(puzzle_instance["initial_state"]["end"])
            obstacles = [tuple(obs) for obs in puzzle_instance["initial_state"]["obstacles"]]
            path = [tuple(p) for p in solution["path"]]
            
            # Check path is not empty
            if not path:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.INVALID_PATH,
                    error_message="Path is empty",
                    verification_time_ms=(time.time() - start_time) * 1000
                )
            
            # Check start and end points
            if path[0] != start:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.INVALID_PATH,
                    error_message=f"Path does not start at {start}",
                    verification_time_ms=(time.time() - start_time) * 1000
                )
            
            if path[-1] != end:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.INVALID_PATH,
                    error_message=f"Path does not end at {end}",
                    verification_time_ms=(time.time() - start_time) * 1000
                )
            
            # Check path validity
            for i, (r, c) in enumerate(path):
                # Check bounds
                if not (0 <= r < grid_size and 0 <= c < grid_size):
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.INVALID_PATH,
                        error_message=f"Path point {i} ({r}, {c}) is out of bounds",
                        verification_time_ms=(time.time() - start_time) * 1000
                    )
                
                # Check obstacles
                if (r, c) in obstacles:
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.INVALID_PATH,
                        error_message=f"Path point {i} ({r}, {c}) is an obstacle",
                        verification_time_ms=(time.time() - start_time) * 1000
                    )
                
                # Check adjacency
                if i > 0:
                    prev_r, prev_c = path[i - 1]
                    dist = abs(r - prev_r) + abs(c - prev_c)
                    if dist != 1:
                        return SolutionResult(
                            is_valid=False,
                            error_code=ErrorCodes.INVALID_PATH,
                            error_message=f"Path point {i} is not adjacent to previous point",
                            verification_time_ms=(time.time() - start_time) * 1000
                        )
            
            return SolutionResult(
                is_valid=True,
                verification_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            self.logger.error(f"Error verifying pathfinding: {e}")
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.VERIFIER_ERROR,
                error_message=str(e),
                verification_time_ms=(time.time() - start_time) * 1000
            )

    def verify_logic_grid(
        self,
        puzzle_instance: Dict[str, Any],
        solution: Dict[str, Any]
    ) -> SolutionResult:
        """Verify logic grid solution"""
        start_time = time.time()
        
        try:
            # Validate metadata first
            is_valid, error_msg = self.validate_metadata(puzzle_instance)
            if not is_valid:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.MISSING_METADATA,
                    error_message=error_msg,
                    verification_time_ms=(time.time() - start_time) * 1000
                )
            
            # For logic grids, we verify the solution structure
            categories = puzzle_instance["initial_state"]["categories"]
            solution_data = solution["solution"]
            
            if not isinstance(solution_data, dict):
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.INVALID_SOLUTION,
                    error_message="Solution must be a dictionary",
                    verification_time_ms=(time.time() - start_time) * 1000
                )
            
            for category in categories:
                if category not in solution_data:
                    return SolutionResult(
                        is_valid=False,
                        error_code=ErrorCodes.INVALID_SOLUTION,
                        error_message=f"Missing category in solution: {category}",
                        verification_time_ms=(time.time() - start_time) * 1000
                    )
            
            return SolutionResult(
                is_valid=True,
                verification_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            self.logger.error(f"Error verifying logic grid: {e}")
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.VERIFIER_ERROR,
                error_message=str(e),
                verification_time_ms=(time.time() - start_time) * 1000
            )

    def verify_arithmetic(
        self,
        puzzle_instance: Dict[str, Any],
        solution: Dict[str, Any]
    ) -> SolutionResult:
        """Verify arithmetic solution"""
        start_time = time.time()
        
        try:
            # Validate metadata first
            is_valid, error_msg = self.validate_metadata(puzzle_instance)
            if not is_valid:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.MISSING_METADATA,
                    error_message=error_msg,
                    verification_time_ms=(time.time() - start_time) * 1000
                )
            
            target = puzzle_instance["initial_state"]["target"]
            operands = puzzle_instance["initial_state"]["operands"]
            solution_expr = solution["solution"]
            
            # Evaluate solution expression
            try:
                result = eval(solution_expr)
            except Exception as e:
                return SolutionResult(
                    is_valid=False,
                    error_code=ErrorCodes.INVALID_SOLUTION,
                    error_message=f"Invalid solution expression: {e}",
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
                    error_message=f"Solution result {result} does not match target {target}",
                    verification_time_ms=(time.time() - start_time) * 1000
                )
            
        except Exception as e:
            self.logger.error(f"Error verifying arithmetic: {e}")
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.VERIFIER_ERROR,
                error_message=str(e),
                verification_time_ms=(time.time() - start_time) * 1000
            )

    def verify_solution(
        self,
        puzzle_instance: Dict[str, Any],
        solution: Optional[Dict[str, Any]] = None
    ) -> SolutionResult:
        """
        Main verification entry point.
        Routes to appropriate verifier based on puzzle type.
        """
        puzzle_type = puzzle_instance.get("puzzle_type")
        
        if not solution:
            solution = puzzle_instance.get("solution")
        
        if not solution:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.INVALID_SOLUTION,
                error_message="No solution provided"
            )
        
        if puzzle_type == "sudoku":
            return self.verify_sudoku(puzzle_instance, solution)
        elif puzzle_type == "pathfinding":
            return self.verify_pathfinding(puzzle_instance, solution)
        elif puzzle_type == "logic_grid":
            return self.verify_logic_grid(puzzle_instance, solution)
        elif puzzle_type == "arithmetic":
            return self.verify_arithmetic(puzzle_instance, solution)
        else:
            return SolutionResult(
                is_valid=False,
                error_code=ErrorCodes.PARSE_FAILURE,
                error_message=f"Unknown puzzle type: {puzzle_type}"
            )

def main():
    """Main entry point for verification"""
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
        help="Timeout in milliseconds per verification (default: 100)"
    )
    
    args = parser.parse_args()
    
    try:
        # Load puzzles
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        puzzles = data.get("puzzles", data) if isinstance(data, dict) else data
        
        verifier = PuzzleVerifier(timeout_ms=args.timeout)
        results = []
        
        for i, puzzle in enumerate(puzzles):
            result = verifier.verify_solution(puzzle)
            results.append({
                "puzzle_index": i,
                "puzzle_type": puzzle.get("puzzle_type"),
                "is_valid": result.is_valid,
                "error_code": result.error_code.value if result.error_code else None,
                "error_message": result.error_message,
                "verification_time_ms": result.verification_time_ms
            })
        
        # Save results
        output_data = {
            "total_verified": len(results),
            "valid_count": sum(1 for r in results if r["is_valid"]),
            "invalid_count": sum(1 for r in results if not r["is_valid"]),
            "results": results
        }
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"Verification complete. Results saved to {args.output}")
        return 0
        
    except FileNotFoundError:
        logger.error(f"Input file not found: {args.input}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
