"""
Unit tests for the symbolic planner and related components.

The tests cover three scenarios:
1. A puzzle with contradictory constraints – should be excluded with
   error code ``CONTRADICTION_DETECTED``.
2. A puzzle with an unparsable constraint – should be excluded with
   error code ``PARSE_FAILURE``.
3. A well‑formed puzzle – should produce a valid decomposition with
   sub‑goals.
"""

import json
import tempfile
from pathlib import Path

import pytest

# Import the objects under test
from code.symbolic.planner import SymbolicPlanner, DecompositionResult
from code.symbolic.exclusion_logger import ExclusionLogger, ExclusionEvent
from code.exceptions import CONTRADICTION_DETECTED, PARSE_FAILURE


@pytest.fixture
def temp_exclusion_file():
    """Create a temporary file path for the exclusion log."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "exclusions.json"
        # Ensure the file does not exist initially
        if path.exists():
            path.unlink()
        yield path
        # Cleanup is automatic with TemporaryDirectory


def test_contradictory_constraints(temp_exclusion_file):
    """Puzzle where two value assignments conflict should be excluded."""
    puzzle = {
        "metadata": {"source_id": "puzzle_contra"},
        "constraints": ["A = 5", "A = 6"]  # Direct contradiction
    }

    logger = ExclusionLogger(output_path=temp_exclusion_file)
    planner = SymbolicPlanner(exclusion_logger=logger)

    result: DecompositionResult = planner.decompose(puzzle)

    # The planner should mark the puzzle as invalid and use the correct code
    assert not result.is_valid
    assert result.error_code == CONTRADICTION_DETECTED
    # The exclusion log should contain exactly one event
    events = logger.get_events()
    assert len(events) == 1
    ev: ExclusionEvent = events[0]
    assert ev.puzzle_id == "puzzle_contra"
    assert ev.reason == CONTRADICTION_DETECTED
    assert ev.error_code == CONTRADICTION_DETECTED


def test_unparsable_constraint(temp_exclusion_file):
    """Puzzle with a malformed constraint string should be excluded."""
    puzzle = {
        "metadata": {"source_id": "puzzle_unparse"},
        "constraints": ["THIS IS NOT A VALID CONSTRAINT"]
    }

    logger = ExclusionLogger(output_path=temp_exclusion_file)
    planner = SymbolicPlanner(exclusion_logger=logger)

    result: DecompositionResult = planner.decompose(puzzle)

    assert not result.is_valid
    assert result.error_code == PARSE_FAILURE
    events = logger.get_events()
    assert len(events) == 1
    ev = events[0]
    assert ev.puzzle_id == "puzzle_unparse"
    assert ev.reason == PARSE_FAILURE
    assert ev.error_code == PARSE_FAILURE


def test_well_formed_puzzle(temp_exclusion_file):
    """A puzzle with parsable, non‑contradictory constraints should succeed."""
    puzzle = {
        "metadata": {"source_id": "puzzle_good"},
        "constraints": [
            "X = Y",
            "ALLDIFF X Y Z",
            "Z = 3"
        ]
    }

    logger = ExclusionLogger(output_path=temp_exclusion_file)
    planner = SymbolicPlanner(exclusion_logger=logger)

    result: DecompositionResult = planner.decompose(puzzle)

    # Should be valid and contain sub‑goals
    assert result.is_valid
    assert result.error_code is None
    assert isinstance(result.sub_goals, list)
    assert len(result.sub_goals) > 0

    # No exclusion events should be logged
    assert logger.get_count() == 0

    # Verify that sub‑goals have the expected structure
    for sg in result.sub_goals:
        assert "id" in sg.__dict__
        assert "description" in sg.__dict__
        assert "constraints" in sg.__dict__

# Ensure the test module can be run directly (optional)
if __name__ == "__main__":
    pytest.main([__file__])