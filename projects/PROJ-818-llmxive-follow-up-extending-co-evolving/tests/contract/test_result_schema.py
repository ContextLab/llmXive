"""
Contract tests for result schema validation.
Ensures training results and forgetting metrics conform to the defined JSON schema.
"""
import pytest
from tests.contract.schemas import validate_result

class TestResultSchema:
    """Tests for the result schema validator."""

    def test_valid_sequential_result(self):
        """Test a valid result for a Sequential training run."""
        valid_result = {
            "run_id": "seq_run_001",
            "condition": "sequential",
            "metrics": {
                "initial_accuracy": 0.95,
                "final_accuracy": 0.88,
                "forgetting_rate": 0.07,
                "retention_rates": {
                    "rule_A": 0.90,
                    "rule_B": 0.85
                }
            },
            "parity_data": {
                "total_evaluations": 100000,
                "checksum": "sha256_hash_string"
            },
            "agent_state_snapshot": {
                "agent_type": "SequentialAgent",
                "config": {},
                "population": [],
                "evaluation_stats": {"total_evaluations": 100000, "by_task": {}}
            }
        }
        result = validate_result(valid_result)
        assert result.valid, f"Validation failed: {result.errors}"

    def test_valid_coevolving_result(self):
        """Test a valid result for a Coevolving training run."""
        valid_result = {
            "run_id": "coev_run_005",
            "condition": "coevolving",
            "metrics": {
                "initial_accuracy": 0.92,
                "final_accuracy": 0.91,
                "forgetting_rate": 0.01,
                "retention_rates": {
                    "rule_X": 0.95,
                    "rule_Y": 0.94
                }
            },
            "parity_data": {
                "total_evaluations": 100000,
                "checksum": "sha256_hash_string_2"
            },
            "agent_state_snapshot": {}
        }
        result = validate_result(valid_result)
        assert result.valid, f"Validation failed: {result.errors}"

    def test_invalid_wrong_condition_enum(self):
        """Test that invalid condition value causes validation failure."""
        invalid_result = {
            "run_id": "bad_run",
            "condition": "invalid_condition", # Not in enum
            "metrics": {
                "initial_accuracy": 0.5,
                "final_accuracy": 0.5,
                "forgetting_rate": 0.0
            },
            "parity_data": {
                "total_evaluations": 0,
                "checksum": ""
            }
        }
        result = validate_result(invalid_result)
        assert not result.valid
        assert any("not in enum" in str(e.message) for e in result.errors)

    def test_invalid_missing_forgetting_rate(self):
        """Test missing forgetting_rate in metrics."""
        invalid_result = {
            "run_id": "bad_run",
            "condition": "mixed",
            "metrics": {
                "initial_accuracy": 0.5,
                "final_accuracy": 0.5
                # Missing forgetting_rate
            },
            "parity_data": {
                "total_evaluations": 0,
                "checksum": ""
            }
        }
        result = validate_result(invalid_result)
        assert not result.valid
        assert any("Missing required property 'forgetting_rate'" in str(e.message) for e in result.errors)

    def test_invalid_missing_parity_data(self):
        """Test missing parity_data."""
        invalid_result = {
            "run_id": "bad_run",
            "condition": "sequential",
            "metrics": {
                "initial_accuracy": 0.5,
                "final_accuracy": 0.5,
                "forgetting_rate": 0.0
            }
            # Missing parity_data
        }
        result = validate_result(invalid_result)
        assert not result.valid
        assert any("Missing required property 'parity_data'" in str(e.message) for e in result.errors)

    def test_invalid_forgetting_rate_negative(self):
        """Test that negative forgetting rate is allowed by schema (logic check is outside schema)."""
        # Schema allows number, so -0.1 is valid structurally, even if semantically weird.
        # This test confirms the schema is permissive on the numeric range.
        valid_structurally = {
            "run_id": "bad_run",
            "condition": "sequential",
            "metrics": {
                "initial_accuracy": 0.5,
                "final_accuracy": 0.6,
                "forgetting_rate": -0.1
            },
            "parity_data": {
                "total_evaluations": 0,
                "checksum": ""
            }
        }
        result = validate_result(valid_structurally)
        assert result.valid # Schema validation passes
