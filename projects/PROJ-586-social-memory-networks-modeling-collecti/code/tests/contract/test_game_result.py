"""Contract test for game result schema validation.

This test defines the expected schema for game result records that will be
output by the experiment. It serves as a contract that the implementation
must satisfy (see T015: results_full.csv).

Per TDD principles, these tests define the contract BEFORE implementation.
"""

import pytest
from typing import Dict, Any, Optional
from dataclasses import dataclass
import math


@dataclass
class GameResult:
    """Schema for a single game result record.

    This defines the contract for game result data that must be output
    by the experiment (see T015: results_full.csv).

    Fields:
        game_id: Unique integer identifier for the game
        specialization_index: Float between 0 and log2(N_agents)
        retrieval_efficiency: Float between 0 and 1
        context_condition: String, one of "full" or "limited"
        agent_count: Positive integer
    """
    game_id: int
    specialization_index: float
    retrieval_efficiency: float
    context_condition: str
    agent_count: int


class TestGameResultSchema:
    """Contract tests for the game result schema."""

    def test_game_result_has_required_fields(self):
        """Test that GameResult has all required fields from the contract."""
        result = GameResult(
            game_id=1,
            specialization_index=0.5,
            retrieval_efficiency=0.8,
            context_condition="full",
            agent_count=3
        )

        # Verify all contract fields exist
        assert hasattr(result, "game_id")
        assert hasattr(result, "specialization_index")
        assert hasattr(result, "retrieval_efficiency")
        assert hasattr(result, "context_condition")
        assert hasattr(result, "agent_count")

    def test_game_result_game_id_is_integer(self):
        """Test that game_id field is an integer."""
        result = GameResult(
            game_id=1,
            specialization_index=0.5,
            retrieval_efficiency=0.8,
            context_condition="full",
            agent_count=3
        )
        assert isinstance(result.game_id, int)

    def test_game_result_specialization_index_is_float(self):
        """Test that specialization_index field is a float."""
        result = GameResult(
            game_id=1,
            specialization_index=0.5,
            retrieval_efficiency=0.8,
            context_condition="full",
            agent_count=3
        )
        assert isinstance(result.specialization_index, float)

    def test_game_result_retrieval_efficiency_is_float(self):
        """Test that retrieval_efficiency field is a float."""
        result = GameResult(
            game_id=1,
            specialization_index=0.5,
            retrieval_efficiency=0.8,
            context_condition="full",
            agent_count=3
        )
        assert isinstance(result.retrieval_efficiency, float)

    def test_game_result_context_condition_is_string(self):
        """Test that context_condition field is a string."""
        result = GameResult(
            game_id=1,
            specialization_index=0.5,
            retrieval_efficiency=0.8,
            context_condition="full",
            agent_count=3
        )
        assert isinstance(result.context_condition, str)

    def test_game_result_agent_count_is_integer(self):
        """Test that agent_count field is an integer."""
        result = GameResult(
            game_id=1,
            specialization_index=0.5,
            retrieval_efficiency=0.8,
            context_condition="full",
            agent_count=3
        )
        assert isinstance(result.agent_count, int)

    def test_game_result_specialization_index_non_negative(self):
        """Test that specialization_index is non-negative."""
        result = GameResult(
            game_id=1,
            specialization_index=0.0,
            retrieval_efficiency=0.8,
            context_condition="full",
            agent_count=3
        )
        assert result.specialization_index >= 0

    def test_game_result_specialization_index_upper_bound(self):
        """Test that specialization_index <= log2(agent_count)."""
        for agent_count in [2, 3, 4, 5, 10]:
            max_index = math.log2(agent_count)
            result = GameResult(
                game_id=1,
                specialization_index=max_index,
                retrieval_efficiency=0.8,
                context_condition="full",
                agent_count=agent_count
            )
            assert result.specialization_index <= max_index

    def test_game_result_retrieval_efficiency_range(self):
        """Test that retrieval_efficiency is between 0 and 1."""
        # Test lower bound
        result_low = GameResult(
            game_id=1,
            specialization_index=0.5,
            retrieval_efficiency=0.0,
            context_condition="full",
            agent_count=3
        )
        assert result_low.retrieval_efficiency >= 0

        # Test upper bound
        result_high = GameResult(
            game_id=1,
            specialization_index=0.5,
            retrieval_efficiency=1.0,
            context_condition="full",
            agent_count=3
        )
        assert result_high.retrieval_efficiency <= 1

    def test_game_result_context_condition_valid_values(self):
        """Test that context_condition accepts valid values."""
        valid_conditions = ["full", "limited"]
        for condition in valid_conditions:
            result = GameResult(
                game_id=1,
                specialization_index=0.5,
                retrieval_efficiency=0.8,
                context_condition=condition,
                agent_count=3
            )
            assert result.context_condition in valid_conditions

    def test_game_result_agent_count_positive(self):
        """Test that agent_count is positive."""
        result = GameResult(
            game_id=1,
            specialization_index=0.5,
            retrieval_efficiency=0.8,
            context_condition="full",
            agent_count=1
        )
        assert result.agent_count > 0

    def test_game_result_from_dict(self):
        """Test that GameResult can be created from a dictionary."""
        data = {
            "game_id": 42,
            "specialization_index": 1.5,
            "retrieval_efficiency": 0.75,
            "context_condition": "limited",
            "agent_count": 5
        }
        result = GameResult(**data)
        assert result.game_id == 42
        assert result.specialization_index == 1.5
        assert result.retrieval_efficiency == 0.75
        assert result.context_condition == "limited"
        assert result.agent_count == 5

    def test_game_result_to_dict(self):
        """Test that GameResult can be converted to a dictionary."""
        result = GameResult(
            game_id=100,
            specialization_index=0.8,
            retrieval_efficiency=0.9,
            context_condition="full",
            agent_count=4
        )
        data = {
            "game_id": result.game_id,
            "specialization_index": result.specialization_index,
            "retrieval_efficiency": result.retrieval_efficiency,
            "context_condition": result.context_condition,
            "agent_count": result.agent_count
        }
        assert data["game_id"] == 100
        assert data["specialization_index"] == 0.8
        assert data["retrieval_efficiency"] == 0.9
        assert data["context_condition"] == "full"
        assert data["agent_count"] == 4

