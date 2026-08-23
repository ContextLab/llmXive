"""
Integration tests for schema validators.
Tests that all validators work correctly together and handle edge cases.
"""
import json
import pytest
from pathlib import Path
import sys
import tempfile
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.contract.schemas import (
    DATASET_SCHEMA,
    AGENT_STATE_SCHEMA,
    RESULT_SCHEMA,
    validate_against_schema
)

class TestSchemaValidators:
    """Integration tests for all schema validators."""

    def test_all_schemas_are_valid_json_schema(self):
        """Verify that all schemas are valid JSON Schema structures."""
        for schema_name, schema in [
            ("dataset", DATASET_SCHEMA),
            ("agent_state", AGENT_STATE_SCHEMA),
            ("result", RESULT_SCHEMA)
        ]:
            # Check required top-level keys
            assert "$schema" in schema, f"{schema_name} missing $schema"
            assert "title" in schema, f"{schema_name} missing title"
            assert "type" in schema, f"{schema_name} missing type"
            assert "properties" in schema, f"{schema_name} missing properties"

    def test_dataset_agent_state_result_compatibility(self, tmp_path):
        """Test that data flows correctly from dataset -> agent_state -> result."""
        # 1. Create valid dataset
        dataset = {
            "metadata": {
                "version": "1.0.0",
                "generation_seed": 42,
                "task_type": "logic_proofs",
                "rule_set_id": "logic_rules_v1",
                "generated_at": "2024-01-15T10:30:00Z",
                "total_instances": 10
            },
            "instances": [
                {
                    "instance_id": "proof_001",
                    "type": "logic_proof",
                    "data": {
                        "axioms": ["A", "A -> B"],
                        "goal": "B",
                        "proof_steps": ["Modus Ponens"]
                    }
                }
            ]
        }
        validate_against_schema(dataset, DATASET_SCHEMA, "dataset")

        # 2. Create valid agent state (simulating training on dataset)
        agent_state = {
            "agent_id": "agent_from_dataset_001",
            "condition": "sequential",
            "state_version": 1,
            "generation_step": 5,
            "rule_sets": [
                {
                    "rule_id": "derived_rule_001",
                    "rules": ["A -> B"],
                    "fitness_score": 0.9,
                    "task_domains": ["logic_proofs"]
                }
            ],
            "evaluation_stats": {
                "total_evaluations": 100,
                "evaluations_by_domain": {
                    "logic_proofs": 100
                }
            },
            "performance_history": [
                {
                    "step": 5,
                    "accuracy": 0.9,
                    "domains_tested": ["logic_proofs"]
                }
            ]
        }
        validate_against_schema(agent_state, AGENT_STATE_SCHEMA, "agent_state")

        # 3. Create valid result (simulating evaluation)
        result = {
            "run_id": "run_from_agent_001",
            "condition": "sequential",
            "seed": 42,
            "config_snapshot": {},
            "final_state": agent_state,
            "forgetting_metrics": {
                "initial_accuracy": 0.95,
                "final_accuracy": 0.90,
                "accuracy_drop": 0.05,
                "retention_rates": {
                    "logic_proofs": 0.95
                }
            },
            "evaluation_parity": {
                "expected_total": 100,
                "actual_total": 100,
                "parity_verified": True
            },
            "generated_at": "2024-01-15T14:30:00Z"
        }
        validate_against_schema(result, RESULT_SCHEMA, "result")

    def test_schema_versioning_consistency(self):
        """Test that schemas support versioning correctly."""
        # All schemas should accept version 1.0.0 format
        versioned_dataset = {
            "metadata": {
                "version": "1.0.0",
                "generation_seed": 42,
                "task_type": "logic_proofs",
                "rule_set_id": "test",
                "generated_at": "2024-01-15T10:30:00Z",
                "total_instances": 1
            },
            "instances": []
        }
        validate_against_schema(versioned_dataset, DATASET_SCHEMA, "dataset")

    def test_schema_extensibility(self):
        """Test that schemas allow for future extensibility where appropriate."""
        # Result schema should allow additional config_snapshot fields
        extensible_result = {
            "run_id": "run_001",
            "condition": "sequential",
            "seed": 42,
            "config_snapshot": {
                "new_field_1": "value1",
                "new_field_2": 123
            },
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
                "initial_accuracy": 1.0,
                "final_accuracy": 1.0,
                "accuracy_drop": 0.0,
                "retention_rates": {}
            },
            "evaluation_parity": {
                "expected_total": 0,
                "actual_total": 0,
                "parity_verified": True
            },
            "generated_at": "2024-01-15T14:30:00Z"
        }
        validate_against_schema(extensible_result, RESULT_SCHEMA, "result")

    def test_schema_error_messages_are_helpful(self):
        """Test that validation errors provide useful messages."""
        invalid_dataset = {
            "metadata": {
                "version": "invalid",  # Wrong format
                "generation_seed": -1,  # Negative
                "task_type": "invalid",
                "rule_set_id": "test",
                "generated_at": "2024-01-15T10:30:00Z",
                "total_instances": -5  # Negative
            },
            "instances": []
        }

        with pytest.raises(ValueError) as exc_info:
            validate_against_schema(invalid_dataset, DATASET_SCHEMA, "dataset")

        error_msg = str(exc_info.value)
        assert "version" in error_msg or "generation_seed" in error_msg or "task_type" in error_msg, \
            f"Error message should mention the problematic field: {error_msg}"

    def test_schema_handles_large_structures(self, tmp_path):
        """Test that schemas handle reasonably large structures."""
        # Create a dataset with many instances
        large_dataset = {
            "metadata": {
                "version": "1.0.0",
                "generation_seed": 42,
                "task_type": "mixed",
                "rule_set_id": "test",
                "generated_at": "2024-01-15T10:30:00Z",
                "total_instances": 100
            },
            "instances": [
                {
                    "instance_id": f"instance_{i}",
                    "type": "logic_proof" if i % 2 == 0 else "grid_world",
                    "data": {
                        "axioms": ["A"],
                        "goal": "A",
                        "proof_steps": ["Identity"]
                    } if i % 2 == 0 else {
                        "grid_size": [5, 5],
                        "start": [0, 0],
                        "goal": [4, 4],
                        "obstacles": [],
                        "rules": []
                    }
                }
                for i in range(100)
            ]
        }

        validate_against_schema(large_dataset, DATASET_SCHEMA, "dataset")