"""
Unit tests for the OraclePolicyEngine.

The tests verify that the engine correctly identifies a budget‑cap
violation and returns exactly one violation of type ``budget_exceeded``.
"""

import pytest

# Import the engine from the models package.
from models.policy import OraclePolicyEngine


def test_budget_cap_violation():
    """
    A workflow whose requested budget exceeds the declared budget cap must
    produce a single ``budget_exceeded`` violation.
    """
    # Construct a minimal workflow that triggers the budget rule.
    workflow = {
        "id": "test-workflow-001",
        "budget_cap": 100,
        "requested_budget": 150,
    }

    engine = OraclePolicyEngine()
    violations = engine.evaluate(workflow)

    # Exactly one violation should be reported.
    assert isinstance(violations, list)
    assert len(violations) == 1
    assert violations[0]["type"] == "budget_exceeded"
    # Verify that the details contain the original caps.
    details = violations[0]["details"]
    assert details["budget_cap"] == 100
    assert details["requested_budget"] == 150


def test_no_violation_when_budget_respected():
    """
    When the requested budget does not exceed the cap, no violations
    should be reported.
    """
    workflow = {
        "id": "test-workflow-002",
        "budget_cap": 200,
        "requested_budget": 150,
    }

    engine = OraclePolicyEngine()
    violations = engine.evaluate(workflow)

    assert violations == []