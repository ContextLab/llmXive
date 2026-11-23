"""
Unit tests for the dataset metadata schema.
"""
import pytest
import json
from src.datasets.metadata_schema import (
    DatasetMetadata,
    InterventionType,
    ScanType,
    validate_schema,
    create_sample_metadata,
    validate_sample_json,
    validate_schema
)


class TestDatasetMetadata:
    """Tests for the DatasetMetadata dataclass."""

    def test_create_valid_metadata(self):
        """Test creating a valid DatasetMetadata instance."""
        metadata = DatasetMetadata(
            pre_scan_count=10,
            post_scan_count=10,
            intervention_type="MBSR",
            scan_type="resting_state"
        )
        assert metadata.pre_scan_count == 10
        assert metadata.post_scan_count == 10
        assert metadata.intervention_type == "MBSR"
        assert metadata.scan_type == "resting_state"

    def test_create_with_optional_fields(self):
        """Test creating metadata with optional fields."""
        metadata = DatasetMetadata(
            pre_scan_count=5,
            post_scan_count=5,
            intervention_type="MBSR",
            scan_type="resting_state",
            dataset_id="ds000001",
            dataset_name="Test Study"
        )
        assert metadata.dataset_id == "ds000001"
        assert metadata.dataset_name == "Test Study"

    def test_invalid_intervention_type(self):
        """Test that invalid intervention_type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            DatasetMetadata(
                pre_scan_count=10,
                post_scan_count=10,
                intervention_type="INVALID",
                scan_type="resting_state"
            )
        assert "Invalid intervention_type" in str(exc_info.value)

    def test_invalid_scan_type(self):
        """Test that invalid scan_type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            DatasetMetadata(
                pre_scan_count=10,
                post_scan_count=10,
                intervention_type="MBSR",
                scan_type="invalid_scan"
            )
        assert "Invalid scan_type" in str(exc_info.value)

    def test_negative_pre_scan_count(self):
        """Test that negative pre_scan_count raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            DatasetMetadata(
                pre_scan_count=-1,
                post_scan_count=10,
                intervention_type="MBSR",
                scan_type="resting_state"
            )
        assert "pre_scan_count must be >= 0" in str(exc_info.value)

    def test_negative_post_scan_count(self):
        """Test that negative post_scan_count raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            DatasetMetadata(
                pre_scan_count=10,
                post_scan_count=-1,
                intervention_type="MBSR",
                scan_type="resting_state"
            )
        assert "post_scan_count must be >= 0" in str(exc_info.value)

    def test_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = DatasetMetadata(
            pre_scan_count=10,
            post_scan_count=10,
            intervention_type="MBSR",
            scan_type="resting_state",
            dataset_id="ds000001"
        )
        d = metadata.to_dict()
        assert d["pre_scan_count"] == 10
        assert d["post_scan_count"] == 10
        assert d["intervention_type"] == "MBSR"
        assert d["scan_type"] == "resting_state"
        assert d["dataset_id"] == "ds000001"

    def test_to_json(self):
        """Test converting metadata to JSON string."""
        metadata = DatasetMetadata(
            pre_scan_count=10,
            post_scan_count=10,
            intervention_type="MBSR",
            scan_type="resting_state"
        )
        json_str = metadata.to_json()
        parsed = json.loads(json_str)
        assert parsed["pre_scan_count"] == 10
        assert parsed["intervention_type"] == "MBSR"

    def test_from_dict(self):
        """Test creating metadata from dictionary."""
        data = {
            "pre_scan_count": 10,
            "post_scan_count": 10,
            "intervention_type": "MBSR",
            "scan_type": "resting_state",
            "dataset_id": "ds000001"
        }
        metadata = DatasetMetadata.from_dict(data)
        assert metadata.pre_scan_count == 10
        assert metadata.dataset_id == "ds000001"

    def test_from_json(self):
        """Test creating metadata from JSON string."""
        json_str = json.dumps({
            "pre_scan_count": 10,
            "post_scan_count": 10,
            "intervention_type": "MBSR",
            "scan_type": "resting_state"
        })
        metadata = DatasetMetadata.from_json(json_str)
        assert metadata.pre_scan_count == 10
        assert metadata.intervention_type == "MBSR"


