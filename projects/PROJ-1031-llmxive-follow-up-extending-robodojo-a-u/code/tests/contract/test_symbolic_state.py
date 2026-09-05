"""
Contract test for SymbolicState schema validation.
"""
import pytest
import sys
from pathlib import Path
import json

# Ensure src is importable
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.state_mapper import SymbolicState


class TestSymbolicStateContract:
    """Tests for SymbolicState schema compliance."""

    def test_symbolic_state_structure(self):
        """Verify SymbolicState has required fields including replan_support."""
        state = SymbolicState(
            task_id="test_003",
            predicates={"on": True},
            affordances={"obj": ["grab"]},
            replan_support=True
        )

        data = state.__dict__
        assert "task_id" in data
        assert "predicates" in data
        assert "affordances" in data
        assert "replan_support" in data
        assert isinstance(data["replan_support"], bool)
