"""
Contract tests for dataset schema validation.
Validates that generated datasets conform to the expected JSON structure.
"""
import json
import pytest
from pathlib import Path
import sys
import os
import tempfile
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.contract.schemas import (
    DATASET_SCHEMA,
    validate_against_schema
)

class TestDatasetSchema:
    """Tests for dataset schema validation."""

    def test_valid_logic_proofs_dataset(self, tmp_path):
        """Test that a valid logic proofs dataset passes validation."""
        valid_dataset = {
            "metadata": {
                "version": "1.0.0",
                "generation_seed": 42,
                "task_type": "logic_proofs",
                "rule_set_id": "logic_rules_v1",
                "generated_at": "2024-01-15T10:30:00Z",
                "total_instances": 100
            },
            "instances": [
                {
                    "instance_id": "proof_001",
                    "type": "logic_proof",
                    "data": {
                        "axioms": ["A", "A -> B"],
                        "goal": "B",
                        "proof_steps": ["Modus Ponens on A and A -> B yields B"]
                    }
                },
                {
                    "instance_id": "proof_002",
                    "type": "logic_proof",
                    "data": {
                        "axioms": ["P", "P -> Q", "Q -> R"],
                        "goal": "R",
                        "proof_steps": [
                            "Modus Ponens on P and P -> Q yields Q",
                            "Modus Ponens on Q and Q -> R yields R"
                        ]
                    }
                }
            ]
        }

        validate_against_schema(valid_dataset, DATASET_SCHEMA, "dataset")

    def test_valid_grid_worlds_dataset(self, tmp_path):
        """Test that a valid grid worlds dataset passes validation."""
        valid_dataset = {
            "metadata": {
                "version": "1.0.0",
                "generation_seed": 123,
                "task_type": "grid_worlds",
                "rule_set_id": "grid_rules_v1",
                "generated_at": "2024-01-15T11:00:00Z",
                "total_instances": 50
            },
            "instances": [
                {
                    "instance_id": "grid_001",
                    "type": "grid_world",
                    "data": {
                        "grid_size": [10, 10],
                        "start": [0, 0],
                        "goal": [9, 9],
                        "obstacles": [[2, 2], [3, 3], [5, 5]],
                        "rules": ["avoid_red", "diagonal_paths"]
                    }
                }
            ]
        }

        validate_against_schema(valid_dataset, DATASET_SCHEMA, "dataset")

    def test_valid_mixed_dataset(self, tmp_path):
        """Test that a valid mixed dataset passes validation."""
        valid_dataset = {
            "metadata": {
                "version": "1.0.0",
                "generation_seed": 456,
                "task_type": "mixed",
                "rule_set_id": "mixed_rules_v1",
                "generated_at": "2024-01-15T12:00:00Z",
                "total_instances": 150
            },
            "instances": [
                {
                    "instance_id": "proof_001",
                    "type": "logic_proof",
                    "data": {
                        "axioms": ["X", "X -> Y"],
                        "goal": "Y",
                        "proof_steps": ["Modus Ponens"]
                    }
                },
                {
                    "instance_id": "grid_001",
                    "type": "grid_world",
                    "data": {
                        "grid_size": [5, 5],
                        "start": [0, 0],
                        "goal": [4, 4],
                        "obstacles": [[1, 1]],
                        "rules": ["avoid_red"]
                    }
                }
            ]
        }

        validate_against_schema(valid_dataset, DATASET_SCHEMA, "dataset")

    def test_missing_metadata_fails(self, tmp_path):
        """Test that dataset missing metadata fails validation."""
        invalid_dataset = {
            "instances": []
        }

        with pytest.raises(ValueError, match="Missing required property 'metadata'"):
            validate_against_schema(invalid_dataset, DATASET_SCHEMA, "dataset")

    def test_missing_instances_fails(self, tmp_path):
        """Test that dataset missing instances fails validation."""
        invalid_dataset = {
            "metadata": {
                "version": "1.0.0",
                "generation_seed": 42,
                "task_type": "logic_proofs",
                "rule_set_id": "logic_rules_v1",
                "generated_at": "2024-01-15T10:30:00Z",
                "total_instances": 100
            }
        }

        with pytest.raises(ValueError, match="Missing required property 'instances'"):
            validate_against_schema(invalid_dataset, DATASET_SCHEMA, "dataset")

    def test_invalid_task_type_fails(self, tmp_path):
        """Test that invalid task_type fails validation."""
        invalid_dataset = {
            "metadata": {
                "version": "1.0.0",
                "generation_seed": 42,
                "task_type": "invalid_type",
                "rule_set_id": "logic_rules_v1",
                "generated_at": "2024-01-15T10:30:00Z",
                "total_instances": 100
            },
            "instances": []
        }

        with pytest.raises(ValueError, match="String 'invalid_type' not in allowed values"):
            validate_against_schema(invalid_dataset, DATASET_SCHEMA, "dataset")

    def test_version_pattern_validation(self, tmp_path):
        """Test that version must match semver pattern."""
        invalid_dataset = {
            "metadata": {
                "version": "invalid-version",
                "generation_seed": 42,
                "task_type": "logic_proofs",
                "rule_set_id": "logic_rules_v1",
                "generated_at": "2024-01-15T10:30:00Z",
                "total_instances": 100
            },
            "instances": []
        }

        with pytest.raises(ValueError, match="does not match pattern"):
            validate_against_schema(invalid_dataset, DATASET_SCHEMA, "dataset")

    def test_instance_structure_validation(self, tmp_path):
        """Test that instances must have required structure."""
        invalid_dataset = {
            "metadata": {
                "version": "1.0.0",
                "generation_seed": 42,
                "task_type": "logic_proofs",
                "rule_set_id": "logic_rules_v1",
                "generated_at": "2024-01-15T10:30:00Z",
                "total_instances": 100
            },
            "instances": [
                {
                    "instance_id": "proof_001",
                    # Missing 'type' and 'data'
                    "extra_field": "value"
                }
            ]
        }

        with pytest.raises(ValueError):
            validate_against_schema(invalid_dataset, DATASET_SCHEMA, "dataset")

    def test_load_and_validate_from_file(self, tmp_path):
        """Test loading a dataset file and validating it."""
        valid_dataset = {
            "metadata": {
                "version": "1.0.0",
                "generation_seed": 42,
                "task_type": "logic_proofs",
                "rule_set_id": "logic_rules_v1",
                "generated_at": "2024-01-15T10:30:00Z",
                "total_instances": 1
            },
            "instances": [
                {
                    "instance_id": "proof_001",
                    "type": "logic_proof",
                    "data": {
                        "axioms": ["A"],
                        "goal": "A",
                        "proof_steps": ["Identity"]
                    }
                }
            ]
        }

        # Write to file
        file_path = tmp_path / "dataset.json"
        with open(file_path, 'w') as f:
            json.dump(valid_dataset, f)

        # Load and validate
        with open(file_path, 'r') as f:
            loaded_data = json.load(f)

        validate_against_schema(loaded_data, DATASET_SCHEMA, "dataset")

    def test_empty_instances_array_valid(self, tmp_path):
        """Test that empty instances array is valid (edge case)."""
        valid_dataset = {
            "metadata": {
                "version": "1.0.0",
                "generation_seed": 42,
                "task_type": "logic_proofs",
                "rule_set_id": "logic_rules_v1",
                "generated_at": "2024-01-15T10:30:00Z",
                "total_instances": 0
            },
            "instances": []
        }

        validate_against_schema(valid_dataset, DATASET_SCHEMA, "dataset")
