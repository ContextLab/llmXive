"""
Symbolic Planner for BES.

Generates sub‑goal decompositions for puzzle solving.
Detects contradictory or unparsable constraints and logs exclusions.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from enum import Enum

# Local project imports
from code.exceptions import (
    CONTRADICTION_DETECTED,
    PARSE_FAILURE,
    raise_contradiction,
    raise_parse_failure,
    ParseFailure,
    ContradictionDetected,
)
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
    """Represents a single sub‑goal in a decomposition."""
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
    Symbolic planner that parses puzzle constraints, checks for contradictions,
    and produces a sequence of sub‑goals.
    """

    def __init__(self, exclusion_logger: Optional[ExclusionLogger] = None):
        """
        Initialise the planner.

        Args:
            exclusion_logger: Optional ``ExclusionLogger`` instance.
        """
        self.parser = PuzzleParser()
        self.exclusion_logger = exclusion_logger or ExclusionLogger()
        self.logger = logging.getLogger(self.__class__.__name__)

    def decompose(self, puzzle_instance: Dict[str, Any]) -> DecompositionResult:
        """
        Decompose a puzzle instance into sub‑goals.

        Args:
            puzzle_instance: Dictionary containing at least ``metadata`` and ``constraints``.

        Returns:
            ``DecompositionResult`` describing the outcome.
        """
        import time
        start_time = time.time()

        puzzle_id = puzzle_instance.get('metadata', {}).get('source_id', 'unknown')
        constraints_raw = puzzle_instance.get('constraints', [])

        try:
            # 1️⃣ Parse constraints
            self.logger.debug(f"Parsing constraints for puzzle {puzzle_id}")
            formal_constraints = self.parser.parse_constraints(constraints_raw)

            if not formal_constraints:
                raise_parse_failure(f"No valid constraints parsed for puzzle {puzzle_id}")

            # 2️⃣ Detect contradictions
            self.logger.debug(f"Checking contradictions for puzzle {puzzle_id}")
            if self._detect_contradictions(formal_constraints):
                raise_contradiction(f"Contradictory constraints in puzzle {puzzle_id}")

            # 3️⃣ Generate sub‑goals
            self.logger.debug(f"Generating sub‑goals for puzzle {puzzle_id}")
            sub_goals = self._generate_sub_goals(formal_constraints, puzzle_instance)

            exec_ms = (time.time() - start_time) * 1000
            return DecompositionResult(
                puzzle_id=puzzle_id,
                sub_goals=sub_goals,
                is_valid=True,
                execution_time_ms=exec_ms,
            )

        except ParseFailure as e:
            exec_ms = (time.time() - start_time) * 1000
            self._log_exclusion(puzzle_id, "PARSE_FAILURE", str(e), constraints_raw)
            return DecompositionResult(
                puzzle_id=puzzle_id,
                sub_goals=[],
                is_valid=False,
                error_code=PARSE_FAILURE,
                error_message=str(e),
                execution_time_ms=exec_ms,
            )

        except ContradictionDetected as e:
            exec_ms = (time.time() - start_time) * 1000
            self._log_exclusion(puzzle_id, "CONTRADICTION_DETECTED", str(e), constraints_raw)
            return DecompositionResult(
                puzzle_id=puzzle_id,
                sub_goals=[],
                is_valid=False,
                error_code=CONTRADICTION_DETECTED,
                error_message=str(e),
                execution_time_ms=exec_ms,
            )

        except Exception as e:
            exec_ms = (time.time() - start_time) * 1000
            self.logger.error(f"Unexpected error during decomposition of {puzzle_id}: {e}")
            return DecompositionResult(
                puzzle_id=puzzle_id,
                sub_goals=[],
                is_valid=False,
                error_code="INTERNAL_ERROR",
                error_message=str(e),
                execution_time_ms=exec_ms,
            )

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _detect_contradictions(self, constraints: List[FormalConstraint]) -> bool:
        """
        Detect logical contradictions among a set of formal constraints.

        Returns ``True`` if a contradiction is found.
        """
        assignments: Dict[str, Any] = {}
        equalities: List[tuple] = []
        inequalities: List[tuple] = []

        for c in constraints:
            ct = c.constraint_type
            if ct == FormalConstraintType.EQUALITY:
                var1, var2 = c.variables[0], c.variables[1]
                equalities.append((var1, var2))

            elif ct == FormalConstraintType.INEQUALITY:
                var1, var2 = c.variables[0], c.variables[1]
                inequalities.append((var1, var2))

            elif ct == FormalConstraintType.VALUE_ASSIGNMENT:
                var = c.variables[0]
                val = c.value
                if var in assignments and assignments[var] != val:
                    return True
                assignments[var] = val

            elif ct == FormalConstraintType.ALL_DIFFERENT:
                # Ensure no two already‑assigned variables share the same value
                seen_vals: Dict[Any, str] = {}
                for var in c.variables:
                    if var in assignments:
                        val = assignments[var]
                        if val in seen_vals:
                            return True
                        seen_vals[val] = var

        # Check that equalities do not conflict with inequalities
        # Build connected components of equal variables
        from collections import defaultdict, deque

        graph = defaultdict(set)
        for a, b in equalities:
            graph[a].add(b)
            graph[b].add(a)

        # Find components
        visited = set()
        components: List[set] = []
        for node in graph:
            if node not in visited:
                comp = set()
                dq = deque([node])
                while dq:
                    cur = dq.popleft()
                    if cur in visited:
                        continue
                    visited.add(cur)
                    comp.add(cur)
                    dq.extend(graph[cur] - visited)
                components.append(comp)

        # Any inequality inside the same component is a contradiction
        for a, b in inequalities:
            for comp in components:
                if a in comp and b in comp:
                    return True

        return False

    def _generate_sub_goals(self, constraints: List[FormalConstraint],
                            puzzle_instance: Dict[str, Any]) -> List[SubGoal]:
        """
        Turn formal constraints into an ordered list of ``SubGoal`` objects.
        The ordering is a simple heuristic: value assignments → equalities →
        all‑different → inequalities.
        """
        sub_goals: List[SubGoal] = []
        counter = 1

        # Helper to create a SubGoal and increment the counter
        def add_goal(desc: str, cons: List[FormalConstraint]) -> None:
            nonlocal counter
            sg = SubGoal(
                id=f"SG_{counter:03d}",
                description=desc,
                constraints=[self._constraint_to_dict(c) for c in cons],
            )
            sub_goals.append(sg)
            counter += 1

        # Group constraints by type
        value_assign = [c for c in constraints if c.constraint_type == FormalConstraintType.VALUE_ASSIGNMENT]
        eqs = [c for c in constraints if c.constraint_type == FormalConstraintType.EQUALITY]
        alldiff = [c for c in constraints if c.constraint_type == FormalConstraintType.ALL_DIFFERENT]
        ineqs = [c for c in constraints if c.constraint_type == FormalConstraintType.INEQUALITY]

        if value_assign:
            add_goal("Assign constant values", value_assign)
        if eqs:
            add_goal("Enforce equalities", eqs)
        if alldiff:
            add_goal("Enforce all‑different constraint", alldiff)
        if ineqs:
            add_goal("Enforce inequalities", ineqs)

        return sub_goals

    @staticmethod
    def _constraint_to_dict(constraint: FormalConstraint) -> Dict[str, Any]:
        """Serialise a ``FormalConstraint`` to a plain dictionary."""
        return {
            "type": constraint.constraint_type.value,
            "variables": constraint.variables,
            "value": constraint.value if hasattr(constraint, "value") else None,
        }

    def _log_exclusion(self, puzzle_id: str, reason: str,
                       error_message: str, constraints: List[Any]) -> None:
        """
        Record an exclusion event via the ``ExclusionLogger``.
        """
        event = ExclusionEvent(
            puzzle_id=puzzle_id,
            reason=reason,
            error_code=reason,
            error_message=error_message,
            source_file=puzzle_id,  # using puzzle_id as a simple identifier
            timestamp=datetime.now().isoformat(),
        )
        self.exclusion_logger.log_exclusion(event)
        self.logger.warning(f"Excluded puzzle {puzzle_id}: {reason} – {error_message}")

def main() -> None:
    """CLI entry point for manual testing of the planner."""
    import argparse

    parser = argparse.ArgumentParser(description="Run Symbolic Planner on a JSON puzzle file")
    parser.add_argument("--input", type=str, required=True, help="Path to input puzzle JSON file")
    parser.add_argument("--output", type=str, required=True, help="Path to write decomposition JSON")
    parser.add_argument(
        "--exclusion-log",
        type=str,
        default="data/processed/exclusions.json",
        help="Path to exclusion log file",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    # Load puzzles (expects a list of puzzle dicts)
    with open(args.input, "r", encoding="utf-8") as f:
        puzzles = json.load(f)

    exclusion_logger = ExclusionLogger(output_path=Path(args.exclusion_log))
    planner = SymbolicPlanner(exclusion_logger=exclusion_logger)

    results = [planner.decompose(p).__dict__ for p in puzzles]

    with open(args.output, "w", encoding="utf-8") as out_f:
        json.dump(results, out_f, indent=2)

    logger.info(f"Decomposition finished. Results written to {args.output}")

if __name__ == "__main__":
    main()