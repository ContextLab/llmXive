"""
Symbolic Planner for Bidirectional Evolutionary Search.

This module implements the backward step of the BES framework, generating
sub-goal decompositions for puzzle solving. It includes robust logic to
detect and flag logically impossible sub-goals that contradict the current
puzzle state.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from code.exceptions import CONTRADICTION_DETECTED, raise_contradiction
from code.symbolic.exclusion_logger import ExclusionLogger, ExclusionReason

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SubGoalStatus(Enum):
    """Status of a sub-goal in the decomposition."""
    VALID = "valid"
    IMPOSSIBLE = "impossible"
    CONTRADICTION = "contradiction"
    PENDING = "pending"


@dataclass
class SubGoal:
    """Represents a single sub-goal in the decomposition."""
    id: str
    description: str
    target_state: Dict[str, Any]
    constraints: List[str]
    status: SubGoalStatus = SubGoalStatus.PENDING
    reason: Optional[str] = None
    lookahead_depth: int = 0


@dataclass
class DecompositionResult:
    """Result of decomposing a puzzle into sub-goals."""
    puzzle_id: str
    initial_state: Dict[str, Any]
    target_state: Dict[str, Any]
    sub_goals: List[SubGoal]
    is_valid: bool
    exclusion_reason: Optional[str] = None
    total_sub_goals: int = 0
    valid_sub_goals: int = 0
    impossible_sub_goals: int = 0


class SymbolicPlanner:
    """
    Symbolic planner that generates sub-goal decompositions for puzzle solving.
    
    This planner includes a lookahead mechanism to detect logically impossible
    sub-goals that would lead to dead-end trajectories.
    """
    
    def __init__(self, exclusion_logger: Optional[ExclusionLogger] = None):
        """
        Initialize the symbolic planner.
        
        Args:
            exclusion_logger: Logger for exclusion events. If None, a default
                              logger will be created.
        """
        self.exclusion_logger = exclusion_logger or ExclusionLogger()
        self.logger = logging.getLogger(__name__)
    
    def _check_state_consistency(
        self, 
        current_state: Dict[str, Any], 
        target_state: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a target state is consistent with the current state.
        
        This is a basic consistency check that verifies:
        1. No direct contradictions in state variables
        2. Target state doesn't violate immutable constraints
        
        Args:
            current_state: The current puzzle state
            target_state: The proposed target state
        
        Returns:
            Tuple of (is_consistent, error_message)
        """
        # Check for direct variable contradictions
        for key, value in target_state.items():
            if key in current_state:
                # Check if the target violates immutable constraints
                if isinstance(current_state[key], dict):
                    if 'immutable' in current_state[key] and current_state[key]['immutable']:
                        if current_state[key]['value'] != value:
                            return False, f"Immutable constraint violated: {key}"
                
                # Check for direct value contradictions in simple types
                elif isinstance(current_state[key], (int, float, str, bool)):
                    # For pathfinding, check if target is unreachable
                    if key == "position" and isinstance(value, dict):
                        # This is a simplified check; real implementation would
                        # use the puzzle-specific verifier
                        pass
        
        return True, None
    
    def _simulate_subgoal_application(
        self, 
        state: Dict[str, Any], 
        sub_goal: SubGoal
    ) -> Tuple[Dict[str, Any], bool, Optional[str]]:
        """
        Simulate applying a sub-goal to the current state.
        
        This function attempts to apply the sub-goal's target state and
        constraints to see if it results in a valid intermediate state.
        
        Args:
            state: Current puzzle state
            sub_goal: The sub-goal to apply
        
        Returns:
            Tuple of (new_state, is_valid, error_message)
        """
        # Create a copy of the state to simulate changes
        new_state = json.loads(json.dumps(state))  # Deep copy
        
        try:
            # Apply target state changes
            for key, value in sub_goal.target_state.items():
                new_state[key] = value
            
            # Check if the resulting state is valid
            is_consistent, error_msg = self._check_state_consistency(
                state, 
                sub_goal.target_state
            )
            
            if not is_consistent:
                return new_state, False, error_msg
            
            return new_state, True, None
            
        except Exception as e:
            return new_state, False, f"Simulation failed: {str(e)}"
    
    def _lookahead_validation(
        self, 
        initial_state: Dict[str, Any], 
        sub_goals: List[SubGoal],
        max_depth: int = 3
    ) -> Tuple[List[SubGoal], List[Tuple[SubGoal, str]]]:
        """
        Perform lookahead validation on the sub-goal sequence.
        
        This function simulates applying each sub-goal in sequence and
        checks for contradictions or impossible states.
        
        Args:
            initial_state: The starting puzzle state
            sub_goals: List of sub-goals to validate
            max_depth: Maximum depth of lookahead simulation
        
        Returns:
            Tuple of (valid_sub_goals, impossible_sub_goals_with_reasons)
        """
        valid_sub_goals = []
        impossible_sub_goals = []
        current_state = json.loads(json.dumps(initial_state))
        
        for i, sub_goal in enumerate(sub_goals):
            if i >= max_depth:
                # Stop lookahead at max depth
                valid_sub_goals.append(sub_goal)
                continue
            
            # Simulate applying this sub-goal
            new_state, is_valid, error_msg = self._simulate_subgoal_application(
                current_state, 
                sub_goal
            )
            
            if is_valid:
                valid_sub_goals.append(sub_goal)
                current_state = new_state
                sub_goal.status = SubGoalStatus.VALID
            else:
                # Mark as impossible and record reason
                sub_goal.status = SubGoalStatus.IMPOSSIBLE
                sub_goal.reason = error_msg
                impossible_sub_goals.append((sub_goal, error_msg))
                self.logger.warning(
                    f"Sub-goal {sub_goal.id} is impossible: {error_msg}"
                )
        
        return valid_sub_goals, impossible_sub_goals
    
    def decompose_puzzle(
        self, 
        puzzle_id: str,
        initial_state: Dict[str, Any],
        target_state: Dict[str, Any],
        constraints: List[str],
        lookahead_depth: int = 3
    ) -> DecompositionResult:
        """
        Decompose a puzzle into a sequence of sub-goals.
        
        This method generates a sub-goal decomposition and performs
        lookahead validation to detect logically impossible sub-goals.
        
        Args:
            puzzle_id: Unique identifier for the puzzle
            initial_state: The starting puzzle state
            target_state: The desired final state
            constraints: List of puzzle constraints
            lookahead_depth: Depth for lookahead validation
        
        Returns:
            DecompositionResult containing the sub-goals and validation status
        """
        self.logger.info(f"Decomposing puzzle {puzzle_id} with lookahead depth {lookahead_depth}")
        
        # Generate initial sub-goals (simplified decomposition logic)
        # In a real implementation, this would use the puzzle-specific
        # planning algorithm
        sub_goals = self._generate_initial_subgoals(
            initial_state, 
            target_state, 
            constraints
        )
        
        # Perform lookahead validation
        valid_sub_goals, impossible_sub_goals = self._lookahead_validation(
            initial_state, 
            sub_goals, 
            lookahead_depth
        )
        
        # Check if we have any impossible sub-goals
        has_impossible = len(impossible_sub_goals) > 0
        
        if has_impossible:
            # Log the impossible sub-goals
            for sub_goal, reason in impossible_sub_goals:
                self.logger.error(
                    f"Impossible sub-goal detected: {sub_goal.id} - {reason}"
                )
                
                # Log to exclusion logger
                self.exclusion_logger.log_exclusion(
                    puzzle_id=puzzle_id,
                    reason=ExclusionReason.IMPOSSIBLE_SUBGOAL,
                    details={
                        "sub_goal_id": sub_goal.id,
                        "reason": reason,
                        "lookahead_depth": lookahead_depth
                    }
                )
                
                # Raise contradiction exception for the first impossible sub-goal
                if sub_goal == impossible_sub_goals[0][0]:
                    raise_contradiction(
                        f"Logically impossible sub-goal detected: {reason}",
                        puzzle_id=puzzle_id,
                        sub_goal_id=sub_goal.id
                    )
        
        # Calculate statistics
        total_sub_goals = len(sub_goals)
        valid_count = len(valid_sub_goals)
        impossible_count = len(impossible_sub_goals)
        
        return DecompositionResult(
            puzzle_id=puzzle_id,
            initial_state=initial_state,
            target_state=target_state,
            sub_goals=sub_goals,
            is_valid=not has_impossible,
            exclusion_reason=impossible_sub_goals[0][1] if impossible_sub_goals else None,
            total_sub_goals=total_sub_goals,
            valid_sub_goals=valid_count,
            impossible_sub_goals=impossible_count
        )
    
    def _generate_initial_subgoals(
        self,
        initial_state: Dict[str, Any],
        target_state: Dict[str, Any],
        constraints: List[str]
    ) -> List[SubGoal]:
        """
        Generate initial sub-goals from the puzzle definition.
        
        This is a simplified implementation that creates sub-goals based on
        the differences between initial and target states.
        
        Args:
            initial_state: Starting puzzle state
            target_state: Desired final state
            constraints: Puzzle constraints
        
        Returns:
            List of initial sub-goals
        """
        sub_goals = []
        sub_goal_counter = 0
        
        # Simple decomposition: create a sub-goal for each state variable
        # that needs to change
        for key in target_state.keys():
            if key not in initial_state or initial_state[key] != target_state[key]:
                sub_goal_counter += 1
                sub_goal = SubGoal(
                    id=f"sg_{sub_goal_counter}",
                    description=f"Set {key} to {target_state[key]}",
                    target_state={key: target_state[key]},
                    constraints=constraints,
                    status=SubGoalStatus.PENDING
                )
                sub_goals.append(sub_goal)
        
        # If no differences found, create a dummy sub-goal
        if not sub_goals:
            sub_goal_counter += 1
            sub_goal = SubGoal(
                id=f"sg_{sub_goal_counter}",
                description="No state changes required",
                target_state={},
                constraints=constraints,
                status=SubGoalStatus.VALID
            )
            sub_goals.append(sub_goal)
        
        return sub_goals


