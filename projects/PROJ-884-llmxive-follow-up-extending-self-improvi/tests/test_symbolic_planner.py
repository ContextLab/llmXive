"""
Unit tests for the symbolic planner and exclusion logger.

The tests cover three scenarios:
1. A well‑formed puzzle where decomposition succeeds.
2. A puzzle with contradictory constraints that should be excluded.
3. A puzzle with an unparsable constraint that should be excluded.
"""

import json
from pathlib import Path

from code.symbolic.planner import SymbolicPlanner, DecompositionResult
from code.symbolic.exclusion_logger import ExclusionLogger, ExclusionEvent

# Helper to create a temporary exclusion logger that writes to a temp file
def make_logger(tmp_path):
    return ExclusionLogger(output_path=Path(tmp_path) / "exclusions.json")

def test_successful_decomposition(tmp_path):
    puzzle = {
        "metadata": {"source_id": "puzzle_success"},
        "constraints": [
            "A = 1",
            "B = 2",
            "ALLDIFF A B C",
            "C = 3",
            "A != B"
        ],
    }
    logger = make_logger(tmp_path)
    planner = SymbolicPlanner(exclusion_logger=logger)

    result: DecompositionResult = planner.decompose(puzzle)

    assert result.is_valid
    assert len(result.sub_goals) > 0
    # No exclusions should be logged
    assert logger.get_count() == 0

def test_contradiction_detection(tmp_path):
    # Contradictory: A = 1 and A = 2
    puzzle = {
        "metadata": {"source_id": "puzzle_contra"},
        "constraints": ["A = 1", "A = 2"],
    }
    logger = make_logger(tmp_path)
    planner = SymbolicPlanner(exclusion_logger=logger)

    result = planner.decompose(puzzle)

    assert not result.is_valid
    assert result.error_code == "CONTRADICTION_DETECTED"
    # One exclusion event should be recorded
    events = logger.get_events()
    assert len(events) == 1
    assert events[0].puzzle_id == "puzzle_contra"
    assert events[0].reason == "CONTRADICTION_DETECTED"

def test_parse_failure_logging(tmp_path):
    # Unparsable constraint string
    puzzle = {
        "metadata": {"source_id": "puzzle_bad"},
        "constraints": ["THIS IS NOT A VALID CONSTRAINT"],
    }
    logger = make_logger(tmp_path)
    planner = SymbolicPlanner(exclusion_logger=logger)

    result = planner.decompose(puzzle)

    assert not result.is_valid
    assert result.error_code == "PARSE_FAILURE"
    events = logger.get_events()
    assert len(events) == 1
    assert events[0].puzzle_id == "puzzle_bad"
    assert events[0].reason == "PARSE_FAILURE"