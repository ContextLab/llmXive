"""
Unit tests for edge cases in the ConstraintResolver.

Tests cover:
1. Implicit constraint handling (no violation logged when constraint is implicit)
2. Parsing failures (false_negative logged when intent parsing fails)
3. Empty constraint lists (no violations, no errors)
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import List, Dict, Any, Optional

from agent.base import ViolationType, ExecutionResult, TaskContext
from agent.constraint_store import Constraint, ConstraintStore
from agent.resolver import ConstraintResolver, ResolutionLog
from agent.resolver_utils import parse_intent, match_constraint


class TestImplicitConstraintHandling:
    """Tests for implicit constraints that should not log violations."""

    def test_implicit_constraint_no_violation(self):
        """
        When a constraint is marked as implicit (requires common-sense reasoning),
        the resolver should NOT log a violation even if it seems unmet.
        """
        # Setup
        task_context = TaskContext(
            task_id="test_task_1",
            task_description="Bring the cup to the table",
            initial_state={"cup_location": "counter", "table_location": "room"},
            target_state={"cup_location": "table"}
        )

        # Create an implicit constraint (e.g., "don't break the cup" - common sense)
        implicit_constraint = Constraint(
            id="c1",
            text="do not break the cup",
            is_implicit=True,  # Marked as implicit
            violation_type=ViolationType.COMMON_SENSE,
            status="active"
        )

        store = ConstraintStore()
        store.add_constraint(implicit_constraint)

        resolver = ConstraintResolver()

        # Create a plan that technically "violates" the common sense constraint
        # (e.g., a plan that says "smash the cup")
        plan = ["smash the cup on the floor"]

        # Execute resolution
        results = resolver.resolve(task_context, plan, store)

        # Verify: No violation logged for implicit constraint
        violation_logs = [r for r in results if r.violation_logged]
        assert len(violation_logs) == 0, "Implicit constraints should not log violations"

    def test_implicit_constraint_with_explicit_override(self):
        """
        If an implicit constraint is explicitly overridden in the plan context,
        it should still be handled gracefully without false violation logs.
        """
        task_context = TaskContext(
            task_id="test_task_2",
            task_description="Clean the spill",
            initial_state={"spill": True},
            target_state={"spill": False}
        )

        # Implicit constraint: "don't use too much water"
        implicit_constraint = Constraint(
            id="c2",
            text="do not use excessive water",
            is_implicit=True,
            violation_type=ViolationType.COMMON_SENSE,
            status="active"
        )

        store = ConstraintStore()
        store.add_constraint(implicit_constraint)

        resolver = ConstraintResolver()

        # Plan that uses a lot of water but is contextually necessary
        plan = ["pour entire bucket of water on spill"]

        results = resolver.resolve(task_context, plan, store)

        # Should not log violation for implicit constraint
        violation_logs = [r for r in results if r.violation_logged]
        assert len(violation_logs) == 0


class TestParsingFailures:
    """Tests for cases where intent parsing fails and false_negative is logged."""

    def test_unparseable_intent_logs_false_negative(self):
        """
        When the resolver cannot parse the intent from the plan description,
        it should log a false_negative event.
        """
        task_context = TaskContext(
            task_id="test_task_3",
            task_description="Organize the shelf",
            initial_state={"items": ["book", "pen", "cup"]},
            target_state={"items_sorted": True}
        )

        store = ConstraintStore()
        resolver = ConstraintResolver()

        # Plan with gibberish or unparseable intent
        plan = ["asdfghjkl random gibberish !@#$%^&*()"]

        results = resolver.resolve(task_context, plan, store)

        # Verify false_negative is logged
        false_negative_logs = [
            r for r in results
            if r.violation_type == ViolationType.FALSE_NEGATIVE
        ]
        assert len(false_negative_logs) >= 1, "Should log false_negative for unparseable intent"

    def test_empty_plan_logs_false_negative(self):
        """
        When the plan is empty, intent parsing fails and false_negative is logged.
        """
        task_context = TaskContext(
            task_id="test_task_4",
            task_description="Open the door",
            initial_state={"door": "closed"},
            target_state={"door": "open"}
        )

        store = ConstraintStore()
        resolver = ConstraintResolver()

        # Empty plan
        plan = []

        results = resolver.resolve(task_context, plan, store)

        # Verify false_negative is logged
        false_negative_logs = [
            r for r in results
            if r.violation_type == ViolationType.FALSE_NEGATIVE
        ]
        assert len(false_negative_logs) >= 1, "Should log false_negative for empty plan"

    def test_malformed_syntax_logs_false_negative(self):
        """
        When the plan has malformed syntax that prevents intent extraction,
        false_negative is logged.
        """
        task_context = TaskContext(
            task_id="test_task_5",
            task_description="Mix ingredients",
            initial_state={"ingredients": ["flour", "eggs"]},
            target_state={"mixed": True}
        )

        store = ConstraintStore()
        resolver = ConstraintResolver()

        # Malformed plan (nested structures, missing verbs, etc.)
        plan = ["{{{ invalid syntax }}}", ">>> broken command"]

        results = resolver.resolve(task_context, plan, store)

        # Verify false_negative is logged
        false_negative_logs = [
            r for r in results
            if r.violation_type == ViolationType.FALSE_NEGATIVE
        ]
        assert len(false_negative_logs) >= 1, "Should log false_negative for malformed syntax"


class TestEmptyConstraintLists:
    """Tests for scenarios with no constraints active."""

    def test_no_constraints_no_violations(self):
        """
        When there are no active constraints, the resolver should return
        an empty result set with no violations logged.
        """
        task_context = TaskContext(
            task_id="test_task_6",
            task_description="Walk across the room",
            initial_state={"position": "start"},
            target_state={"position": "end"}
        )

        store = ConstraintStore()
        # No constraints added

        resolver = ConstraintResolver()
        plan = ["walk forward", "turn left", "walk forward"]

        results = resolver.resolve(task_context, plan, store)

        # Verify no violations logged
        assert len(results) == 0, "Should return empty results when no constraints exist"

    def test_empty_constraint_store_with_valid_plan(self):
        """
        Even with a valid plan, if the constraint store is empty,
        no violation logs should be generated.
        """
        task_context = TaskContext(
            task_id="test_task_7",
            task_description="Stack blocks",
            initial_state={"blocks": ["red", "blue", "green"]},
            target_state={"stacked": True}
        )

        store = ConstraintStore()
        resolver = ConstraintResolver()

        plan = ["pick up red block", "place on table", "pick up blue block", "stack on red"]

        results = resolver.resolve(task_context, plan, store)

        # Verify no results (no constraints to check)
        assert len(results) == 0

    def test_empty_constraint_store_with_invalid_plan(self):
        """
        If the plan is invalid but there are no constraints,
        the resolver should not log violations (no rules to violate).
        """
        task_context = TaskContext(
            task_id="test_task_8",
            task_description="Pour water",
            initial_state={"cup": "empty"},
            target_state={"cup": "full"}
        )

        store = ConstraintStore()
        resolver = ConstraintResolver()

        # Invalid plan (nonsensical)
        plan = ["teleport water from ocean to cup"]

        results = resolver.resolve(task_context, plan, store)

        # No violations because no constraints exist to check against
        assert len(results) == 0, "No violations should be logged when no constraints exist"


class TestIntegrationEdgeCases:
    """Integration tests combining multiple edge cases."""

    def test_mixed_implicit_and_explicit_constraints(self):
        """
        Test scenario with both implicit and explicit constraints:
        - Implicit: no violation logged
        - Explicit: violation logged if violated
        """
        task_context = TaskContext(
            task_id="test_task_9",
            task_description="Prepare a meal",
            initial_state={"kitchen": "clean"},
            target_state={"meal": "ready"}
        )

        store = ConstraintStore()

        # Explicit constraint (must be followed)
        explicit_constraint = Constraint(
            id="c_explicit",
            text="do not use raw eggs",
            is_implicit=False,
            violation_type=ViolationType.SAFETY,
            status="active"
        )

        # Implicit constraint (common sense)
        implicit_constraint = Constraint(
            id="c_implicit",
            text="do not waste food",
            is_implicit=True,
            violation_type=ViolationType.COMMON_SENSE,
            status="active"
        )

        store.add_constraint(explicit_constraint)
        store.add_constraint(implicit_constraint)

        resolver = ConstraintResolver()

        # Plan that violates explicit constraint but not implicit
        plan = ["use raw eggs in salad"]

        results = resolver.resolve(task_context, plan, store)

        # Verify: explicit violation logged, implicit not logged
        explicit_violations = [
            r for r in results
            if r.constraint_id == "c_explicit" and r.violation_logged
        ]
        implicit_violations = [
            r for r in results
            if r.constraint_id == "c_implicit" and r.violation_logged
        ]

        assert len(explicit_violations) == 1, "Explicit constraint violation should be logged"
        assert len(implicit_violations) == 0, "Implicit constraint violation should not be logged"

    def test_parsing_failure_with_constraints(self):
        """
        When parsing fails, false_negative is logged regardless of constraints.
        """
        task_context = TaskContext(
            task_id="test_task_10",
            task_description="Assemble furniture",
            initial_state={"parts": ["legs", "top"]},
            target_state={"assembled": True}
        )

        store = ConstraintStore()
        store.add_constraint(Constraint(
            id="c1",
            text="do not scratch the surface",
            is_implicit=False,
            violation_type=ViolationType.DAMAGE,
            status="active"
        ))

        resolver = ConstraintResolver()
        plan = ["??? parse error ???"]

        results = resolver.resolve(task_context, plan, store)

        # Should log false_negative for parsing failure
        false_negative_logs = [
            r for r in results
            if r.violation_type == ViolationType.FALSE_NEGATIVE
        ]
        assert len(false_negative_logs) >= 1, "Should log false_negative even with constraints present"