class TestValidateSchema:
    """Tests for the validate_schema function."""

    def test_valid_schema(self):
        """Test validation of valid data."""
        data = {
            "pre_scan_count": 10,
            "post_scan_count": 10,
            "intervention_type": "MBSR",
            "scan_type": "resting_state"
        }
        is_valid, errors = validate_schema(data)
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_required_field(self):
        """Test validation fails on missing required field."""
        data = {
            "pre_scan_count": 10,
            "post_scan_count": 10,
            "intervention_type": "MBSR"
            # scan_type missing
        }
        is_valid, errors = validate_schema(data)
        assert is_valid is False
        assert any("scan_type" in e for e in errors)

    def test_invalid_intervention_type(self):
        """Test validation fails on invalid intervention_type."""
        data = {
            "pre_scan_count": 10,
            "post_scan_count": 10,
            "intervention_type": "INVALID",
            "scan_type": "resting_state"
        }
        is_valid, errors = validate_schema(data)
        assert is_valid is False
        assert any("intervention_type" in e for e in errors)

    def test_invalid_scan_type(self):
        """Test validation fails on invalid scan_type."""
        data = {
            "pre_scan_count": 10,
            "post_scan_count": 10,
            "intervention_type": "MBSR",
            "scan_type": "invalid"
        }
        is_valid, errors = validate_schema(data)
        assert is_valid is False
        assert any("scan_type" in e for e in errors)

    def test_negative_pre_scan_count(self):
        """Test validation fails on negative pre_scan_count."""
        data = {
            "pre_scan_count": -1,
            "post_scan_count": 10,
            "intervention_type": "MBSR",
            "scan_type": "resting_state"
        }
        is_valid, errors = validate_schema(data)
        assert is_valid is False
        assert any("pre_scan_count" in e for e in errors)

    def test_non_integer_pre_scan_count(self):
        """Test validation fails on non-integer pre_scan_count."""
        data = {
            "pre_scan_count": "10",
            "post_scan_count": 10,
            "intervention_type": "MBSR",
            "scan_type": "resting_state"
        }
        is_valid, errors = validate_schema(data)
        assert is_valid is False
        assert any("pre_scan_count must be an integer" in e for e in errors)


class TestCreateSampleMetadata:
    """Tests for the create_sample_metadata function."""

    def test_sample_metadata_structure(self):
        """Test that sample metadata has all required fields."""
        sample = create_sample_metadata()
        required_fields = ["pre_scan_count", "post_scan_count", "intervention_type", "scan_type"]
        for field in required_fields:
            assert field in sample

    def test_sample_metadata_values(self):
        """Test that sample metadata has valid values."""
        sample = create_sample_metadata()
        assert sample["pre_scan_count"] >= 0
        assert sample["post_scan_count"] >= 0
        assert sample["intervention_type"] in [e.value for e in InterventionType]
        assert sample["scan_type"] in [e.value for e in ScanType]


class TestValidateSampleJson:
    """Tests for the validate_sample_json function."""

    def test_valid_json(self):
        """Test validation of valid JSON string."""
        sample = create_sample_metadata()
        json_str = json.dumps(sample)
        is_valid, errors = validate_sample_json(json_str)
        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_json(self):
        """Test validation of invalid JSON string."""
        is_valid, errors = validate_sample_json("{invalid json}")
        assert is_valid is False
        assert any("Invalid JSON" in e for e in errors)

    def test_json_missing_required_field(self):
        """Test validation of JSON missing required field."""
        data = {
            "pre_scan_count": 10,
            "post_scan_count": 10,
            "intervention_type": "MBSR"
        }
        json_str = json.dumps(data)
        is_valid, errors = validate_sample_json(json_str)
        assert is_valid is False
        assert any("scan_type" in e for e in errors)