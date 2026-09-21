import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict
import pytest

from src.validators import load_schema, validate_data, SchemaValidationError

def get_contract_path(contract_name: str) -> Path:
    """Get the path to a contract schema file."""
    contracts_dir = Path(__file__).parent.parent.parent / "contracts"
    return contracts_dir / f"{contract_name}.schema.yaml"

def load_contract_schema(contract_name: str) -> Dict[str, Any]:
    """Load a contract schema from the contracts directory."""
    path = get_contract_path(contract_name)
    if not path.exists():
        raise FileNotFoundError(f"Contract schema not found: {path}")
    return load_schema(path)

class TestDatasetSchema:
    """Test suite for the Dataset contract schema."""

    @pytest.fixture
    def valid_dataset_data(self) -> Dict[str, Any]:
        return {
            "dataset_id": "test_001",
            "source": "synthetic",
            "distribution_type": "Normal",
            "sample_size": 1000,
            "contamination_rate": 0.05,
            "columns": ["feature_1", "feature_2"],
            "created_at": "2023-01-01T00:00:00Z"
        }

    @pytest.fixture
    def invalid_dataset_data(self) -> Dict[str, Any]:
        return {
            "dataset_id": 123,  # Should be string
            "source": "synthetic",
            "distribution_type": "Normal",
            "sample_size": "large",  # Should be int
            "contamination_rate": 0.05,
            "columns": ["feature_1"],
            "created_at": "2023-01-01T00:00:00Z"
        }

    def test_load_schema_exists(self):
        """Test that the Dataset schema file exists and loads."""
        schema = load_contract_schema("dataset")
        assert schema is not None
        assert "type" in schema
        assert schema["type"] == "object"

    def test_validate_valid_data(self, valid_dataset_data):
        """Test that valid dataset data passes validation."""
        schema = load_contract_schema("dataset")
        try:
            validate_data(valid_dataset_data, schema)
            # If we get here without exception, validation passed
            assert True
        except SchemaValidationError as e:
            pytest.fail(f"Valid data failed validation: {e}")

    def test_validate_invalid_data(self, invalid_dataset_data):
        """Test that invalid dataset data fails validation."""
        schema = load_contract_schema("dataset")
        with pytest.raises(SchemaValidationError):
            validate_data(invalid_dataset_data, schema)

    def test_dataset_schema_integration(self, valid_dataset_data):
        """Integration test for Dataset schema validation."""
        schema = load_contract_schema("dataset")
        # Verify required fields are enforced
        required_fields = schema.get("required", [])
        assert "dataset_id" in required_fields
        assert "source" in required_fields
        assert "distribution_type" in required_fields

class TestContaminationProfileSchema:
    """Test suite for the ContaminationProfile contract schema."""

    @pytest.fixture
    def valid_profile_data(self) -> Dict[str, Any]:
        return {
            "profile_id": "profile_001",
            "dataset_id": "test_001",
            "contamination_method": "cauchy",
            "contamination_rate": 0.1,
            "scale_factor": 5.0,
            "injected_indices": [10, 25, 100],
            "created_at": "2023-01-01T00:00:00Z"
        }

    @pytest.fixture
    def invalid_profile_data(self) -> Dict[str, Any]:
        return {
            "profile_id": "profile_001",
            "dataset_id": "test_001",
            "contamination_method": "cauchy",
            "contamination_rate": "high",  # Should be float
            "scale_factor": 5.0,
            "injected_indices": ["a", "b"],  # Should be list of ints
            "created_at": "2023-01-01T00:00:00Z"
        }

    def test_load_schema_exists(self):
        """Test that the ContaminationProfile schema file exists and loads."""
        schema = load_contract_schema("contamination_profile")
        assert schema is not None
        assert "type" in schema
        assert schema["type"] == "object"

    def test_validate_valid_data(self, valid_profile_data):
        """Test that valid contamination profile data passes validation."""
        schema = load_contract_schema("contamination_profile")
        try:
            validate_data(valid_profile_data, schema)
            assert True
        except SchemaValidationError as e:
            pytest.fail(f"Valid data failed validation: {e}")

    def test_validate_invalid_data(self, invalid_profile_data):
        """Test that invalid contamination profile data fails validation."""
        schema = load_contract_schema("contamination_profile")
        with pytest.raises(SchemaValidationError):
            validate_data(invalid_profile_data, schema)

    def test_contamination_profile_schema_integration(self, valid_profile_data):
        """Integration test for ContaminationProfile schema validation."""
        schema = load_contract_schema("contamination_profile")
        required_fields = schema.get("required", [])
        assert "profile_id" in required_fields
        assert "dataset_id" in required_fields
        assert "contamination_method" in required_fields

