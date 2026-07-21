"""
Contract tests for dataset configuration validation.

These tests verify that the dataset_config_validator correctly validates
configurations against the schema and handles edge cases appropriately.
"""
import json
import os
import tempfile
from pathlib import Path

import pytest
from jsonschema import ValidationError

# Import the validator module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from dataset_config_validator import (
    load_schema,
    validate_config,
    create_sample_config,
)


class TestLoadSchema:
    """Tests for the load_schema function."""

    def test_load_default_schema(self):
        """Test loading the schema from the default path."""
        schema = load_schema()
        assert "properties" in schema
        assert "version" in schema["properties"]
        assert "datasets" in schema["properties"]

    def test_load_custom_schema(self):
        """Test loading the schema from a custom path."""
        # Create a temporary schema file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
            $schema: http://json-schema.org/draft-07/schema#
            type: object
            properties:
              test:
                type: string
            """)
            temp_path = f.name

        try:
            schema = load_schema(temp_path)
            assert "properties" in schema
            assert "test" in schema["properties"]
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_schema(self):
        """Test that loading a nonexistent schema raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_schema("/nonexistent/path/schema.yaml")


class TestValidateConfig:
    """Tests for the validate_config function."""

    def test_validate_valid_config(self):
        """Test validation of a valid configuration."""
        # Create a temporary valid config
        valid_config = {
            "version": "1.0.0",
            "description": "Test configuration",
            "datasets": [
                {
                    "id": "PRJNA123456",
                    "source": "ncbi_sra",
                    "description": "Test dataset",
                    "metadata": {
                        "wetland_type": "constructed",
                        "nutrient_removal": True,
                        "target_nutrients": ["nitrogen"],
                        "sampling_stages": ["early"],
                        "location": "Test Location",
                        "study_period": "12_months"
                    }
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_config, f)
            temp_path = f.name

        try:
            is_valid, error = validate_config(temp_path)
            assert is_valid is True
            assert error is None
        finally:
            os.unlink(temp_path)

    def test_validate_invalid_version_format(self):
        """Test validation fails for invalid version format."""
        invalid_config = {
            "version": "invalid",
            "description": "Test",
            "datasets": []
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_config, f)
            temp_path = f.name

        try:
            is_valid, error = validate_config(temp_path)
            assert is_valid is False
            assert "Validation error" in error
        finally:
            os.unlink(temp_path)

    def test_validate_missing_required_field(self):
        """Test validation fails when required field is missing."""
        invalid_config = {
            "version": "1.0.0",
            "description": "Test"
            # Missing "datasets"
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_config, f)
            temp_path = f.name

        try:
            is_valid, error = validate_config(temp_path)
            assert is_valid is False
            assert "Validation error" in error
        finally:
            os.unlink(temp_path)

    def test_validate_invalid_source(self):
        """Test validation fails for invalid source value."""
        invalid_config = {
            "version": "1.0.0",
            "description": "Test",
            "datasets": [
                {
                    "id": "PRJNA123",
                    "source": "invalid_source",
                    "description": "Test",
                    "metadata": {
                        "wetland_type": "constructed",
                        "nutrient_removal": True,
                        "target_nutrients": ["nitrogen"],
                        "sampling_stages": ["early"],
                        "location": "Test",
                        "study_period": "12_months"
                    }
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_config, f)
            temp_path = f.name

        try:
            is_valid, error = validate_config(temp_path)
            assert is_valid is False
            assert "Validation error" in error
        finally:
            os.unlink(temp_path)

    def test_validate_nonexistent_config(self):
        """Test validation of a nonexistent config file."""
        is_valid, error = validate_config("/nonexistent/config.json")
        assert is_valid is False
        assert "not found" in error

    def test_validate_invalid_json(self):
        """Test validation of a file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name

        try:
            is_valid, error = validate_config(temp_path)
            assert is_valid is False
            assert "Invalid JSON" in error
        finally:
            os.unlink(temp_path)


class TestCreateSampleConfig:
    """Tests for the create_sample_config function."""

    def test_create_sample_config_creates_file(self):
        """Test that create_sample_config creates a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "sample_config.json")
            create_sample_config(output_path)

            assert os.path.exists(output_path)

    def test_create_sample_config_valid_schema(self):
        """Test that created sample config is valid against schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "sample_config.json")
            create_sample_config(output_path)

            is_valid, error = validate_config(output_path)
            assert is_valid is True
            assert error is None

    def test_create_sample_config_structure(self):
        """Test that created sample config has expected structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "sample_config.json")
            create_sample_config(output_path)

            with open(output_path, 'r') as f:
                config = json.load(f)

            assert "version" in config
            assert "description" in config
            assert "datasets" in config
            assert len(config["datasets"]) > 0
            assert config["datasets"][0]["id"] is not None
            assert config["datasets"][0]["source"] in ["ncbi_sra", "zenodo"]