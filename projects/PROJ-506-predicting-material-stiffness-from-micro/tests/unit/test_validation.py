"""
Unit tests for the tensor validation logic (T019).
"""
import pytest
import numpy as np
import json
import yaml
from pathlib import Path
import tempfile
import os

# Import the module under test
from code.data_generation.validate_tensors import (
    validate_schema_conformity,
    compute_vrh_bounds,
    validate_vrh_bounds,
    validate_dataset
)


class TestSchemaConformity:
    """Tests for schema validation logic."""

    def test_valid_record(self):
        """Test that a valid record passes schema check."""
        schema = {
            "type": "object",
            "properties": {
                "image_path": {"type": "string"},
                "stiffness_tensor": {"type": "array", "minItems": 6, "maxItems": 6},
                "inclusion_density": {"type": "number"},
                "seed": {"type": "integer"}
            }
        }
        record = {
            "image_path": "data/raw/micro_123.png",
            "stiffness_tensor": [1.0, 1.0, 1.0, 0.5, 0.5, 0.5],
            "inclusion_density": 0.25,
            "seed": 123
        }
        
        is_valid, errors = validate_schema_conformity(record, schema)
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_field(self):
        """Test detection of missing required field."""
        schema = {
            "type": "object",
            "properties": {
                "image_path": {"type": "string"},
                "stiffness_tensor": {"type": "array"},
                "inclusion_density": {"type": "number"},
                "seed": {"type": "integer"}
            }
        }
        record = {
            "image_path": "data/raw/micro_123.png",
            "stiffness_tensor": [1.0, 1.0, 1.0, 0.5, 0.5, 0.5],
            # missing inclusion_density and seed
        }
        
        is_valid, errors = validate_schema_conformity(record, schema)
        assert is_valid is False
        assert len(errors) > 0
        assert any("inclusion_density" in e for e in errors)
        assert any("seed" in e for e in errors)

    def test_wrong_type(self):
        """Test detection of wrong data types."""
        schema = {
            "type": "object",
            "properties": {
                "image_path": {"type": "string"},
                "stiffness_tensor": {"type": "array"},
                "inclusion_density": {"type": "number"},
                "seed": {"type": "integer"}
            }
        }
        record = {
            "image_path": 12345, # Should be string
            "stiffness_tensor": [1.0, 1.0, 1.0, 0.5, 0.5, 0.5],
            "inclusion_density": "0.25", # Should be number
            "seed": 123
        }
        
        is_valid, errors = validate_schema_conformity(record, schema)
        assert is_valid is False
        assert len(errors) > 0

    def test_stiffness_tensor_length(self):
        """Test detection of incorrect stiffness tensor length."""
        schema = {
            "type": "object",
            "properties": {
                "image_path": {"type": "string"},
                "stiffness_tensor": {"type": "array", "minItems": 6, "maxItems": 6},
                "inclusion_density": {"type": "number"},
                "seed": {"type": "integer"}
            }
        }
        record = {
            "image_path": "data/raw/micro_123.png",
            "stiffness_tensor": [1.0, 1.0, 1.0], # Only 3 elements
            "inclusion_density": 0.25,
            "seed": 123
        }
        
        is_valid, errors = validate_schema_conformity(record, schema)
        assert is_valid is False
        assert any("stiffness_tensor" in e for e in errors)


