"""
Unit tests for session filtering logic in code/ingestion.py.

Verifies:
- Sessions with < 3 turns are excluded.
- Sessions with >= 3 turns are included.
- Null text handling (if applicable in ingestion logic).
"""
import pytest
from pathlib import Path
import sys

# Add project root to path for imports if running standalone
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.ingestion import filter_sessions_by_turns

def test_filter_sessions_excludes_less_than_3():
    """Test that sessions with fewer than 3 turns are excluded."""
    data = [
        {"session_id": "s1", "turns": [{"text": "Hi"}, {"text": "Hello"}]},  # 2 turns
        {"session_id": "s2", "turns": []},  # 0 turns
        {"session_id": "s3", "turns": [{"text": "A"}]},  # 1 turn
    ]
    result = filter_sessions_by_turns(data, min_turns=3)
    assert len(result) == 0
    assert all(s["session_id"] not in ["s1", "s2", "s3"] for s in result)

def test_filter_sessions_includes_3_or_more():
    """Test that sessions with 3 or more turns are included."""
    data = [
        {"session_id": "s1", "turns": [{"text": "A"}, {"text": "B"}, {"text": "C"}]},  # 3 turns
        {"session_id": "s2", "turns": [{"text": "A"}, {"text": "B"}, {"text": "C"}, {"text": "D"}]},  # 4 turns
    ]
    result = filter_sessions_by_turns(data, min_turns=3)
    assert len(result) == 2
    session_ids = [s["session_id"] for s in result]
    assert "s1" in session_ids
    assert "s2" in session_ids

def test_filter_sessions_mixed():
    """Test filtering on a mixed dataset."""
    data = [
        {"session_id": "s1", "turns": [{"text": "A"}, {"text": "B"}]},  # 2 turns (exclude)
        {"session_id": "s2", "turns": [{"text": "A"}, {"text": "B"}, {"text": "C"}]},  # 3 turns (include)
        {"session_id": "s3", "turns": [{"text": "A"}]},  # 1 turn (exclude)
        {"session_id": "s4", "turns": [{"text": "A"}, {"text": "B"}, {"text": "C"}, {"text": "D"}, {"text": "E"}]},  # 5 turns (include)
    ]
    result = filter_sessions_by_turns(data, min_turns=3)
    assert len(result) == 2
    session_ids = [s["session_id"] for s in result]
    assert "s2" in session_ids
    assert "s4" in session_ids
    assert "s1" not in session_ids
    assert "s3" not in session_ids
