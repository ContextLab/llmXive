import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from code.exceptions import PARSE_FAILURE, CONTRADICTION_DETECTED, VERIFIER_ERROR
from code.symbolic.parser import PuzzleParser, parse_dataset_file
from code.utils.logger import log

class SubGoalStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    EXCLUDED = "excluded"

@dataclass
class SubGoal:
    id: str
    description: str
    status: SubGoalStatus = SubGoalStatus.PENDING
    exclusion_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DecompositionResult:
    puzzle_id: str
    sub_goals: List[SubGoal]
    success: bool
    error_message: Optional[str] = None
    exclusion_log: List[Dict[str, str]] = field(default_factory=list)

class SymbolicPlanner:
    """
    Symbolic planner to generate sub-goal decompositions for puzzle solving.
    Implements logging for exclusion reasons as per FR-006.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger("symbolic_planner")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        self.exclusion_log: List[Dict[str, str]] = []

    def plan(self, puzzle_instance: Dict[str, Any]) -> DecompositionResult:
        """
        Generate a decomposition of sub-goals for the given puzzle instance.
        
        Args:
            puzzle_instance: Dictionary containing puzzle data (constraints, initial state, etc.)
        
        Returns:
            DecompositionResult containing sub-goals and exclusion logs.
        """
        puzzle_id = puzzle_instance.get("id", "unknown")
        self.exclusion_log = []
        sub_goals: List[SubGoal] = []
        
        try:
            # Parse constraints using the parser module
            parser = PuzzleParser()
            constraints = parser.parse(puzzle_instance)
            
            if not constraints:
                self._log_exclusion(
                    puzzle_id, "IMPOSSIBLE_GOAL", 
                    "No constraints parsed from puzzle instance."
                )
                return DecompositionResult(
                    puzzle_id=puzzle_id,
                    sub_goals=[],
                    success=False,
                    error_message="No constraints parsed.",
                    exclusion_log=self.exclusion_log
                )

            # Process constraints to generate sub-goals
            for i, constraint in enumerate(constraints):
                sub_goal_id = f"{puzzle_id}_sg_{i}"
                
                # Check for specific failure modes as per spec
                if constraint.type == "PARSE_FAILURE":
                    self._log_exclusion(
                        puzzle_id, "PARSE_FAILURE",
                        f"Constraint {i} failed to parse: {constraint.error}"
                    )
                    continue
                
                if constraint.type == "CONTRADICTION_DETECTED":
                    self._log_exclusion(
                        puzzle_id, "CONTRADICTION_DETECTED",
                        f"Constraint {i} contains a contradiction: {constraint.error}"
                    )
                    continue

                # Check for non-linear constraints if applicable
                if constraint.metadata.get("is_nonlinear", False):
                    self._log_exclusion(
                        puzzle_id, "NON_LINEAR_CONSTRAINT",
                        f"Constraint {i} is non-linear and cannot be decomposed symbolically."
                    )
                    continue

                # Create valid sub-goal
                sub_goal = SubGoal(
                    id=sub_goal_id,
                    description=constraint.description,
                    status=SubGoalStatus.PENDING,
                    metadata={"source_constraint_id": constraint.id}
                )
                sub_goals.append(sub_goal)

            # Check if all constraints were excluded
            if not sub_goals:
                if not self.exclusion_log:
                    self._log_exclusion(
                        puzzle_id, "IMPOSSIBLE_GOAL",
                        "No valid sub-goals could be generated."
                    )
                return DecompositionResult(
                    puzzle_id=puzzle_id,
                    sub_goals=[],
                    success=False,
                    error_message="No valid sub-goals generated.",
                    exclusion_log=self.exclusion_log
                )

            return DecompositionResult(
                puzzle_id=puzzle_id,
                sub_goals=sub_goals,
                success=True,
                exclusion_log=self.exclusion_log
            )

        except PARSE_FAILURE as e:
            self._log_exclusion(puzzle_id, "PARSE_FAILURE", str(e))
            return DecompositionResult(
                puzzle_id=puzzle_id,
                sub_goals=[],
                success=False,
                error_message=str(e),
                exclusion_log=self.exclusion_log
            )
        except CONTRADICTION_DETECTED as e:
            self._log_exclusion(puzzle_id, "CONTRADICTION_DETECTED", str(e))
            return DecompositionResult(
                puzzle_id=puzzle_id,
                sub_goals=[],
                success=False,
                error_message=str(e),
                exclusion_log=self.exclusion_log
            )
        except Exception as e:
            self._log_exclusion(puzzle_id, "VERIFIER_ERROR", str(e))
            return DecompositionResult(
                puzzle_id=puzzle_id,
                sub_goals=[],
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                exclusion_log=self.exclusion_log
            )

    def _log_exclusion(self, puzzle_id: str, reason: str, details: str) -> None:
        """
        Log an exclusion reason for a sub-goal or puzzle.
        
        Args:
            puzzle_id: ID of the puzzle being processed.
            reason: One of PARSE_FAILURE, CONTRADICTION_DETECTED, 
                    IMPOSSIBLE_GOAL, NON_LINEAR_CONSTRAINT.
            details: Human-readable explanation of the exclusion.
        """
        valid_reasons = {
            "PARSE_FAILURE", 
            "CONTRADICTION_DETECTED", 
            "IMPOSSIBLE_GOAL", 
            "NON_LINEAR_CONSTRAINT"
        }
        
        if reason not in valid_reasons:
            self.logger.warning(
                f"Invalid exclusion reason '{reason}'. "
                f"Must be one of {valid_reasons}."
            )
            reason = "UNKNOWN"

        entry = {
            "puzzle_id": puzzle_id,
            "reason": reason,
            "details": details,
            "timestamp": str(logging.getLogger().manager.manager) # Simplified for demo
        }
        
        # Use a real timestamp
        from datetime import datetime
        entry["timestamp"] = datetime.now().isoformat()

        self.exclusion_log.append(entry)
        self.logger.info(
            f"Exclusion logged for {puzzle_id}: {reason} - {details}"
        )

    def get_exclusion_log(self) -> List[Dict[str, str]]:
        """Return the current exclusion log."""
        return self.exclusion_log

    def clear_exclusion_log(self) -> None:
        """Clear the exclusion log."""
        self.exclusion_log = []

def main():
    """
    Main entry point for testing the planner with exclusion logging.
    """
    # Create a sample puzzle instance for testing
    sample_puzzle = {
        "id": "test_puzzle_001",
        "type": "pathfinding",
        "initial_state": {"x": 0, "y": 0},
        "target_state": {"x": 5, "y": 5},
        "constraints": [
            {
                "id": "c1",
                "type": "obstacle",
                "description": "Avoid cells (2,2) and (3,3)",
                "metadata": {"cells": [(2,2), (3,3)]}
            },
            {
                "id": "c2",
                "type": "distance",
                "description": "Path length must be minimal",
                "metadata": {"min_length": 10}
            },
            {
                "id": "c3",
                "type": "nonlinear",
                "description": "Complex non-linear constraint",
                "metadata": {"is_nonlinear": True}
            }
        ]
    }

    planner = SymbolicPlanner()
    result = planner.plan(sample_puzzle)

    print(f"Puzzle ID: {result.puzzle_id}")
    print(f"Success: {result.success}")
    print(f"Sub-goals generated: {len(result.sub_goals)}")
    print(f"Exclusion log entries: {len(result.exclusion_log)}")
    
    if result.exclusion_log:
        print("\nExclusion Log:")
        for entry in result.exclusion_log:
            print(f"  - {entry['reason']}: {entry['details']}")
    
    if result.error_message:
        print(f"Error: {result.error_message}")

if __name__ == "__main__":
    main()