class TestVRHBounds:
    """Tests for Voigt-Reuss-Hill bound calculations."""

    def test_compute_vrh_valid(self):
        """Test VRH calculation on a valid tensor."""
        # A simple isotropic-like tensor
        tensor = [10.0, 10.0, 10.0, 5.0, 5.0, 5.0]
        voigt, reuss = compute_vrh_bounds(tensor)
        
        # Voigt is mean: (10+10+10+5+5+5)/6 = 45/6 = 7.5
        assert np.isclose(voigt, 7.5)
        
        # Reuss is harmonic mean: 6 / (3/10 + 3/5) = 6 / (0.3 + 0.6) = 6/0.9 = 6.666...
        expected_reuss = 6.0 / (3.0/10.0 + 3.0/5.0)
        assert np.isclose(reuss, expected_reuss)

    def test_compute_vrh_zero_component(self):
        """Test VRH calculation with zero component (should handle gracefully)."""
        tensor = [10.0, 0.0, 10.0, 5.0, 5.0, 5.0]
        voigt, reuss = compute_vrh_bounds(tensor)
        
        # Should return 0 for Reuss when division by zero occurs
        assert voigt > 0
        assert reuss == 0.0

    def test_validate_vrh_pass(self):
        """Test that a valid tensor passes VRH validation."""
        tensor = [10.0, 10.0, 10.0, 5.0, 5.0, 5.0]
        is_valid, msg = validate_vrh_bounds(tensor)
        assert is_valid is True
        assert "valid" in msg.lower()

    def test_validate_vrh_fail_negative(self):
        """Test that a tensor with negative components fails."""
        tensor = [10.0, -5.0, 10.0, 5.0, 5.0, 5.0]
        is_valid, msg = validate_vrh_bounds(tensor)
        assert is_valid is False
        assert "non-positive" in msg.lower()

    def test_validate_vrh_fail_wrong_format(self):
        """Test that a tensor with wrong format fails."""
        tensor = [1.0, 2.0, 3.0] # Only 3 elements
        is_valid, msg = validate_vrh_bounds(tensor)
        assert is_valid is False
        assert "format" in msg.lower()


class TestDatasetValidation:
    """Tests for the full dataset validation workflow."""

    def test_validate_dataset_all_valid(self):
        """Test validation of a dataset where all records are valid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata_path = Path(tmpdir) / "metadata.json"
            schema_path = Path(tmpdir) / "schema.yaml"
            
            # Create valid records
            records = [
                {
                    "image_path": f"data/raw/micro_{i}.png",
                    "stiffness_tensor": [10.0, 10.0, 10.0, 5.0, 5.0, 5.0],
                    "inclusion_density": 0.2 + (i * 0.01),
                    "seed": i
                }
                for i in range(5)
            ]
            
            with open(metadata_path, 'w') as f:
                json.dump(records, f)
            
            schema = {
                "type": "object",
                "properties": {
                    "image_path": {"type": "string"},
                    "stiffness_tensor": {"type": "array"},
                    "inclusion_density": {"type": "number"},
                    "seed": {"type": "integer"}
                }
            }
            with open(schema_path, 'w') as f:
                yaml.dump(schema, f)
            
            results = validate_dataset(metadata_path, schema_path)
            
            assert results['total_records'] == 5
            assert results['valid_count'] == 5
            assert results['invalid_count'] == 0
            assert results['success_rate'] == 1.0

    def test_validate_dataset_mixed(self):
        """Test validation of a dataset with some invalid records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata_path = Path(tmpdir) / "metadata.json"
            schema_path = Path(tmpdir) / "schema.yaml"
            
            # Create mixed records
            records = [
                {
                    "image_path": "data/raw/micro_0.png",
                    "stiffness_tensor": [10.0, 10.0, 10.0, 5.0, 5.0, 5.0],
                    "inclusion_density": 0.2,
                    "seed": 0
                },
                {
                    "image_path": "data/raw/micro_1.png",
                    "stiffness_tensor": [-5.0, 10.0, 10.0, 5.0, 5.0, 5.0], # Invalid: negative
                    "inclusion_density": 0.3,
                    "seed": 1
                },
                {
                    "image_path": "data/raw/micro_2.png",
                    "stiffness_tensor": [10.0, 10.0, 10.0, 5.0, 5.0, 5.0],
                    "inclusion_density": 1.5, # Invalid: > 1.0
                    "seed": 2
                }
            ]
            
            with open(metadata_path, 'w') as f:
                json.dump(records, f)
            
            schema = {
                "type": "object",
                "properties": {
                    "image_path": {"type": "string"},
                    "stiffness_tensor": {"type": "array"},
                    "inclusion_density": {"type": "number"},
                    "seed": {"type": "integer"}
                }
            }
            with open(schema_path, 'w') as f:
                yaml.dump(schema, f)
            
            results = validate_dataset(metadata_path, schema_path)
            
            assert results['total_records'] == 3
            assert results['valid_count'] == 1
            assert results['invalid_count'] == 2
            assert results['success_rate'] == 1.0/3.0
            assert 1 in results['invalid_indices']
            assert 2 in results['invalid_indices']

    def test_validate_dataset_missing_file(self):
        """Test that validation raises error for missing metadata."""
        with pytest.raises(FileNotFoundError):
            validate_dataset(Path("/nonexistent/path.json"))