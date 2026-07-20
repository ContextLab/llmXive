"""Unit tests for implicit constraint logging (FR-009)."""
import pytest
from agent.resolver import ConstraintResolver, ResolutionLog
from agent.constraint_store import Constraint
from agent.base import TaskContext

def test_implicit_constraint_detection():
    """Test that implicit constraints are correctly identified."""
    resolver = ConstraintResolver()
    
    # Test implicit patterns
    implicit_texts = [
        "Ensure the room is reasonably tidy",
        "Make sure the task is completed logically",
        "Use common sense to arrange items",
        "Avoid unnecessary effort",
        "Take into account the typical arrangement",
        "Ensure the setup is appropriate",
        "Consider the practical arrangement"
    ]
    
    for text in implicit_texts:
        assert resolver._is_implicit_constraint(text), f"Failed to detect implicit: {text}"

def test_explicit_constraint_detection():
    """Test that explicit constraints are NOT flagged as implicit."""
    resolver = ConstraintResolver()
    
    explicit_texts = [
        "Place the book on the table",
        "Do not touch the vase",
        "Put the cup in the sink",
        "Open the drawer",
        "Turn on the light"
    ]
    
    for text in explicit_texts:
        assert not resolver._is_implicit_constraint(text), f"False positive implicit: {text}"

def test_implicit_unverified_logging():
    """Test that implicit constraints are logged as 'implicit_unverified'."""
    resolver = ConstraintResolver()
    
    implicit_constraint = Constraint(
        id="test-implicit-1",
        text="Ensure the room is reasonably tidy",
        is_active=True
    )
    
    context = TaskContext(task_id="test-001", constraints=[implicit_constraint])
    plan_text = "I will clean the room a bit."
    
    log = resolver.resolve_constraint(implicit_constraint, plan_text, context)
    
    assert log.resolution_status == "implicit_unverified"
    assert log.is_implicit is True
    assert "common-sense" in log.reason.lower() or "world knowledge" in log.reason.lower()

def test_explicit_constraint_resolved():
    """Test that explicit constraints are resolved normally."""
    resolver = ConstraintResolver()
    
    explicit_constraint = Constraint(
        id="test-explicit-1",
        text="Place the book on the table",
        is_active=True
    )
    
    context = TaskContext(task_id="test-001", constraints=[explicit_constraint])
    plan_text = "I will place the book on the table."
    
    log = resolver.resolve_constraint(explicit_constraint, plan_text, context)
    
    assert log.resolution_status == "resolved"
    assert log.is_implicit is False

def test_violation_rate_excludes_implicit():
    """Test that violation rate calculation excludes implicit_unverified constraints."""
    resolver = ConstraintResolver()
    
    # Add 2 explicit violations, 2 explicit resolved, 3 implicit
    constraints_data = [
        ("explicit-viol-1", "Place the book on the shelf", False),  # violation
        ("explicit-viol-2", "Open the window", False),              # violation
        ("explicit-res-1", "Close the door", True),                 # resolved
        ("explicit-res-2", "Turn off the light", True),             # resolved
        ("implicit-1", "Ensure it's reasonably tidy", None),        # implicit
        ("implicit-2", "Make it logically arranged", None),         # implicit
        ("implicit-3", "Use common sense", None),                   # implicit
    ]
    
    context = TaskContext(task_id="test-001", constraints=[])
    plan_text = "I will close the door and turn off the light."
    
    for cid, text, is_explicit_resolved in constraints_data:
        constraint = Constraint(id=cid, text=text, is_active=True)
        if is_explicit_resolved is True:
            resolver.resolve_constraint(constraint, plan_text, context)
        elif is_explicit_resolved is False:
            resolver.resolve_constraint(constraint, plan_text, context)
        else:
            resolver.resolve_constraint(constraint, plan_text, context)
    
    # Should have 2 violations, 2 resolved, 3 implicit
    violation_rate = resolver.get_violation_rate()
    expected_rate = 2 / 4  # 2 violations out of 4 non-implicit constraints
    
    assert abs(violation_rate - expected_rate) < 0.001
    assert resolver.get_implicit_count() == 3

def test_implicit_count_method():
    """Test the get_implicit_count method."""
    resolver = ConstraintResolver()
    
    context = TaskContext(task_id="test-001", constraints=[])
    plan_text = "Some plan text."
    
    # Add 3 implicit constraints
    for i in range(3):
        constraint = Constraint(
            id=f"implicit-{i}",
            text=f"Ensure it's reasonably {i}",
            is_active=True
        )
        resolver.resolve_constraint(constraint, plan_text, context)
    
    assert resolver.get_implicit_count() == 3

def test_resolution_log_structure():
    """Test that ResolutionLog has correct structure for implicit entries."""
    log = ResolutionLog(
        constraint_id="test-1",
        constraint_text="Ensure it's reasonably tidy",
        resolution_status="implicit_unverified",
        reason="Constraint requires common-sense reasoning",
        is_implicit=True
    )
    
    assert log.constraint_id == "test-1"
    assert log.resolution_status == "implicit_unverified"
    assert log.is_implicit is True
    assert log.reason is not None