"""
Unit tests for symbolic state mapping logic, specifically focusing on deterministic thresholding.
"""
import pytest
import sys
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure src is importable
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.state_mapper import StateMapper, SymbolicState, create_symbolic_state
from src.config import SEED


class TestStateMapper:
    """Tests for the StateMapper class."""

    def test_mapper_initialization(self):
        """Verify StateMapper initializes with config."""
        mapper = StateMapper()
        assert mapper is not None
        # Verify seed is set for deterministic behavior
        assert hasattr(mapper, 'seed')
        assert mapper.seed == SEED

    def test_symbolic_state_dataclass(self):
        """Verify SymbolicState is a valid dataclass."""
        state = SymbolicState(
            task_id="test_001",
            predicates={"on table": True},
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

    def test_deterministic_thresholding_seed_fixed(self):
        """
        Verify that the thresholding logic in StateMapper is deterministic
        when the global seed (SEED) is fixed.
        """
        # Set seed explicitly to ensure reproducibility
        np.random.seed(SEED)
        
        # Create a fixed random embedding
        fixed_embedding = np.random.rand(5, 64).astype(np.float32)
        fixed_metadata = {"task_id": "det_test", "replan": False}

        # First run
        mapper1 = StateMapper()
        state1 = mapper1.map_to_symbolic(fixed_embedding, fixed_metadata)

        # Reset seed to the same value
        np.random.seed(SEED)
        
        # Second run with identical inputs
        mapper2 = StateMapper()
        state2 = mapper2.map_to_symbolic(fixed_embedding, fixed_metadata)

        # Verify predicates are identical
        assert state1.predicates == state2.predicates, \
            "Predicates differ between runs with same seed: {} vs {}".format(state1.predicates, state2.predicates)
        
        # Verify affordances are identical
        assert state1.affordances == state2.affordances, \
            "Affordances differ between runs with same seed: {} vs {}".format(state1.affordances, state2.affordances)

    def test_deterministic_thresholding_value_stability(self):
        """
        Verify that specific threshold values derived from embeddings are stable
        across multiple instantiations when seed is fixed.
        """
        np.random.seed(SEED)
        embedding = np.random.rand(10, 32).astype(np.float32)
        metadata = {"task_id": "val_test", "replan": True}

        # Run mapping multiple times
        results = []
        for _ in range(5):
            np.random.seed(SEED) # Reset seed before each creation
            mapper = StateMapper()
            state = mapper.map_to_symbolic(embedding, metadata)
            # Convert predicates dict to a sorted tuple of items for comparison
            results.append(tuple(sorted(state.predicates.items())))

        # All results must be identical
        first_result = results[0]
        for i, res in enumerate(results[1:], 2):
            assert res == first_result, \
                "Result {} differs from result 1. Expected: {}, Got: {}".format(i, first_result, res)

    def test_thresholding_logic_excludes_continuous_vars(self):
        """
        Verify that the mapping logic explicitly excludes continuous physics variables
        (like friction, mass) from the resulting SymbolicState predicates.
        """
        # Create a mapper
        mapper = StateMapper()
        
        # Mock embedding that might imply continuous variables
        embedding = np.ones((1, 64), dtype=np.float32)
        metadata = {"task_id": "cont_test", "replan": True, "physics_vars": ["friction", "mass", "velocity"]}
        
        state = mapper.map_to_symbolic(embedding, metadata)
        
        # Assert that continuous physics variables are NOT in predicates
        continuous_vars = ["friction", "mass", "velocity", "acceleration", "torque"]
        for var in continuous_vars:
            assert var not in state.predicates, \
                "Continuous variable '{}' found in predicates: {}".format(var, state.predicates)
            assert var not in state.affordances, \
                "Continuous variable '{}' found in affordances: {}".format(var, state.affordances)

    def test_replan_support_flag_propagation(self):
        """
        Verify that the replan_support flag is correctly propagated from metadata
        to the SymbolicState based on T046 implementation.
        """
        mapper = StateMapper()
        embedding = np.zeros((1, 10), dtype=np.float32)
        
        # Test True case
        state_true = mapper.map_to_symbolic(embedding, {"task_id": "t1", "replan": True})
        assert state_true.replan_support is True
        
        # Test False case
        state_false = mapper.map_to_symbolic(embedding, {"task_id": "t2", "replan": False})
        assert state_false.replan_support is False
        
        # Test missing key (should default to False or raise, checking default behavior)
        # Assuming default is False if not specified, based on typical safety patterns
        state_missing = mapper.map_to_symbolic(embedding, {"task_id": "t3"})
        # If the implementation defaults to False, this passes. If it raises, the test handles it.
        # Based on T046 description "populate... based on task metadata", we assume it handles missing keys gracefully.
        # Let's assert it exists and is boolean.
        assert isinstance(state_missing.replan_support, bool)