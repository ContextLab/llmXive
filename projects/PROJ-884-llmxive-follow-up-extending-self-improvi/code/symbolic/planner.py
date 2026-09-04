"""
Symbolic Planner for BES.

Generates sub-goal decompositions for puzzle solving.
Includes logic to detect and flag CONTRADICTION_DETECTED or PARSE_FAILURE.
Integrates with the exclusion logger to record invalid instances.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Import from project API surface
from code.exceptions import CONTRADICTION_DETECTED, PARSE_FAILURE, raise_contradiction, raise_parse_failure
from code.symbolic.exclusion_logger import ExclusionEvent, ExclusionLogger
from code.symbolic.parser import FormalConstraint, FormalConstraintType, PuzzleParser

logger = logging.getLogger(__name__)

class SubGoalStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONTRADICTION = "contradiction"

@dataclass
class SubGoal:
    """Represents a single sub-goal in a decomposition."""
    id: str
    description: str
    status: SubGoalStatus = SubGoalStatus.PENDING
    constraints: List[Dict[str, Any]] = field(default_factory=list)
    error_code: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class DecompositionResult:
    """Result of a symbolic decomposition."""
    puzzle_id: str
    sub_goals: List[SubGoal]
    is_valid: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0

class SymbolicPlanner:
    """
    Symbolic Planner that generates sub-goal decompositions.
    
    This planner parses puzzle constraints, validates them against the formal grammar,
    and breaks down complex puzzles into a sequence of manageable sub-goals.
    It integrates with the exclusion logger to flag instances that cannot be parsed
    or contain contradictions.
    """

    def __init__(self, exclusion_logger: Optional[ExclusionLogger] = None):
        """
        Initialize the planner.
        
        Args:
            exclusion_logger: Optional logger to record exclusion events.
        """
        self.parser = PuzzleParser()
        self.exclusion_logger = exclusion_logger or ExclusionLogger()
        self.logger = logging.getLogger(self.__class__.__name__)

    def decompose(self, puzzle_instance: Dict[str, Any]) -> DecompositionResult:
        """
        Decompose a puzzle instance into sub-goals.
        
        Args:
            puzzle_instance: Dictionary containing puzzle constraints, initial state, target state.
            
        Returns:
            DecompositionResult containing sub-goals or error information.
        """
        import time
        start_time = time.time()
        
        puzzle_id = puzzle_instance.get('metadata', {}).get('source_id', 'unknown')
        constraints_raw = puzzle_instance.get('constraints', [])
        
        try:
            # Step 1: Parse constraints into formal language
            self.logger.debug(f"Parsing constraints for puzzle {puzzle_id}")
            formal_constraints = self.parser.parse_constraints(constraints_raw)
            
            if not formal_constraints:
                raise_parse_failure(f"No valid constraints parsed for puzzle {puzzle_id}")
            
            # Step 2: Detect contradictions in constraints
            self.logger.debug(f"Checking for contradictions in puzzle {puzzle_id}")
            contradiction_found = self._detect_contradictions(formal_constraints)
            
            if contradiction_found:
                raise_contradiction(f"Contradictory constraints detected in puzzle {puzzle_id}")
            
            # Step 3: Generate sub-goal decomposition
            self.logger.debug(f"Generating sub-goals for puzzle {puzzle_id}")
            sub_goals = self._generate_sub_goals(formal_constraints, puzzle_instance)
            
            execution_time = (time.time() - start_time) * 1000
            
            return DecompositionResult(
                puzzle_id=puzzle_id,
                sub_goals=sub_goals,
                is_valid=True,
                execution_time_ms=execution_time
            )
            
        except PARSE_FAILURE as e:
            execution_time = (time.time() - start_time) * 1000
            self._log_exclusion(
                puzzle_id=puzzle_id,
                reason="PARSE_FAILURE",
                error_message=str(e),
                constraints=constraints_raw
            )
            return DecompositionResult(
                puzzle_id=puzzle_id,
                sub_goals=[],
                is_valid=False,
                error_code="PARSE_FAILURE",
                error_message=str(e),
                execution_time_ms=execution_time
            )
            
        except CONTRADICTION_DETECTED as e:
            execution_time = (time.time() - start_time) * 1000
            self._log_exclusion(
                puzzle_id=puzzle_id,
                reason="CONTRADICTION_DETECTED",
                error_message=str(e),
                constraints=constraints_raw
            )
            return DecompositionResult(
                puzzle_id=puzzle_id,
                sub_goals=[],
                is_valid=False,
                error_code="CONTRADICTION_DETECTED",
                error_message=str(e),
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error(f"Unexpected error decomposing puzzle {puzzle_id}: {e}")
            return DecompositionResult(
                puzzle_id=puzzle_id,
                sub_goals=[],
                is_valid=False,
                error_code="INTERNAL_ERROR",
                error_message=str(e),
                execution_time_ms=execution_time
            )

    def _detect_contradictions(self, constraints: List[FormalConstraint]) -> bool:
        """
        Detect logical contradictions in a set of formal constraints.
        
        Args:
            constraints: List of parsed formal constraints.
            
        Returns:
            True if a contradiction is detected, False otherwise.
        """
        # Extract variable assignments and their domains
        assignments: Dict[str, Any] = {}
        equalities: List[Tuple[str, str]] = []
        inequalities: List[Tuple[str, str]] = []
        
        for constraint in constraints:
            if constraint.constraint_type == FormalConstraintType.EQUALITY:
                var1, var2 = constraint.variables[0], constraint.variables[1]
                if var1 in assignments and var2 in assignments:
                    if assignments[var1] != assignments[var2]:
                        return True
                if var1 in assignments:
                    equalities.append((var1, var2))
                elif var2 in assignments:
                    equalities.append((var2, var1))
                else:
                    equalities.append((var1, var2))
                    
            elif constraint.constraint_type == FormalConstraintType.INEQUALITY:
                var1, var2 = constraint.variables[0], constraint.variables[1]
                if var1 in assignments and var2 in assignments:
                    if assignments[var1] == assignments[var2]:
                        return True
                inequalities.append((var1, var2))
                
            elif constraint.constraint_type == FormalConstraintType.VALUE_ASSIGNMENT:
                var = constraint.variables[0]
                value = constraint.value
                if var in assignments:
                    if assignments[var] != value:
                        return True
                assignments[var] = value
                
            elif constraint.constraint_type == FormalConstraintType.ALL_DIFFERENT:
                # Check if any pair in the group is already assigned the same value
                group_vars = constraint.variables
                assigned_values = {}
                for var in group_vars:
                    if var in assignments:
                        val = assignments[var]
                        if val in assigned_values:
                            return True
                        assigned_values[val] = var
            
        # Check for transitive contradictions in equalities
        # Build a graph of equalities and check for conflicts with inequalities
        from collections import defaultdict
        equality_graph = defaultdict(set)
        for var1, var2 in equalities:
            equality_graph[var1].add(var2)
            equality_graph[var2].add(var1)
        
        # Find connected components
        visited = set()
        components = []
        for var in equality_graph:
            if var not in visited:
                component = set()
                stack = [var]
                while stack:
                    node = stack.pop()
                    if node not in visited:
                        visited.add(node)
                        component.add(node)
                        stack.extend(equality_graph[node] - visited)
                components.append(component)
        
        # Check if any inequality connects two variables in the same component
        for var1, var2 in inequalities:
            for component in components:
                if var1 in component and var2 in component:
                    return True
                    
        return False

    def _generate_sub_goals(self, constraints: List[FormalConstraint], puzzle_instance: Dict[str, Any]) -> List[SubGoal]:
        """
        Generate a sequence of sub-goals from formal constraints.
        
        Args:
            constraints: List of parsed formal constraints.
            puzzle_instance: Original puzzle instance for context.
            
        Returns:
            List of SubGoal objects.
        """
        sub_goals = []
        goal_counter = 1
        
        # Group constraints by type for logical ordering
        value_assignments = [c for c in constraints if c.constraint_type == FormalConstraintType.VALUE_ASSIGNMENT]
        equalities = [c for c in constraints if c.constraint_type == FormalConstraintType.EQUALITY]
        inequalities = [c for c in constraints if c.constraint_type == FormalConstraintType.INEQUALITY]
        all_different = [c for c in constraints if c.constraint_type == FormalConstraintType.ALL_DIFFERENT]
        
        # 1. Process value assignments first (base facts)
        for constraint in value_assignments:
            sub_goal = SubGoal(
                id=f"SG_{goal_counter:03d}",
                description=f"Set {constraint.variables[0]} = {constraint.value}",
                status=SubGoalStatus.PENDING,
                constraints=[self._constraint_to_dict(constraint)]
            )
            sub_goals.append(sub_goal)
            goal_counter += 1
            
        # 2. Process equalities (propagate known values)
        for constraint in equalities:
            sub_goal = SubGoal(
                id=f"SG_{goal_counter:03d}",
                description=f"Ensure {constraint.variables[0]} == {constraint.variables[1]}",
                status=SubGoalStatus.PENDING,
                constraints=[self._constraint_to_dict(constraint)]
            )
            sub_goals.append(sub_goal)
            goal_counter += 1
            
        # 3. Process all-different constraints (grouping)
        for constraint in all_different:
            sub_goal = SubGoal(
                id=f"SG_{goal_counter:03d}",
                description=f"Ensure all variables {constraint.variables} are different",
                status=SubGoalStatus.PENDING,
                constraints=[self._constraint_to_dict(constraint)]
            )
            sub_goals.append(sub_goal)
            goal_counter += 1
            
        # 4. Process inequalities (final checks)
        for constraint in inequalities:
            sub_goal = SubGoal(
                id=f"SG_{goal_counter:03d}",
                description=f"Ensure {constraint.variables[0]} != {constraint.variables[1]}",
                status=SubGoalStatus.PENDING,
                constraints=[self._constraint_to_dict(constraint)]
            )
            sub_goals.append(sub_goal)
            goal_counter += 1
            
        return sub_goals

    def _constraint_to_dict(self, constraint: FormalConstraint) -> Dict[str, Any]:
        """Convert a FormalConstraint to a dictionary."""
        return {
            "type": constraint.constraint_type.value,
            "variables": constraint.variables,
            "value": constraint.value if hasattr(constraint, 'value') else None
        }

    def _log_exclusion(self, puzzle_id: str, reason: str, error_message: str, constraints: List[Any]):
        """
        Log an exclusion event to the exclusion logger.
        
        Args:
            puzzle_id: ID of the excluded puzzle.
            reason: Reason for exclusion (e.g., PARSE_FAILURE, CONTRADICTION_DETECTED).
            error_message: Detailed error message.
            constraints: The constraints that caused the exclusion.
        """
        event = ExclusionEvent(
            puzzle_id=puzzle_id,
            reason=reason,
            error_code=reason,
            error_message=error_message,
            source_file=puzzle_id,  # Using puzzle_id as source identifier
            timestamp=datetime.now().isoformat()
        )
        self.exclusion_logger.log_exclusion(event)
        self.logger.warning(f"Excluded puzzle {puzzle_id}: {reason} - {error_message}")

def main():
    """Main entry point for the planner."""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Symbolic Planner for BES")
    parser.add_argument("--input", type=str, required=True, help="Path to input puzzle JSON file")
    parser.add_argument("--output", type=str, required=True, help="Path to output decomposition JSON file")
    parser.add_argument("--exclusion-log", type=str, default="data/processed/exclusions.json", help="Path to exclusion log")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Load puzzles
    with open(args.input, 'r') as f:
        puzzles = json.load(f)
        
    # Initialize planner
    exclusion_logger = ExclusionLogger(output_path=Path(args.exclusion_log))
    planner = SymbolicPlanner(exclusion_logger=exclusion_logger)
    
    results = []
    for puzzle in puzzles:
        result = planner.decompose(puzzle)
        results.append(result)
        
    # Save results
    with open(args.output, 'w') as f:
        json.dump([r.__dict__ if hasattr(r, '__dict__') else r for r in results], f, indent=2)
        
    logger.info(f"Decomposition complete. Results saved to {args.output}")

if __name__ == "__main__":
    main()
