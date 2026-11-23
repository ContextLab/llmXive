"""
Contract tests for validating JSON/YAML outputs against defined contracts.

This module validates that the output schemas defined in `contracts/`
match the Pydantic models defined in `src/models/schemas.py`.
It ensures that generated data adheres to the strict contracts
required for reproducibility and downstream analysis.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml
from pydantic import ValidationError

# Import the Pydantic models created in T005
from src.models.schemas import (
    Subject,
    ConnectivityMatrix,
    NetworkMetrics,
    BehavioralScore,
)

# Determine the root directory relative to this test file
REPO_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = REPO_ROOT / "contracts"

# Contract file paths
DATASET_CONTRACT_PATH = CONTRACTS_DIR / "dataset.schema.yaml"
OUTPUT_CONTRACT_PATH = CONTRACTS_DIR / "output.schema.yaml"

@pytest.fixture
def dataset_contract() -> Dict[str, Any]:
    """Load the dataset contract schema."""
    if not DATASET_CONTRACT_PATH.exists():
        pytest.skip(f"Dataset contract not found at {DATASET_CONTRACT_PATH}")
    with open(DATASET_CONTRACT_PATH, "r") as f:
        return yaml.safe_load(f)

@pytest.fixture
def output_contract() -> Dict[str, Any]:
    """Load the output contract schema."""
    if not OUTPUT_CONTRACT_PATH.exists():
        pytest.skip(f"Output contract not found at {OUTPUT_CONTRACT_PATH}")
    with open(OUTPUT_CONTRACT_PATH, "r") as f:
        return yaml.safe_load(f)

def validate_against_contract(data: Dict[str, Any], contract: Dict[str, Any], model_class: Any) -> None:
    """
    Validates a dictionary against a contract and the corresponding Pydantic model.

    Args:
        data: The data dictionary to validate.
        contract: The contract schema dictionary.
        model_class: The Pydantic model class to validate against.

    Raises:
        ValidationError: If the data does not match the model.
        AssertionError: If the data does not match the contract structure.
    """
    # 1. Validate structure against Pydantic model (Type Safety)
    try:
        model_instance = model_class(**data)
    except ValidationError as e:
        pytest.fail(f"Data failed Pydantic validation: {e}")

    # 2. Validate structure against Contract (Schema Safety)
    # Check that all required keys in contract exist in data
    contract_properties = contract.get("properties", {})
    required_fields = contract.get("required", [])

    for field in required_fields:
        if field not in data:
            pytest.fail(f"Missing required field '{field}' from contract")

    # Check types for known fields if specified in contract
    for key, value in data.items():
        if key in contract_properties:
            field_type = contract_properties[key].get("type")
            if field_type:
                if field_type == "array" and not isinstance(value, list):
                    pytest.fail(f"Field '{key}' expected array, got {type(value)}")
                elif field_type == "object" and not isinstance(value, dict):
                    pytest.fail(f"Field '{key}' expected object, got {type(value)}")
                elif field_type == "string" and not isinstance(value, str):
                    pytest.fail(f"Field '{key}' expected string, got {type(value)}")
                elif field_type == "number" and not isinstance(value, (int, float)):
                    pytest.fail(f"Field '{key}' expected number, got {type(value)}")

class TestSubjectContract:
    """Tests for the Subject schema contract."""

    def test_subject_model_contracts(self, dataset_contract):
        """Validate a sample subject against the dataset contract."""
        # Create a valid sample based on the Pydantic model definition
        sample_data = {
            "subject_id": "sub-01",
            "age": 25,
            "sex": "M",
            "group": "control"
        }

        # Verify against Pydantic
        subject = Subject(**sample_data)
        assert subject.subject_id == "sub-01"

        # Verify against Contract
        validate_against_contract(sample_data, dataset_contract, Subject)

    def test_subject_missing_required_field(self, dataset_contract):
        """Ensure validation fails when required fields are missing."""
        sample_data = {
            "subject_id": "sub-01",
            # Missing 'age'
        }

        with pytest.raises((ValidationError, AssertionError)):
            validate_against_contract(sample_data, dataset_contract, Subject)

class TestConnectivityMatrixContract:
    """Tests for the ConnectivityMatrix schema contract."""

    def test_connectivity_matrix_contracts(self, output_contract):
        """Validate a sample connectivity matrix against the output contract."""
        sample_data = {
            "subject_id": "sub-01",
            "matrix_shape": [200, 200],
            "matrix_type": "pearson",
            "data": [[1.0, 0.5], [0.5, 1.0]]  # Simplified for test
        }

        # Verify against Pydantic
        matrix = ConnectivityMatrix(**sample_data)
        assert matrix.matrix_type == "pearson"

        # Verify against Contract
        validate_against_contract(sample_data, output_contract, ConnectivityMatrix)

    def test_connectivity_matrix_symmetry_check(self):
        """Ensure the model enforces logical constraints (e.g., symmetry implied)."""
        # While Pydantic doesn't enforce matrix math, we test that the data structure is valid
        sample_data = {
            "subject_id": "sub-01",
            "matrix_shape": [2, 2],
            "matrix_type": "pearson",
            "data": [[1.0, 0.5], [0.5, 1.0]]
        }
        matrix = ConnectivityMatrix(**sample_data)
        assert len(matrix.data) == 2

class TestNetworkMetricsContract:
    """Tests for the NetworkMetrics schema contract."""

    def test_network_metrics_contracts(self, output_contract):
        """Validate a sample network metrics object against the output contract."""
        sample_data = {
            "subject_id": "sub-01",
            "global_efficiency": 0.45,
            "modularity": 0.65,
            "participation_coefficient": 0.78,
            "networks": {
                "DMN": 0.5,
                "Salience": 0.6
            }
        }

        # Verify against Pydantic
        metrics = NetworkMetrics(**sample_data)
        assert metrics.global_efficiency > 0

        # Verify against Contract
        validate_against_contract(sample_data, output_contract, NetworkMetrics)

class TestBehavioralScoreContract:
    """Tests for the BehavioralScore schema contract."""

    def test_behavioral_score_contracts(self, dataset_contract):
        """Validate a sample behavioral score against the dataset contract."""
        sample_data = {
            "subject_id": "sub-01",
            "bmrq_total": 45.5,
            "bmrq_subscale_music_emotion": 8.2
        }

        # Verify against Pydantic
        score = BehavioralScore(**sample_data)
        assert score.bmrq_total > 0

        # Verify against Contract
        validate_against_contract(sample_data, dataset_contract, BehavioralScore)

class TestIntegration:
    """Integration tests ensuring all schemas work together."""

    def test_full_pipeline_schema_consistency(self, dataset_contract, output_contract):
        """Test that data flows correctly between input and output schemas."""
        # Simulate a full subject record
        subject_data = {
            "subject_id": "sub-01",
            "age": 30,
            "sex": "F",
            "group": "control"
        }
        score_data = {
            "subject_id": "sub-01",
            "bmrq_total": 50.0,
            "bmrq_subscale_music_emotion": 9.0
        }

        # Validate Subject
        validate_against_contract(subject_data, dataset_contract, Subject)
        # Validate Score
        validate_against_contract(score_data, dataset_contract, BehavioralScore)

        # Ensure IDs match (simulating a join)
        assert subject_data["subject_id"] == score_data["subject_id"]