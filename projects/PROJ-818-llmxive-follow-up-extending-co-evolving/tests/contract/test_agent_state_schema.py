"""
Contract tests for agent state schema validation.
Validates that agent state files conform to the expected JSON structure.
"""
import json
import pytest
from pathlib import Path
import sys
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.contract.schemas import (
    AGENT_STATE_SCHEMA,
    validate_against_schema
)

class TestAgentStateSchema:
    """Tests for agent state schema validation."""

    def test_valid_sequential_agent_state(self, tmp_path):
        """Test that a valid sequential agent state passes validation."""
        valid_state = {
            "agent_id": "sequential_agent_001",
            "condition": "sequential",
            "state_version": 1,
            "generation_step": 10,
            "rule_sets": [
                {
                    "rule_id": "rule_001",
                    "rules": ["A -> B", "B -> C"],
                    "fitness_score": 0.85,
                    "task_domains": ["logic_proofs"]
                }
            ],
            "evaluation_stats": {
                "total_evaluations": 1000,
                "evaluations_by_domain": {
                    "logic_proofs": 1000
                }
            },
            "performance_history": [
                {
                    "step": 5,
                    "accuracy": 0.80,
                    "domains_tested": ["logic_proofs"]
                },
                {
                    "step": 10,
                    "accuracy": 0.85,
                    "domains_tested": ["logic_proofs"]
                }
            ]
        }

        validate_against_schema(valid_state, AGENT_STATE_SCHEMA, "agent_state")

    def test_valid_mixed_agent_state(self, tmp_path):
        """Test that a valid mixed agent state passes validation."""
        valid_state = {
            "agent_id": "mixed_agent_001",
            "condition": "mixed",
            "state_version": 2,
            "generation_step": 20,
            "rule_sets": [
                {
                    "rule_id": "rule_001",
                    "rules": ["A -> B", "B -> C"],
                    "fitness_score": 0.88,
                    "task_domains": ["logic_proofs", "grid_worlds"]
                },
                {
                    "rule_id": "rule_002",
                    "rules": ["avoid_red", "diagonal_paths"],
                    "fitness_score": 0.75,
                    "task_domains": ["grid_worlds"]
                }
            ],
            "evaluation_stats": {
                "total_evaluations": 2000,
                "evaluations_by_domain": {
                    "logic_proofs": 1000,
                    "grid_worlds": 1000
                }
            },
            "performance_history": [
                {
                    "step": 10,
                    "accuracy": 0.82,
                    "domains_tested": ["logic_proofs", "grid_worlds"]
                }
            ]
        }

        validate_against_schema(valid_state, AGENT_STATE_SCHEMA, "agent_state")

    def test_valid_coevolving_agent_state(self, tmp_path):
        """Test that a valid coevolving agent state passes validation."""
        valid_state = {
            "agent_id": "coevolving_agent_001",
            "condition": "coevolving",
            "state_version": 3,
            "generation_step": 15,
            "rule_sets": [
                {
                    "rule_id": "subpop1_rule_001",
                    "rules": ["A -> B", "B -> C"],
                    "fitness_score": 0.90,
                    "task_domains": ["logic_proofs"]
                },
                {
                    "rule_id": "subpop2_rule_001",
                    "rules": ["avoid_red", "diagonal_paths"],
                    "fitness_score": 0.85,
                    "task_domains": ["grid_worlds"]
                }
            ],
            "evaluation_stats": {
                "total_evaluations": 1500,
                "evaluations_by_domain": {
                    "logic_proofs": 750,
                    "grid_worlds": 750
                }
            },
            "performance_history": [
                {
                    "step": 5,
                    "accuracy": 0.78,
                    "domains_tested": ["logic_proofs"]
                },
                {
                    "step": 10,
                    "accuracy": 0.85,
                    "domains_tested": ["grid_worlds"]
                },
                {
                    "step": 15,
                    "accuracy": 0.88,
                    "domains_tested": ["logic_proofs", "grid_worlds"]
                }
            ]
        }

        validate_against_schema(valid_state, AGENT_STATE_SCHEMA, "agent_state")

    def test_missing_required_fields_fails(self, tmp_path):
        """Test that missing required fields fails validation."""
        invalid_state = {
            "agent_id": "test_agent",
            # Missing condition, state_version, rule_sets, evaluation_stats
        }

        with pytest.raises(ValueError):
            validate_against_schema(invalid_state, AGENT_STATE_SCHEMA, "agent_state")

    def test_invalid_condition_fails(self, tmp_path):
        """Test that invalid condition value fails validation."""
        invalid_state = {
            "agent_id": "test_agent",
            "condition": "invalid_condition",
            "state_version": 1,
            "rule_sets": [],
            "evaluation_stats": {
                "total_evaluations": 0,
                "evaluations_by_domain": {}
            }
        }

        with pytest.raises(ValueError, match="String 'invalid_condition' not in allowed values"):
            validate_against_schema(invalid_state, AGENT_STATE_SCHEMA, "agent_state")

    def test_negative_evaluation_count_fails(self, tmp_path):
        """Test that negative evaluation count fails validation."""
        invalid_state = {
            "agent_id": "test_agent",
            "condition": "sequential",
            "state_version": 1,
            "rule_sets": [],
            "evaluation_stats": {
                "total_evaluations": -1,
                "evaluations_by_domain": {}
            }
        }

        with pytest.raises(ValueError, match="Integer -1 is less than minimum"):
            validate_against_schema(invalid_state, AGENT_STATE_SCHEMA, "agent_state")

    def test_accuracy_out_of_range_fails(self, tmp_path):
        """Test that accuracy outside [0, 1] fails validation."""
        invalid_state = {
            "agent_id": "test_agent",
            "condition": "sequential",
            "state_version": 1,
            "rule_sets": [],
            "evaluation_stats": {
                "total_evaluations": 0,
                "evaluations_by_domain": {}
            },
            "performance_history": [
                {
                    "step": 1,
                    "accuracy": 1.5,  # Invalid: > 1
                    "domains_tested": ["logic_proofs"]
                }
            ]
        }

        with pytest.raises(ValueError, match="Number 1.5 is greater than maximum"):
            validate_against_schema(invalid_state, AGENT_STATE_SCHEMA, "agent_state")

    def test_load_and_validate_from_file(self, tmp_path):
        """Test loading an agent state file and validating it."""
        valid_state = {
            "agent_id": "test_agent_001",
            "condition": "sequential",
            "state_version": 1,
            "generation_step": 5,
            "rule_sets": [
                {
                    "rule_id": "rule_001",
                    "rules": ["A"],
                    "fitness_score": 0.5,
                    "task_domains": ["logic_proofs"]
                }
            ],
            "evaluation_stats": {
                "total_evaluations": 100,
                "evaluations_by_domain": {
                    "logic_proofs": 100
                }
            },
            "performance_history": []
        }

        # Write to file
        file_path = tmp_path / "agent_state.json"
        with open(file_path, 'w') as f:
            json.dump(valid_state, f)

        # Load and validate
        with open(file_path, 'r') as f:
            loaded_data = json.load(f)

        validate_against_schema(loaded_data, AGENT_STATE_SCHEMA, "agent_state")

    def test_empty_rule_sets_valid(self, tmp_path):
        """Test that empty rule_sets array is valid (edge case)."""
        valid_state = {
            "agent_id": "test_agent_001",
            "condition": "sequential",
            "state_version": 0,
            "generation_step": 0,
            "rule_sets": [],
            "evaluation_stats": {
                "total_evaluations": 0,
                "evaluations_by_domain": {}
            },
            "performance_history": []
        }

        validate_against_schema(valid_state, AGENT_STATE_SCHEMA, "agent_state")

    def test_multiple_rule_sets_valid(self, tmp_path):
        """Test that multiple rule_sets are valid."""
        valid_state = {
            "agent_id": "test_agent_001",
            "condition": "coevolving",
            "state_version": 5,
            "generation_step": 10,
            "rule_sets": [
                {
                    "rule_id": "rule_001",
                    "rules": ["A"],
                    "fitness_score": 0.5,
                    "task_domains": ["logic_proofs"]
                },
                {
                    "rule_id": "rule_002",
                    "rules": ["B"],
                    "fitness_score": 0.6,
                    "task_domains": ["grid_worlds"]
                },
                {
                    "rule_id": "rule_003",
                    "rules": ["C"],
                    "fitness_score": 0.7,
                    "task_domains": ["logic_proofs", "grid_worlds"]
                }
            ],
            "evaluation_stats": {
                "total_evaluations": 300,
                "evaluations_by_domain": {
                    "logic_proofs": 150,
                    "grid_worlds": 150
                }
            },
            "performance_history": []
        }

        validate_against_schema(valid_state, AGENT_STATE_SCHEMA, "agent_state")