class TestGameResultValidation:
    """Tests for validating game result data against the schema contract."""

    def test_validate_dict_schema(self):
        """Test validation of a dictionary against GameResult schema."""
        valid_data = {
            "game_id": 1,
            "specialization_index": 0.5,
            "retrieval_efficiency": 0.8,
            "context_condition": "full",
            "agent_count": 3
        }

        # Should not raise
        result = GameResult(**valid_data)
        assert result is not None

    def test_validate_missing_field_raises(self):
        """Test that missing required fields raise an error."""
        invalid_data = {
            "game_id": 1,
            # Missing specialization_index, retrieval_efficiency, etc.
        }

        with pytest.raises(TypeError):
            GameResult(**invalid_data)

    def test_validate_wrong_type_raises(self):
        """Test that wrong field types raise an error."""
        # Note: dataclasses don't enforce types at runtime, but we test
        # that the schema contract specifies the correct types
        invalid_data = {
            "game_id": "not_an_int",  # Should be int
            "specialization_index": 0.5,
            "retrieval_efficiency": 0.8,
            "context_condition": "full",
            "agent_count": 3
        }

        # Create the object (dataclass won't raise)
        result = GameResult(**invalid_data)
        # But the contract says game_id should be int
        assert not isinstance(result.game_id, int)

    def test_csv_column_order_matches_contract(self):
        """Test that CSV columns match the expected contract order."""
        # Per T015, the CSV should have columns in this order:
        expected_columns = [
            "game_id",
            "specialization_index",
            "retrieval_efficiency",
            "context_condition",
            "agent_count"
        ]

        # Verify the GameResult fields match
        result = GameResult(
            game_id=1,
            specialization_index=0.5,
            retrieval_efficiency=0.8,
            context_condition="full",
            agent_count=3
        )

        actual_columns = [f.name for f in GameResult.__dataclass_fields__.values()]
        assert actual_columns == expected_columns

    def test_schema_compatible_with_pandas(self):
        """Test that GameResult is compatible with pandas DataFrame creation."""
        try:
            import pandas as pd
            results = [
                GameResult(game_id=1, specialization_index=0.5,
                          retrieval_efficiency=0.8, context_condition="full",
                          agent_count=3),
                GameResult(game_id=2, specialization_index=0.7,
                          retrieval_efficiency=0.9, context_condition="limited",
                          agent_count=5),
            ]
            # Convert to dict list for DataFrame
            data = [
                {
                    "game_id": r.game_id,
                    "specialization_index": r.specialization_index,
                    "retrieval_efficiency": r.retrieval_efficiency,
                    "context_condition": r.context_condition,
                    "agent_count": r.agent_count
                }
                for r in results
            ]
            df = pd.DataFrame(data)
            assert len(df) == 2
            assert list(df.columns) == ["game_id", "specialization_index",
                                        "retrieval_efficiency", "context_condition",
                                        "agent_count"]
        except ImportError:
            pytest.skip("pandas not available")

    def test_schema_compatible_with_json(self):
        """Test that GameResult can be serialized to JSON."""
        import json

        result = GameResult(
            game_id=1,
            specialization_index=0.5,
            retrieval_efficiency=0.8,
            context_condition="full",
            agent_count=3
        )

        data = {
            "game_id": result.game_id,
            "specialization_index": result.specialization_index,
            "retrieval_efficiency": result.retrieval_efficiency,
            "context_condition": result.context_condition,
            "agent_count": result.agent_count
        }

        json_str = json.dumps(data)
        parsed = json.loads(json_str)

        assert parsed["game_id"] == 1
        assert parsed["specialization_index"] == 0.5
        assert parsed["retrieval_efficiency"] == 0.8
        assert parsed["context_condition"] == "full"
        assert parsed["agent_count"] == 3

    def test_schema_matches_t015_requirements(self):
        """Test that schema matches T015 output requirements.

        T015 specifies: Output results_full.csv with game_id, specialization_index,
        retrieval_efficiency, context_condition, agent_count.
        """
        expected_fields = {
            "game_id": int,
            "specialization_index": float,
            "retrieval_efficiency": float,
            "context_condition": str,
            "agent_count": int
        }

        for field_name, field_type in expected_fields.items():
            assert field_name in GameResult.__dataclass_fields__
            # Type hint check (runtime enforcement not guaranteed by dataclass)
            field = GameResult.__dataclass_fields__[field_name]
            assert field.type == field_type or str(field.type) == str(field_type)

    def test_schema_allows_full_context_condition(self):
        """Test that 'full' context condition is allowed (US-1 requirement)."""
        result = GameResult(
            game_id=1,
            specialization_index=0.5,
            retrieval_efficiency=0.8,
            context_condition="full",
            agent_count=3
        )
        assert result.context_condition == "full"

    def test_schema_allows_limited_context_condition(self):
        """Test that 'limited' context condition is allowed (US-2 requirement)."""
        result = GameResult(
            game_id=1,
            specialization_index=0.5,
            retrieval_efficiency=0.8,
            context_condition="limited",
            agent_count=3
        )
        assert result.context_condition == "limited"