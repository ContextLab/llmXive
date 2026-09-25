"""
Fitness Evaluator for the Bidirectional Evolutionary Search (BES) framework.

This module implements the fitness evaluation step, which scores candidate solutions
using the deterministic verifier (T012). It enforces a timeout per evaluation to
ensure the evolutionary loop remains tractable.
"""

import signal
import time
import logging
import os
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

# Import the verifier API surface as defined in the project
from code.dataset.verifier import PuzzleVerifier, SolutionResult, ErrorCodes

logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    """Custom exception raised when an evaluation times out."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout events."""
    raise TimeoutException("Evaluation timed out")


@dataclass
class FitnessResult:
    """
    Result of a fitness evaluation.

    Attributes:
        score: The numeric fitness score (higher is better).
        valid: Boolean indicating if the solution is valid.
        error_code: Specific error code if invalid (e.g., 'VIOLATION', 'TIMEOUT').
        evaluation_time_ms: Time taken to evaluate in milliseconds.
        details: Additional diagnostic information.
    """
    score: float
    valid: bool
    error_code: Optional[str] = None
    evaluation_time_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FitnessEvaluator:
    """
    Evaluates the fitness of candidate solutions using the deterministic verifier.

    Attributes:
        verifier: The instance of PuzzleVerifier to use.
        timeout_seconds: Maximum time allowed for a single evaluation.
    """
    verifier: PuzzleVerifier
    timeout_seconds: float = 5.0

    def evaluate(self, puzzle_instance: Dict[str, Any], candidate_solution: str) -> FitnessResult:
        """
        Evaluate a candidate solution against a puzzle instance.

        Args:
            puzzle_instance: The dictionary containing puzzle constraints and metadata.
            candidate_solution: The string representation of the candidate solution.

        Returns:
            FitnessResult containing the score, validity, and metadata.
        """
        start_time = time.time()
        
        # Set up the timeout handler
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(self.timeout_seconds))

        try:
            # Perform the verification
            # The verifier returns a SolutionResult object
            result = self.verifier.verify(puzzle_instance, candidate_solution)
            
            # Cancel the alarm if successful
            signal.alarm(0)

            elapsed_time_ms = (time.time() - start_time) * 1000

            if result.is_valid:
                # Score is 1.0 for valid solutions, or could be a function of complexity
                # For now, we assign 1.0 for valid, 0.0 for invalid
                score = 1.0
                error_code = None
                valid = True
            else:
                # Score is 0.0 for invalid solutions
                score = 0.0
                error_code = result.error_code
                valid = False

            return FitnessResult(
                score=score,
                valid=valid,
                error_code=error_code,
                evaluation_time_ms=elapsed_time_ms,
                details={
                    "puzzle_id": puzzle_instance.get("metadata", {}).get("source_id", "unknown"),
                    "solution_length": len(candidate_solution),
                    "verifier_output": result
                }
            )

        except TimeoutException as e:
            signal.alarm(0)
            elapsed_time_ms = (time.time() - start_time) * 1000
            logger.warning(f"Evaluation timed out after {self.timeout_seconds}s")
            return FitnessResult(
                score=0.0,
                valid=False,
                error_code="TIMEOUT",
                evaluation_time_ms=elapsed_time_ms,
                details={"reason": str(e)}
            )
        except Exception as e:
            signal.alarm(0)
            elapsed_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Evaluation failed with unexpected error: {e}")
            return FitnessResult(
                score=0.0,
                valid=False,
                error_code="VERIFIER_ERROR",
                evaluation_time_ms=elapsed_time_ms,
                details={"reason": str(e)}
            )

    def evaluate_batch(self, puzzle_instances: List[Dict[str, Any]], 
                       candidate_solutions: List[str]) -> List[FitnessResult]:
        """
        Evaluate a batch of candidate solutions.

        Args:
            puzzle_instances: List of puzzle instance dictionaries.
            candidate_solutions: List of candidate solution strings.

        Returns:
            List of FitnessResult objects.
        """
        if len(puzzle_instances) != len(candidate_solutions):
            raise ValueError("puzzle_instances and candidate_solutions must have the same length")

        results = []
        for puzzle, solution in zip(puzzle_instances, candidate_solutions):
            result = self.evaluate(puzzle, solution)
            results.append(result)
        return results


def main():
    """
    Main entry point for testing the fitness evaluator.
    This function generates a mock puzzle and solution, evaluates it, and prints the result.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Initialize the verifier
    verifier = PuzzleVerifier()
    
    # Create a mock puzzle instance
    mock_puzzle = {
        "constraints": ["x + y = 5", "x > 0", "y > 0"],
        "initial_state": {},
        "target_state": {"x": 2, "y": 3},
        "metadata": {
            "source_id": "mock_test_001",
            "generation_seed": 42
        }
    }
    
    # Create a mock candidate solution
    mock_solution = "x=2, y=3"
    
    # Initialize the evaluator
    evaluator = FitnessEvaluator(verifier=verifier, timeout_seconds=2.0)
    
    # Evaluate the solution
    result = evaluator.evaluate(mock_puzzle, mock_solution)
    
    print(f"Evaluation Result:")
    print(f"  Score: {result.score}")
    print(f"  Valid: {result.valid}")
    print(f"  Error Code: {result.error_code}")
    print(f"  Time (ms): {result.evaluation_time_ms}")
    print(f"  Details: {result.details}")


if __name__ == "__main__":
    main()