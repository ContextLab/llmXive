"""
Contract tests for agent state schema validation.
Ensures agent state snapshots conform to the defined JSON schema.
"""
import pytest
from tests.contract.schemas import validate_agent_state

class TestAgentStateSchema:
    """Tests for the agent state schema validator."""

    def test_valid_sequential_agent_state(self):
        """Test a valid state for a SequentialAgent."""
        valid_state = {
            "agent_type": "SequentialAgent",
            "config": {
                "max_generations": 100,
                "population_size": 50
            },
            "population": [
                {
                    "id": "rule_set_1",
                    "rules": ["A -> B", "B -> C"],
                    "fitness": 0.85
                },
                {
                    "id": "rule_set_2",
                    "rules": ["X -> Y"],
                    "fitness": 0.72
                }
            ],
            "evaluation_stats": {
                "total_evaluations": 5000,
                "by_task": {
                    "logic": 2500,
                    "grid": 2500
                }
            },
            "generation_history": [
                {"gen": 0, "avg_fitness": 0.5},
                {"gen": 1, "avg_fitness": 0.6}
            ]
        }
        result = validate_agent_state(valid_state)
        assert result.valid, f"Validation failed: {result.errors}"

    def test_valid_coevolving_agent_state(self):
        """Test a valid state for a CoevolvingAgent with sub-populations."""
        valid_state = {
            "agent_type": "CoevolvingAgent",
            "config": {
                "num_subpops": 2,
                "exchange_rate": 0.1
            },
            "population": [
                {
                    "id": "subpop_1_rule_1",
                    "rules": ["Avoid Red"],
                    "fitness": 0.9
                },
                {
                    "id": "subpop_2_rule_1",
                    "rules": ["Diagonal Path"],
                    "fitness": 0.88
                }
            ],
            "evaluation_stats": {
                "total_evaluations": 10000,
                "by_task": {
                    "grid_avoid_red": 5000,
                    "grid_diagonal": 5000
                }
            },
            "generation_history": []
        }
        result = validate_agent_state(valid_state)
        assert result.valid, f"Validation failed: {result.errors}"

    def test_invalid_missing_agent_type(self):
        """Test that missing agent_type causes validation failure."""
        invalid_state = {
            "config": {},
            "population": [],
            "evaluation_stats": {"total_evaluations": 0, "by_task": {}}
        }
        result = validate_agent_state(invalid_state)
        assert not result.valid
        assert any("Missing required property 'agent_type'" in str(e.message) for e in result.errors)

    def test_invalid_wrong_fitness_type(self):
        """Test that non-numeric fitness causes validation failure."""
        invalid_state = {
            "agent_type": "MixedAgent",
            "config": {},
            "population": [
                {
                    "id": "r1",
                    "rules": ["A"],
                    "fitness": "high" # Should be number
                }
            ],
            "evaluation_stats": {"total_evaluations": 0, "by_task": {}}
        }
        result = validate_agent_state(invalid_state)
        assert not result.valid
        assert any("Expected type 'number'" in str(e.message) for e in result.errors)

    def test_invalid_missing_evaluation_stats(self):
        """Test missing evaluation_stats."""
        invalid_state = {
            "agent_type": "SequentialAgent",
            "config": {},
            "population": []
        }
        result = validate_agent_state(invalid_state)
        assert not result.valid
        assert any("Missing required property 'evaluation_stats'" in str(e.message) for e in result.errors)
