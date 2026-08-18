import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import sys
import os

# Import exceptions from the project root
# Note: Using absolute imports relative to the 'code' directory context
try:
    from exceptions import BaseResearchException, PARSE_FAILURE, CONTRADICTION_DETECTED, raise_parse_failure, raise_contradiction
except ImportError:
    # Fallback for direct execution or different import context
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from exceptions import BaseResearchException, PARSE_FAILURE, CONTRADICTION_DETECTED, raise_parse_failure, raise_contradiction

# Configure logging for the module
logger = logging.getLogger(__name__)

class SubGoalStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    EXCLUDED = "excluded"

@dataclass
class SubGoal:
    id: str
    description: str
    status: SubGoalStatus
    failure_reason: Optional[str] = None
    exclusion_code: Optional[str] = None

@dataclass
class DecompositionResult:
    sub_goals: List[SubGoal]
    original_puzzle_id: str
    total_sub_goals: int
    successful_sub_goals: int
    excluded_sub_goals: int
    status: str  # "complete", "partial", "failed"

class SymbolicPlanner:
    """
    Symbolic planner to decompose puzzle constraints into sub-goals.
    Implements robust failure logging and categorization for T037.
    """

    # Exclusion codes defined in T019b and T037
    EXCLUSION_CODES = {
        "PARSE_FAILURE": "PARSE_FAILURE",
        "CONTRADICTION_DETECTED": "CONTRADICTION_DETECTED",
        "IMPOSSIBLE_GOAL": "IMPOSSIBLE_GOAL",
        "NON_LINEAR_CONSTRAINT": "NON_LINEAR_CONSTRAINT"
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.exclusion_log_path = Path("data/processed/exclusions.json")
        self.exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize exclusion log if it doesn't exist
        if not self.exclusion_log_path.exists():
            self._write_exclusions([])
        
        logger.info(f"SymbolicPlanner initialized. Exclusion log: {self.exclusion_log_path}")

    def _load_exclusions(self) -> List[Dict[str, Any]]:
        """Load existing exclusions from the JSON log file."""
        try:
            with open(self.exclusion_log_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Could not load exclusions log: {e}. Starting fresh.")
            return []

    def _write_exclusions(self, exclusions: List[Dict[str, Any]]) -> None:
        """Write the full exclusions list back to the JSON log file."""
        with open(self.exclusion_log_path, 'w') as f:
            json.dump(exclusions, f, indent=2)
        logger.debug(f"Wrote {len(exclusions)} exclusions to {self.exclusion_log_path}")

    def _log_exclusion(self, puzzle_id: str, sub_goal_id: str, reason_code: str, 
                     reason_details: str) -> None:
        """
        Log a specific exclusion case to data/processed/exclusions.json.
        This satisfies T037 requirement to categorize and log failures.
        """
        if reason_code not in self.EXCLUSION_CODES.values():
            logger.warning(f"Unknown exclusion code: {reason_code}. Defaulting to PARSE_FAILURE.")
            reason_code = self.EXCLUSION_CODES["PARSE_FAILURE"]

        exclusion_entry = {
            "puzzle_id": puzzle_id,
            "sub_goal_id": sub_goal_id,
            "exclusion_code": reason_code,
            "reason_details": reason_details,
            "timestamp": str(Path(__file__).parent.parent) # Placeholder for real timestamp if needed
        }

        exclusions = self._load_exclusions()
        exclusions.append(exclusion_entry)
        self._write_exclusions(exclusions)
        
        logger.warning(f"Excluded sub-goal {sub_goal_id} for puzzle {puzzle_id}: {reason_code} - {reason_details}")

    def decompose(self, puzzle_constraints: Dict[str, Any], puzzle_id: str) -> DecompositionResult:
        """
        Decompose puzzle constraints into sub-goals.
        Handles failures by logging them and marking sub-goals as excluded.
        """
        sub_goals: List[SubGoal] = []
        successful_count = 0
        excluded_count = 0

        logger.info(f"Decomposing puzzle {puzzle_id} with {len(puzzle_constraints.get('constraints', []))} constraints")

        constraints = puzzle_constraints.get('constraints', [])
        initial_state = puzzle_constraints.get('initial_state', {})
        target_state = puzzle_constraints.get('target_state', {})

        # 1. Check for Parse Failures (e.g., missing required fields)
        if not constraints:
            reason = "No constraints provided in puzzle definition"
            self._log_exclusion(puzzle_id, "global", self.EXCLUSION_CODES["PARSE_FAILURE"], reason)
            return DecompositionResult(
                sub_goals=[],
                original_puzzle_id=puzzle_id,
                total_sub_goals=0,
                successful_sub_goals=0,
                excluded_sub_goals=1,
                status="failed"
            )

        # 2. Process each constraint
        for idx, constraint in enumerate(constraints):
            sub_goal_id = f"{puzzle_id}_sg_{idx}"
            
            try:
                # Simulate parsing logic that might fail
                # In a real implementation, this would call the parser from code/symbolic/parser.py
                if not isinstance(constraint, dict):
                    raise ValueError(f"Constraint at index {idx} is not a dictionary")
                
                if 'type' not in constraint:
                    raise ValueError(f"Constraint at index {idx} missing 'type' field")
                
                # Check for non-linear constraints (example logic)
                if constraint.get('type') == 'complex_relation' and 'non_linear' in constraint:
                    reason = f"Non-linear constraint detected: {constraint.get('non_linear')}"
                    self._log_exclusion(puzzle_id, sub_goal_id, self.EXCLUSION_CODES["NON_LINEAR_CONSTRAINT"], reason)
                    sub_goals.append(SubGoal(
                        id=sub_goal_id,
                        description=f"Handle {constraint.get('type')}",
                        status=SubGoalStatus.EXCLUDED,
                        failure_reason=reason,
                        exclusion_code=self.EXCLUSION_CODES["NON_LINEAR_CONSTRAINT"]
                    ))
                    excluded_count += 1
                    continue

                # Check for impossible goals (e.g., target state contradicts initial state)
                if initial_state and target_state:
                    # Simple check for immediate contradiction
                    if initial_state.get('value') == target_state.get('value') and constraint.get('require_change'):
                        reason = "Target state contradicts initial state (no change required but change forced)"
                        self._log_exclusion(puzzle_id, sub_goal_id, self.EXCLUSION_CODES["IMPOSSIBLE_GOAL"], reason)
                        sub_goals.append(SubGoal(
                            id=sub_goal_id,
                            description=f"Solve {constraint.get('type')}",
                            status=SubGoalStatus.EXCLUDED,
                            failure_reason=reason,
                            exclusion_code=self.EXCLUSION_CODES["IMPOSSIBLE_GOAL"]
                        ))
                        excluded_count += 1
                        continue

                # Successful decomposition
                sub_goals.append(SubGoal(
                    id=sub_goal_id,
                    description=f"Solve {constraint.get('type')}",
                    status=SubGoalStatus.SUCCESS
                ))
                successful_count += 1

            except Exception as e:
                # Catch-all for unexpected parsing errors
                reason = f"Unexpected error: {str(e)}"
                self._log_exclusion(puzzle_id, sub_goal_id, self.EXCLUSION_CODES["PARSE_FAILURE"], reason)
                sub_goals.append(SubGoal(
                    id=sub_goal_id,
                    description=f"Handle {constraint.get('type', 'unknown')}",
                    status=SubGoalStatus.EXCLUDED,
                    failure_reason=reason,
                    exclusion_code=self.EXCLUSION_CODES["PARSE_FAILURE"]
                ))
                excluded_count += 1

        # Determine overall status
        if excluded_count == len(constraints):
            status = "failed"
        elif excluded_count > 0:
            status = "partial"
        else:
            status = "complete"

        logger.info(f"Decomposition for {puzzle_id} complete: {successful_count} success, {excluded_count} excluded. Status: {status}")

        return DecompositionResult(
            sub_goals=sub_goals,
            original_puzzle_id=puzzle_id,
            total_sub_goals=len(constraints),
            successful_sub_goals=successful_count,
            excluded_sub_goals=excluded_count,
            status=status
        )

    def get_exclusion_summary(self) -> Dict[str, int]:
        """
        Return a summary of exclusion codes found in the log.
        Consumable by T029 for analysis.
        """
        exclusions = self._load_exclusions()
        summary = {code: 0 for code in self.EXCLUSION_CODES.values()}
        
        for entry in exclusions:
            code = entry.get('exclusion_code')
            if code in summary:
                summary[code] += 1
            else:
                summary[code] = 1 # Count unknowns too if they exist
        
        return summary

def main():
    """
    Main entry point for testing the planner and generating the exclusions log.
    This script creates a dummy dataset to demonstrate the logging capability.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    planner = SymbolicPlanner()
    
    # Create a test dataset with various failure modes to populate the log
    test_puzzles = [
        {
            "id": "puzzle_001",
            "constraints": [
                {"type": "simple", "value": 10},
                {"type": "complex_relation", "non_linear": "x^2 + y = z"}
            ],
            "initial_state": {"value": 5},
            "target_state": {"value": 10}
        },
        {
            "id": "puzzle_002",
            "constraints": [
                {"type": "simple", "value": 20},
                {"type": "simple", "value": 30}
            ],
            "initial_state": {"value": 50},
            "target_state": {"value": 50} # Contradiction if require_change is implied
        },
        {
            "id": "puzzle_003",
            "constraints": [], # Parse failure: empty constraints
            "initial_state": {},
            "target_state": {}
        },
        {
            "id": "puzzle_004",
            "constraints": [
                "invalid_constraint_string", # Parse failure: not a dict
                {"type": "simple", "value": 100}
            ],
            "initial_state": {},
            "target_state": {}
        }
    ]

    logger.info("Running planner on test dataset to generate exclusions log...")
    
    for puzzle in test_puzzles:
        try:
            result = planner.decompose(puzzle, puzzle['id'])
            logger.info(f"Puzzle {puzzle['id']}: {result.status}")
            for sg in result.sub_goals:
                if sg.status == SubGoalStatus.EXCLUDED:
                    logger.warning(f"  Excluded: {sg.id} - {sg.exclusion_code}")
        except Exception as e:
            logger.error(f"Failed to decompose {puzzle['id']}: {e}")

    summary = planner.get_exclusion_summary()
    logger.info(f"Exclusion Summary: {summary}")
    logger.info(f"Exclusions log written to: {planner.exclusion_log_path}")

    # Verify the file exists and has content
    if planner.exclusion_log_path.exists():
        with open(planner.exclusion_log_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Total exclusions recorded: {len(data)}")
    else:
        logger.error("Exclusions log file was not created!")

if __name__ == "__main__":
    main()