class TestRemovalMethodSchema:
    """Test suite for the RemovalMethod contract schema."""

    @pytest.fixture
    def valid_removal_data(self) -> Dict[str, Any]:
        return {
            "method_id": "iqr_001",
            "method_name": "IQR",
            "dataset_id": "test_001",
            "parameters": {
                "k": 1.5
            },
            "rows_removed": 50,
            "rows_remaining": 950,
            "created_at": "2023-01-01T00:00:00Z"
        }

    @pytest.fixture
    def invalid_removal_data(self) -> Dict[str, Any]:
        return {
            "method_id": "iqr_001",
            "method_name": "IQR",
            "dataset_id": "test_001",
            "parameters": {
                "k": "too_high"  # Should be float
            },
            "rows_removed": -5,  # Should be non-negative
            "rows_remaining": 950,
            "created_at": "2023-01-01T00:00:00Z"
        }

    def test_load_schema_exists(self):
        """Test that the RemovalMethod schema file exists and loads."""
        schema = load_contract_schema("removal_method")
        assert schema is not None
        assert "type" in schema
        assert schema["type"] == "object"

    def test_validate_valid_data(self, valid_removal_data):
        """Test that valid removal method data passes validation."""
        schema = load_contract_schema("removal_method")
        try:
            validate_data(valid_removal_data, schema)
            assert True
        except SchemaValidationError as e:
            pytest.fail(f"Valid data failed validation: {e}")

    def test_validate_invalid_data(self, invalid_removal_data):
        """Test that invalid removal method data fails validation."""
        schema = load_contract_schema("removal_method")
        with pytest.raises(SchemaValidationError):
            validate_data(invalid_removal_data, schema)

    def test_removal_method_schema_integration(self, valid_removal_data):
        """Integration test for RemovalMethod schema validation."""
        schema = load_contract_schema("removal_method")
        required_fields = schema.get("required", [])
        assert "method_id" in required_fields
        assert "method_name" in required_fields
        assert "dataset_id" in required_fields
        assert "parameters" in required_fields

class TestEstimationResultSchema:
    """Test suite for the EstimationResult contract schema."""

    @pytest.fixture
    def valid_result_data(self) -> Dict[str, Any]:
        return {
            "result_id": "res_001",
            "method_id": "iqr_001",
            "dataset_id": "test_001",
            "estimated_variance": 1.25,
            "ground_truth_variance": 1.0,
            "bias": 0.25,
            "mse": 0.0625,
            "computation_time_ms": 150.5,
            "created_at": "2023-01-01T00:00:00Z"
        }

    @pytest.fixture
    def invalid_result_data(self) -> Dict[str, Any]:
        return {
            "result_id": "res_001",
            "method_id": "iqr_001",
            "dataset_id": "test_001",
            "estimated_variance": "NaN",  # Should be float
            "ground_truth_variance": 1.0,
            "bias": 0.25,
            "mse": 0.0625,
            "computation_time_ms": -10,  # Should be non-negative
            "created_at": "2023-01-01T00:00:00Z"
        }

    def test_load_schema_exists(self):
        """Test that the EstimationResult schema file exists and loads."""
        schema = load_contract_schema("estimation_result")
        assert schema is not None
        assert "type" in schema
        assert schema["type"] == "object"

    def test_validate_valid_data(self, valid_result_data):
        """Test that valid estimation result data passes validation."""
        schema = load_contract_schema("estimation_result")
        try:
            validate_data(valid_result_data, schema)
            assert True
        except SchemaValidationError as e:
            pytest.fail(f"Valid data failed validation: {e}")

    def test_validate_invalid_data(self, invalid_result_data):
        """Test that invalid estimation result data fails validation."""
        schema = load_contract_schema("estimation_result")
        with pytest.raises(SchemaValidationError):
            validate_data(invalid_result_data, schema)

    def test_estimation_result_schema_integration(self, valid_result_data):
        """Integration test for EstimationResult schema validation."""
        schema = load_contract_schema("estimation_result")
        required_fields = schema.get("required", [])
        assert "result_id" in required_fields
        assert "method_id" in required_fields
        assert "dataset_id" in required_fields
        assert "estimated_variance" in required_fields
        assert "ground_truth_variance" in required_fields

def test_dataset_schema_integration():
    """Placeholder for integration test function."""
    pass

def test_contamination_profile_schema_integration():
    """Placeholder for integration test function."""
    pass