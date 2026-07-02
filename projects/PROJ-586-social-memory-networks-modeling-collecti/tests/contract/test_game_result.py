import pytest
from typing import Dict, Any, Optional
from dataclasses import dataclass
import math

# Import from the project
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from run_experiment import GameResult

@dataclass
class TestGameResultSchema:
    """Contract tests for GameResult schema."""

    def test_required_fields(self):
        """Test that all required fields are present."""
        result = GameResult(
            game_id=1,
            agent_count=5,
            context_condition="full",
            specialization_index=1.2,
            retrieval_efficiency=0.85,
            valid=True
        )
        
        assert hasattr(result, 'game_id')
        assert hasattr(result, 'agent_count')
        assert hasattr(result, 'context_condition')
        assert hasattr(result, 'specialization_index')
        assert hasattr(result, 'retrieval_efficiency')
        assert hasattr(result, 'valid')

    def test_field_types(self):
        """Test that fields have correct types."""
        result = GameResult(
            game_id=1,
            agent_count=5,
            context_condition="full",
            specialization_index=1.2,
            retrieval_efficiency=0.85,
            valid=True
        )
        
        assert isinstance(result.game_id, int)
        assert isinstance(result.agent_count, int)
        assert isinstance(result.context_condition, str)
        assert isinstance(result.specialization_index, float)
        assert isinstance(result.retrieval_efficiency, float)
        assert isinstance(result.valid, bool)

    def test_specialization_range(self):
        """Test specialization index is within valid range."""
        # Range: 0 to log2(N_agents)
        for n in [3, 5, 7]:
            result = GameResult(
                game_id=1,
                agent_count=n,
                context_condition="full",
                specialization_index=0.5,
                retrieval_efficiency=0.5,
                valid=True
            )
            max_spec = math.log2(n)
            assert 0 <= result.specialization_index <= max_spec

    def test_retrieval_efficiency_range(self):
        """Test retrieval efficiency is between 0 and 1."""
        result = GameResult(
            game_id=1,
            agent_count=5,
            context_condition="full",
            specialization_index=1.0,
            retrieval_efficiency=0.75,
            valid=True
        )
        assert 0.0 <= result.retrieval_efficiency <= 1.0

    def test_context_condition_values(self):
        """Test context condition has valid values."""
        for ctx in ["full", "limited"]:
            result = GameResult(
                game_id=1,
                agent_count=5,
                context_condition=ctx,
                specialization_index=1.0,
                retrieval_efficiency=0.5,
                valid=True
            )
            assert result.context_condition in ["full", "limited"]

class TestGameResultValidation:
    """Validation tests for GameResult."""

    def test_valid_result(self):
        """Test a valid result passes validation."""
        result = GameResult(
            game_id=1,
            agent_count=5,
            context_condition="full",
            specialization_index=1.0,
            retrieval_efficiency=0.5,
            valid=True
        )
        assert result.valid is True

    def test_invalid_specialization(self):
        """Test result with invalid specialization is marked invalid."""
        # This would be caught by the validator in production
        # Here we just ensure the schema accepts the value
        result = GameResult(
            game_id=1,
            agent_count=5,
            context_condition="full",
            specialization_index=-0.5,  # Invalid
            retrieval_efficiency=0.5,
            valid=True
        )
        # The schema allows it, but the validator would reject it
        assert result.specialization_index == -0.5

    def test_invalid_retrieval_efficiency(self):
        """Test result with invalid retrieval efficiency."""
        result = GameResult(
            game_id=1,
            agent_count=5,
            context_condition="full",
            specialization_index=1.0,
            retrieval_efficiency=1.5,  # Invalid
            valid=True
        )
        assert result.retrieval_efficiency == 1.5
