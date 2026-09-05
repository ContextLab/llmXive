"""
Unit tests for symbolic state mapping logic.
"""
import pytest
import sys
import numpy as np
from pathlib import Path

# Ensure src is importable
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.state_mapper import StateMapper, SymbolicState, create_symbolic_state


class TestStateMapper:
    """Tests for the StateMapper class."""

    def test_mapper_initialization(self):
        """Verify StateMapper initializes with config."""
        mapper = StateMapper()
        assert mapper is not None

    def test_symbolic_state_dataclass(self):
        """Verify SymbolicState is a valid dataclass."""
        state = SymbolicState(
            task_id="test_001",
            predicates={"on_table": True},
            affordances={"cup": ["graspable"]},
            replan_support=True
        )
        assert state.task_id == "test_001"
        assert state.replan_support is True

    def test_create_symbolic_state(self):
        """Verify the factory function creates a valid state."""
        # Mock input embedding
        mock_embedding = np.random.rand(10, 128).astype(np.float32)
        mock_metadata = {"task_id": "meta_1", "replan": True}

        state = create_symbolic_state(mock_embedding, mock_metadata)
        assert isinstance(state, SymbolicState)
        assert state.task_id == "meta_1"
        assert state.replan_support is True
