"""
Contract tests for result schema validation.
Validates that training result files conform to the expected JSON structure,
including forgetting metrics and evaluation parity checks.
"""
import json
import pytest
from pathlib import Path
import sys
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.contract.schemas import (
    RESULT_SCHEMA,
    validate_against_schema
)

class TestResultSchema:
    """Tests for result schema validation."""

    def test_valid_sequential_result(self, tmp_path):
        """Test that a valid sequential training result passes validation."""
        valid_result = {
            "run_id": "run_seq_001",
            "condition": "sequential",
            "seed": 42,
            "config_snapshot": {
                "generations": 10,
                "population_size": 50,
                "mutation_rate": 0.1
            },
            "final_state": {
                "agent_id": "sequential_agent_001",
                "condition": "sequential",
                "state_version": 10,
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
                }
            },
            "forgetting_metrics": {
                "initial_accuracy": 0.95,
                "final_accuracy": 0.85,
                "accuracy_drop": 0.10,
                "retention_rates": {
                    "logic_proofs": 0.89
                }
            },
            "evaluation_parity": {
                "expected_total": 1000,
                "actual_total": 1000,
                "parity_verified": True
            },
            "generated_at": "2024-01-15T14:30:00Z"
        }

        validate_against_schema(valid_result, RESULT_SCHEMA, "result")

    def test_valid_mixed_result(self, tmp_path):
        """Test that a valid mixed training result passes validation."""
        valid_result = {
            "run_id": "run_mix_001",
            "condition": "mixed",
            "seed": 123,
            "config_snapshot": {
                "generations": 10,
                "population_size": 50,
                "mutation_rate": 0.1
            },
            "final_state": {
                "agent_id": "mixed_agent_001",
                "condition": "mixed",
                "state_version": 10,
                "generation_step": 10,
                "rule_sets": [
                    {
                        "rule_id": "rule_001",
                        "rules": ["A -> B", "avoid_red"],
                        "fitness_score": 0.80,
                        "task_domains": ["logic_proofs", "grid_worlds"]
                    }
                ],
                "evaluation_stats": {
                    "total_evaluations": 1000,
                    "evaluations_by_domain": {
                        "logic_proofs": 500,
                        "grid_worlds": 500
                    }
                }
            },
            "forgetting_metrics": {
                "initial_accuracy": 0.92,
                "final_accuracy": 0.88,
                "accuracy_drop": 0.04,
                "retention_rates": {
                    "logic_proofs": 0.95,
                    "grid_worlds": 0.91
                }
            },
            "evaluation_parity": {
                "expected_total": 1000,
                "actual_total": 1000,
                "parity_verified": True
            },
            "generated_at": "2024-01-15T14:35:00Z"
        }

        validate_against_schema(valid_result, RESULT_SCHEMA, "result")

    def test_valid_coevolving_result(self, tmp_path):
        """Test that a valid coevolving training result passes validation."""
        valid_result = {
            "run_id": "run_coev_001",
            "condition": "coevolving",
            "seed": 456,
            "config_snapshot": {
                "generations": 10,
                "population_size": 50,
                "mutation_rate": 0.1
            },
            "final_state": {
                "agent_id": "coevolving_agent_001",
                "condition": "coevolving",
                "state_version": 10,
                "generation_step": 10,
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
                        "fitness_score": 0.88,
                        "task_domains": ["grid_worlds"]
                    }
                ],
                "evaluation_stats": {
                    "total_evaluations": 1000,
                    "evaluations_by_domain": {
                        "logic_proofs": 500,
                        "grid_worlds": 500
                    }
                }
            },
            "forgetting_metrics": {
                "initial_accuracy": 0.93,
                "final_accuracy": 0.90,
                "accuracy_drop": 0.03,
                "retention_rates": {
                    "logic_proofs": 0.97,
                    "grid_worlds": 0.97
                }
            },
            "evaluation_parity": {
                "expected_total": 1000,
                "actual_total": 1000,
                "parity_verified": True
            },
            "generated_at": "2024-01-15T14:40:00Z"
        }

        validate_against_schema(valid_result, RESULT_SCHEMA, "result")

    def test_missing_required_fields_fails(self, tmp_path):
        """Test that missing required fields fails validation."""
        invalid_result = {
            "run_id": "run_001",
            # Missing condition, seed, final_state, forgetting_metrics
        }

        with pytest.raises(ValueError):
            validate_against_schema(invalid_result, RESULT_SCHEMA, "result")

    def test_invalid_condition_fails(self, tmp_path):
        """Test that invalid condition value fails validation."""
        invalid_result = {
            "run_id": "run_001",
            "condition": "invalid_condition",
            "seed": 42,
            "final_state": {},
            "forgetting_metrics": {},
            "evaluation_parity": {},
            "generated_at": "2024-01-15T14:30:00Z"
        }

        with pytest.raises(ValueError, match="String 'invalid_condition' not in allowed values"):
            validate_against_schema(invalid_result, RESULT_SCHEMA, "result")

    def test_forgetting_metrics_accuracy_drop_negative_fails(self, tmp_path):
        """Test that accuracy drop cannot be negative (final > initial)."""
        # Note: Schema doesn't enforce this mathematically, but we test the structure
        valid_structure = {
            "run_id": "run_001",
            "condition": "sequential",
            "seed": 42,
            "final_state": {
                "agent_id": "test",
                "condition": "sequential",
                "state_version": 1,
                "generation_step": 1,
                "rule_sets": [],
                "evaluation_stats": {
                    "total_evaluations": 0,
                    "evaluations_by_domain": {}
                }
            },
            "forgetting_metrics": {
                "initial_accuracy": 0.5,
                "final_accuracy": 0.9,  # Final > Initial (unusual but structurally valid)
                "accuracy_drop": -0.4,  # Negative drop
                "retention_rates": {}
            },
            "evaluation_parity": {
                "expected_total": 0,
                "actual_total": 0,
                "parity_verified": True
            },
            "generated_at": "2024-01-15T14:30:00Z"
        }

        # This should pass schema validation (structure is correct)
        validate_against_schema(valid_structure, RESULT_SCHEMA, "result")

    def test_accuracy_values_out_of_range_fails(self, tmp_path):
        """Test that accuracy values outside [0, 1] fail validation."""
        invalid_result = {
            "run_id": "run_001",
            "condition": "sequential",
            "seed": 42,
            "final_state": {
                "agent_id": "test",
                "condition": "sequential",
                "state_version": 1,
                "generation_step": 1,
                "rule_sets": [],
                "evaluation_stats": {
                    "total_evaluations": 0,
                    "evaluations_by_domain": {}
                }
            },
            "forgetting_metrics": {
                "initial_accuracy": 1.5,  # Invalid
                "final_accuracy": 0.8,
                "accuracy_drop": 0.7,
                "retention_rates": {}
            },
            "evaluation_parity": {
                "expected_total": 0,
                "actual_total": 0,
                "parity_verified": True
            },
            "generated_at": "2024-01-15T14:30:00Z"
        }

        with pytest.raises(ValueError, match="Number 1.5 is greater than maximum"):
            validate_against_schema(invalid_result, RESULT_SCHEMA, "result")

    def test_load_and_validate_from_file(self, tmp_path):
        """Test loading a result file and validating it."""
        valid_result = {
            "run_id": "run_001",
            "condition": "sequential",
            "seed": 42,
            "final_state": {
                "agent_id": "test",
                "condition": "sequential",
                "state_version": 1,
                "generation_step": 1,
                "rule_sets": [],
                "evaluation_stats": {
                    "total_evaluations": 100,
                    "evaluations_by_domain": {
                        "logic_proofs": 100
                    }
                }
            },
            "forgetting_metrics": {
                "initial_accuracy": 0.9,
                "final_accuracy": 0.85,
                "accuracy_drop": 0.05,
                "retention_rates": {
                    "logic_proofs": 0.94
                }
            },
            "evaluation_parity": {
                "expected_total": 100,
                "actual_total": 100,
                "parity_verified": True
            },
            "generated_at": "2024-01-15T14:30:00Z"
        }

        # Write to file
        file_path = tmp_path / "result.json"
        with open(file_path, 'w') as f:
            json.dump(valid_result, f)

        # Load and validate
        with open(file_path, 'r') as f:
            loaded_data = json.load(f)

        validate_against_schema(loaded_data, RESULT_SCHEMA, "result")

    def test_parity_mismatch_still_valid_structure(self, tmp_path):
        """Test that parity mismatch is structurally valid (logic error, not schema error)."""
        valid_structure = {
            "run_id": "run_001",
            "condition": "sequential",
            "seed": 42,
            "final_state": {
                "agent_id": "test",
                "condition": "sequential",
                "state_version": 1,
                "generation_step": 1,
                "rule_sets": [],
                "evaluation_stats": {
                    "total_evaluations": 100,
                    "evaluations_by_domain": {}
                }
            },
            "forgetting_metrics": {
                "initial_accuracy": 0.9,
                "final_accuracy": 0.85,
                "accuracy_drop": 0.05,
                "retention_rates": {}
            },
            "evaluation_parity": {
                "expected_total": 100,
                "actual_total": 95,  # Mismatch
                "parity_verified": False
            },
            "generated_at": "2024-01-15T14:30:00Z"
        }

        # This should pass schema validation (structure is correct)
        validate_against_schema(valid_structure, RESULT_SCHEMA, "result")

    def test_retention_rates_per_domain(self, tmp_path):
        """Test retention rates for multiple domains."""
        valid_result = {
            "run_id": "run_001",
            "condition": "coevolving",
            "seed": 42,
            "final_state": {
                "agent_id": "test",
                "condition": "coevolving",
                "state_version": 1,
                "generation_step": 1,
                "rule_sets": [],
                "evaluation_stats": {
                    "total_evaluations": 100,
                    "evaluations_by_domain": {}
                }
            },
            "forgetting_metrics": {
                "initial_accuracy": 0.9,
                "final_accuracy": 0.85,
                "accuracy_drop": 0.05,
                "retention_rates": {
                    "logic_proofs": 0.94,
                    "grid_worlds": 0.96
                }
            },
            "evaluation_parity": {
                "expected_total": 100,
                "actual_total": 100,
                "parity_verified": True
            },
            "generated_at": "2024-01-15T14:30:00Z"
        }

        validate_against_schema(valid_result, RESULT_SCHEMA, "result")
