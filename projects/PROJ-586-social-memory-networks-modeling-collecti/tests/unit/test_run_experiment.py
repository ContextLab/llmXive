import pytest
import os
import sys
from pathlib import Path
import tempfile
import pandas as pd
import numpy as np

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from run_experiment import parse_agent_counts, GameResult, run_single_game

class TestRunExperiment:
    """Tests for run_experiment.py functionality."""

    def test_parse_agent_counts_valid(self):
        """Test parsing valid agent count strings."""
        assert parse_agent_counts("3") == [3]
        assert parse_agent_counts("3,5,7") == [3, 5, 7]
        assert parse_agent_counts(" 3 , 5 , 7 ") == [3, 5, 7]

    def test_parse_agent_counts_invalid(self):
        """Test parsing invalid agent count strings."""
        with pytest.raises(ValueError):
            parse_agent_counts("abc")
        with pytest.raises(ValueError):
            parse_agent_counts("3,abc,7")

    def test_game_result_schema(self):
        """Test GameResult dataclass schema."""
        result = GameResult(
            game_id=1,
            agent_count=5,
            context_condition="full",
            specialization_index=1.5,
            retrieval_efficiency=0.8,
            valid=True
        )
        assert result.game_id == 1
        assert result.agent_count == 5
        assert result.context_condition == "full"
        assert result.specialization_index == 1.5
        assert result.retrieval_efficiency == 0.8
        assert result.valid is True

    def test_run_single_game_full_context(self):
        """Test single game simulation with full context."""
        result = run_single_game(
            game_id=0,
            agent_count=3,
            context_condition="full",
            seed=42
        )
        assert result is not None
        assert result.game_id == 0
        assert result.agent_count == 3
        assert result.context_condition == "full"
        assert result.valid is True
        assert result.specialization_index >= 0
        assert 0 <= result.retrieval_efficiency <= 1.0

    def test_run_single_game_limited_context(self):
        """Test single game simulation with limited context."""
        result = run_single_game(
            game_id=0,
            agent_count=3,
            context_condition="limited",
            seed=42
        )
        assert result is not None
        assert result.valid is True
        assert result.specialization_index >= 0

    def test_reproducibility(self):
        """Test that same seed produces same results."""
        result1 = run_single_game(0, 3, "full", seed=123)
        result2 = run_single_game(0, 3, "full", seed=123)
        
        assert result1.specialization_index == result2.specialization_index
        assert result1.retrieval_efficiency == result2.retrieval_efficiency

    def test_different_agent_counts(self):
        """Test simulation with different agent counts."""
        for count in [3, 5, 7]:
            result = run_single_game(0, count, "full", seed=42)
            assert result is not None
            assert result.agent_count == count
            assert result.valid is True
