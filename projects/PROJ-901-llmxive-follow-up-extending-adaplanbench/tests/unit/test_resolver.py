"""
Unit tests for the ConstraintResolver class.
"""
import pytest
from agent.resolver import ConstraintResolver, ResolutionLog
from agent.constraint_store import Constraint, ConstraintStore
from agent.base import TaskContext


class TestConstraintResolver:
    """Tests for the ConstraintResolver class."""

    def test_resolve_no_violation(self):
        """Test resolution with no violations."""
        store = ConstraintStore()
        store.add_constraint(
            id="c1",
            text="do not use red objects",
            is_active=True
        )
        
        resolver = ConstraintResolver(store)
        context = TaskContext(task_id="test-001", current_step=1)
        
        is_violation, logs = resolver.resolve("do not use red objects", context)
        
        assert is_violation is False
        assert len(logs) > 0
        assert all(log.matched for log in logs)

    def test_resolve_violation(self):
        """Test resolution detecting a violation."""
        store = ConstraintStore()
        store.add_constraint(
            id="c2",
            text="do not use red objects",
            is_active=True
        )
        
        resolver = ConstraintResolver(store)
        context = TaskContext(task_id="test-002", current_step=1)
        
        is_violation, logs = resolver.resolve("use red objects", context)
        
        assert is_violation is True
        assert len(logs) > 0
        assert any(log.is_violation for log in logs)

    def test_resolve_parse_failure(self):
        """Test resolution with an unparseable intent."""
        store = ConstraintStore()
        resolver = ConstraintResolver(store)
        context = TaskContext(task_id="test-003", current_step=1)
        
        # Empty intent should cause parse failure
        is_violation, logs = resolver.resolve("", context)
        
        assert is_violation is False
        assert len(logs) > 0
        assert logs[0].resolution_type == "parse_failure"

    def test_multiple_constraints(self):
        """Test resolution against multiple constraints."""
        store = ConstraintStore()
        store.add_constraint(id="c3", text="no red", is_active=True)
        store.add_constraint(id="c4", text="no blue", is_active=True)
        
        resolver = ConstraintResolver(store)
        context = TaskContext(task_id="test-004", current_step=1)
        
        is_violation, logs = resolver.resolve("use red and blue", context)
        
        assert is_violation is True
        assert len(logs) == 2  # One log per constraint

    def test_get_logs(self):
        """Test retrieving all logs."""
        store = ConstraintStore()
        resolver = ConstraintResolver(store)
        context = TaskContext(task_id="test-005", current_step=1)
        
        resolver.resolve("use red", context)
        resolver.resolve("use blue", context)
        
        all_logs = resolver.get_logs()
        assert len(all_logs) >= 2

    def test_inactive_constraints_ignored(self):
        """Test that inactive constraints are not checked."""
        store = ConstraintStore()
        store.add_constraint(id="c5", text="no red", is_active=False)
        
        resolver = ConstraintResolver(store)
        context = TaskContext(task_id="test-006", current_step=1)
        
        # Should not match any active constraints
        is_violation, logs = resolver.resolve("use red", context)
        
        assert is_violation is False
        # Depending on implementation, may return empty logs or logs for inactive constraints
        # This test verifies behavior matches spec
