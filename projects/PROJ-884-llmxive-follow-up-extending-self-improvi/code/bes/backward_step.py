"""
Backward Step Implementation for Bidirectional Evolutionary Search.

This module implements the symbolic backward step, replacing the neural verifier
with a deterministic symbolic planner that generates sub-goals and validates
solution trajectories.
"""
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from code.exceptions import PARSE_FAILURE, CONTRADICTION_DETECTED, VERIFIER_ERROR
from code.symbolic.parser import PuzzleParser, parse_dataset_file
from code.symbolic.planner import SymbolicPlanner, DecompositionResult, SubGoalStatus
from code.utils.logger import log
from code.utils.seed import set_seed


class BackwardStepError(Exception):
    """Custom exception for backward step failures."""
    pass


@dataclass
class BackwardStepResult:
    """Result of the backward step execution."""
    success: bool
    sub_goals: List[Dict[str, Any]]
    validation_status: str
    execution_time_ms: float
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    excluded_count: int = 0
    exclusion_reasons: List[Dict[str, str]] = field(default_factory=list)


class BackwardStep:
    """
    Implements the backward step of the BES framework.

    Uses a symbolic planner to decompose puzzle constraints into sub-goals
    and validate solution trajectories deterministically.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        parser: Optional[PuzzleParser] = None,
        planner: Optional[SymbolicPlanner] = None
    ):
        """
        Initialize the backward step.

        Args:
            config: Experiment configuration dictionary
            parser: Optional custom parser instance
            planner: Optional custom planner instance
        """
        self.config = config
        self.parser = parser or PuzzleParser()
        self.planner = planner or SymbolicPlanner(
            max_sub_goals=config.get('max_sub_goals', 10),
            timeout_ms=config.get('planner_timeout_ms', 1000)
        )
        self.exclusion_log: List[Dict[str, str]] = []

    def _log_exclusion(self, reason: str, details: Dict[str, Any]) -> None:
        """
        Log an exclusion reason as per FR-006.

        Args:
            reason: The type of failure (PARSE_FAILURE, CONTRADICTION_DETECTED)
            details: Additional context about the failure
        """
        self.exclusion_log.append({
            'reason': reason,
            'details': details,
            'timestamp': time.time()
        })

    def process_puzzle(
        self,
        puzzle_instance: Dict[str, Any]
    ) -> BackwardStepResult:
        """
        Process a single puzzle instance through the symbolic backward step.

        Args:
            puzzle_instance: Dictionary containing puzzle constraints and metadata

        Returns:
            BackwardStepResult containing sub-goals and validation status
        """
        start_time = time.time()

        try:
            # Parse the puzzle constraints
            log(f"Parsing puzzle instance: {puzzle_instance.get('id', 'unknown')}")
            formal_constraints = self.parser.parse(puzzle_instance)

            if not formal_constraints:
                raise PARSE_FAILURE("Failed to parse puzzle constraints")

            # Generate sub-goal decomposition
            log(f"Decomposing puzzle into sub-goals")
            decomposition: DecompositionResult = self.planner.decompose(
                formal_constraints
            )

            if decomposition.status == SubGoalStatus.FAILED:
                error_code = decomposition.error_code or "UNKNOWN_DECOMPOSITION_ERROR"
                error_msg = decomposition.error_message or "Decomposition failed"
                self._log_exclusion(error_code, {
                    'puzzle_id': puzzle_instance.get('id'),
                    'error': error_msg
                })
                raise CONTRADICTION_DETECTED(error_msg)

            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000

            # Return successful result
            return BackwardStepResult(
                success=True,
                sub_goals=[sg.to_dict() for sg in decomposition.sub_goals],
                validation_status="VALIDATED",
                execution_time_ms=execution_time_ms,
                excluded_count=len(self.exclusion_log),
                exclusion_reasons=self.exclusion_log.copy()
            )

        except PARSE_FAILURE as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self._log_exclusion("PARSE_FAILURE", {
                'puzzle_id': puzzle_instance.get('id'),
                'error': str(e)
            })
            return BackwardStepResult(
                success=False,
                sub_goals=[],
                validation_status="PARSE_FAILURE",
                execution_time_ms=execution_time_ms,
                error_code="PARSE_FAILURE",
                error_message=str(e),
                excluded_count=len(self.exclusion_log),
                exclusion_reasons=self.exclusion_log.copy()
            )

        except CONTRADICTION_DETECTED as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self._log_exclusion("CONTRADICTION_DETECTED", {
                'puzzle_id': puzzle_instance.get('id'),
                'error': str(e)
            })
            return BackwardStepResult(
                success=False,
                sub_goals=[],
                validation_status="CONTRADICTION_DETECTED",
                execution_time_ms=execution_time_ms,
                error_code="CONTRADICTION_DETECTED",
                error_message=str(e),
                excluded_count=len(self.exclusion_log),
                exclusion_reasons=self.exclusion_log.copy()
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            log(f"Unexpected error in backward step: {str(e)}", level="ERROR")
            return BackwardStepResult(
                success=False,
                sub_goals=[],
                validation_status="VERIFIER_ERROR",
                execution_time_ms=execution_time_ms,
                error_code="VERIFIER_ERROR",
                error_message=str(e),
                excluded_count=len(self.exclusion_log),
                exclusion_reasons=self.exclusion_log.copy()
            )

    def process_batch(
        self,
        puzzle_instances: List[Dict[str, Any]]
    ) -> Tuple[List[BackwardStepResult], int]:
        """
        Process a batch of puzzle instances.

        Args:
            puzzle_instances: List of puzzle instance dictionaries

        Returns:
            Tuple of (list of results, count of excluded puzzles)
        """
        results = []
        excluded_count = 0

        for puzzle in puzzle_instances:
            result = self.process_puzzle(puzzle)
            results.append(result)
            if not result.success:
                excluded_count += 1

        return results, excluded_count


def main() -> None:
    """
    Entry point for testing the backward step module.

    Reads configuration, loads a sample puzzle dataset, and processes it
    through the backward step to demonstrate functionality.
    """
    import json
    from code.config import load_config

    # Load configuration
    config_path = Path("config/experiment_config.yaml")
    if not config_path.exists():
        config_path = Path("config/default_config.yaml")

    if config_path.exists():
        config = load_config(config_path)
    else:
        config = {
            'max_sub_goals': 10,
            'planner_timeout_ms': 1000,
            'seed': 42
        }

    set_seed(config.get('seed', 42))

    # Create a sample puzzle instance for demonstration
    sample_puzzle = {
        'id': 'demo_puzzle_001',
        'type': 'pathfinding',
        'constraints': {
            'grid_size': 5,
            'start': (0, 0),
            'end': (4, 4),
            'obstacles': [(2, 2), (3, 3)]
        },
        'difficulty': 'medium'
    }

    # Initialize backward step
    backward_step = BackwardStep(config)

    # Process the sample puzzle
    log("Starting backward step processing for sample puzzle")
    result = backward_step.process_puzzle(sample_puzzle)

    # Output results
    print(json.dumps({
        'success': result.success,
        'sub_goals_count': len(result.sub_goals),
        'validation_status': result.validation_status,
        'execution_time_ms': result.execution_time_ms,
        'error_code': result.error_code,
        'error_message': result.error_message,
        'excluded_count': result.excluded_count
    }, indent=2))

    if result.sub_goals:
        print("\nGenerated Sub-goals:")
        for i, sg in enumerate(result.sub_goals, 1):
            print(f"  {i}. {sg.get('description', 'No description')}")

    if result.exclusion_reasons:
        print("\nExclusion Log:")
        for reason in result.exclusion_reasons:
            print(f"  - {reason['reason']}: {reason['details']}")


if __name__ == "__main__":
    main()