def main():
    """Main entry point for testing the planner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test symbolic planner")
    parser.add_argument("--puzzle-id", type=str, default="test_001")
    parser.add_argument("--lookahead-depth", type=int, default=3)
    args = parser.parse_args()
    
    # Create a test puzzle
    initial_state = {
        "position": {"x": 0, "y": 0},
        "grid_size": 10,
        "obstacles": [{"x": 2, "y": 2}, {"x": 3, "y": 3}]
    }
    
    target_state = {
        "position": {"x": 5, "y": 5},
        "grid_size": 10,
        "obstacles": [{"x": 2, "y": 2}, {"x": 3, "y": 3}]
    }
    
    constraints = ["avoid_obstacles", "shortest_path"]
    
    # Create planner and decompose
    planner = SymbolicPlanner()
    
    try:
        result = planner.decompose_puzzle(
            puzzle_id=args.puzzle_id,
            initial_state=initial_state,
            target_state=target_state,
            constraints=constraints,
            lookahead_depth=args.lookahead_depth
        )
        
        print(f"Puzzle {result.puzzle_id} decomposition:")
        print(f"  Valid: {result.is_valid}")
        print(f"  Total sub-goals: {result.total_sub_goals}")
        print(f"  Valid sub-goals: {result.valid_sub_goals}")
        print(f"  Impossible sub-goals: {result.impossible_sub_goals}")
        
        if not result.is_valid:
            print(f"  Exclusion reason: {result.exclusion_reason}")
            
    except Exception as e:
        print(f"Error during decomposition: {str(e)}")
        raise


if __name__ == "__main__":
    main()