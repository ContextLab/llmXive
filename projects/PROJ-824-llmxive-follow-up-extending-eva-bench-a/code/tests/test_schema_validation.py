"""
Tests for schema validation functionality.
"""
import json
import tempfile
import yaml
from pathlib import Path
import pytest

from contracts.schema_validator import (
    validate_dataset,
    validate_injection_config,
    get_dataset_schema,
    get_injection_schema,
)


class TestDatasetSchemaValidation:
    """Tests for dataset schema validation."""

    def test_valid_dataset_structure(self):
        """Test that a valid dataset structure passes validation."""
        valid_data = {
            "metadata": {
                "version": "1.0.0",
                "source": "HuggingFace/eva-bench-v1",
                "created_at": "2024-01-15T10:30:00Z",
                "checksum": "abc123def456",
                "license": "MIT",
                "total_scenarios": 213,
            },
            "scenarios": [
                {
                    "id": "scenario_001",
                    "name": "Customer Support",
                    "audio_file": "audio_001.wav",
                    "audio_duration_sec": 45.5,
                    "expected_turns": 5,
                    "metrics": ["Conversation Progression", "Turn-Taking"],
                    "tags": ["support", "basic"],
                }
            ],
        }
        is_valid, msg = validate_dataset(valid_data)
        assert is_valid, f"Expected valid dataset, got error: {msg}"

    def test_missing_required_field(self):
        """Test that missing required fields fail validation."""
        invalid_data = {
            "metadata": {
                "version": "1.0.0",
                # Missing 'source', 'created_at', 'checksum'
            },
            "scenarios": [],
        }
        is_valid, msg = validate_dataset(invalid_data)
        assert not is_valid
        assert "Validation Error" in msg

    def test_invalid_scenario_id_format(self):
        """Test that invalid scenario ID format fails validation."""
        invalid_data = {
            "metadata": {
                "version": "1.0.0",
                "source": "test",
                "created_at": "2024-01-01T00:00:00Z",
                "checksum": "test123",
            },
            "scenarios": [
                {
                    "id": "invalid id with spaces!",  # Invalid pattern
                    "name": "Test",
                    "audio_file": "test.wav",
                    "expected_turns": 1,
                    "metrics": ["Conversation Progression"],
                }
            ],
        }
        is_valid, msg = validate_dataset(invalid_data)
        assert not is_valid
        assert "pattern" in msg.lower() or "Validation Error" in msg

    def test_validate_from_json_file(self):
        """Test validation from a JSON file path."""
        data = {
            "metadata": {
                "version": "1.0.0",
                "source": "test",
                "created_at": "2024-01-01T00:00:00Z",
                "checksum": "test123",
            },
            "scenarios": [],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            is_valid, msg = validate_dataset(temp_path)
            assert is_valid, f"Expected valid, got: {msg}"
        finally:
            Path(temp_path).unlink()

    def test_validate_from_yaml_file(self):
        """Test validation from a YAML file path."""
        data = {
            "metadata": {
                "version": "1.0.0",
                "source": "test",
                "created_at": "2024-01-01T00:00:00Z",
                "checksum": "test123",
            },
            "scenarios": [],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(data, f)
            temp_path = f.name

        try:
            is_valid, msg = validate_dataset(temp_path)
            assert is_valid, f"Expected valid, got: {msg}"
        finally:
            Path(temp_path).unlink()

    def test_file_not_found(self):
        """Test validation with non-existent file."""
        is_valid, msg = validate_dataset("/nonexistent/path/file.json")
        assert not is_valid
        assert "not found" in msg.lower()


class TestInjectionSchemaValidation:
    """Tests for injection configuration schema validation."""

    def test_valid_injection_config(self):
        """Test that a valid injection config passes validation."""
        valid_data = {
            "injection_config": {
                "latency_steps": [200, 500, 1000, 2000],
                "tolerance_ms": 10,
                "seed": 42,
                "output_dir": "data/injected",
                "audio_format": "wav",
            }
        }
        is_valid, msg = validate_injection_config(valid_data)
        assert is_valid, f"Expected valid config, got error: {msg}"

    def test_missing_required_field(self):
        """Test that missing required fields fail validation."""
        invalid_data = {
            "injection_config": {
                "latency_steps": [200],
                # Missing 'tolerance_ms' and 'seed'
            }
        }
        is_valid, msg = validate_injection_config(invalid_data)
        assert not is_valid
        assert "Validation Error" in msg

    def test_invalid_latency_steps_type(self):
        """Test that non-integer latency steps fail validation."""
        invalid_data = {
            "injection_config": {
                "latency_steps": ["200", 500],  # String instead of int
                "tolerance_ms": 10,
                "seed": 42,
            }
        }
        is_valid, msg = validate_injection_config(invalid_data)
        assert not is_valid
        assert "Validation Error" in msg

    def test_negative_latency_step(self):
        """Test that negative latency steps fail validation."""
        invalid_data = {
            "injection_config": {
                "latency_steps": [-100, 200],
                "tolerance_ms": 10,
                "seed": 42,
            }
        }
        is_valid, msg = validate_injection_config(invalid_data)
        assert not is_valid
        assert "minimum" in msg.lower() or "Validation Error" in msg

    def test_invalid_audio_format(self):
        """Test that invalid audio format fails validation."""
        invalid_data = {
            "injection_config": {
                "latency_steps": [200],
                "tolerance_ms": 10,
                "seed": 42,
                "audio_format": "ogg",  # Not in enum
            }
        }
        is_valid, msg = validate_injection_config(invalid_data)
        assert not is_valid
        assert "Validation Error" in msg

    def test_with_results_object(self):
        """Test config with optional results object."""
        valid_data = {
            "injection_config": {
                "latency_steps": [200],
                "tolerance_ms": 10,
                "seed": 42,
            },
            "results": {
                "scenario_id": "scenario_001",
                "original_hash": "abc123",
                "injected_hash": "def456",
                "injected_duration_ms": 200,
                "expected_duration_ms": 200,
                "deviation_ms": 0.0,
                "passed_tolerance": True,
                "timestamp": "2024-01-01T12:00:00Z",
            },
        }
        is_valid, msg = validate_injection_config(valid_data)
        assert is_valid, f"Expected valid, got: {msg}"

    def test_validate_from_json_file(self):
        """Test validation from a JSON file path."""
        data = {
            "injection_config": {
                "latency_steps": [200],
                "tolerance_ms": 10,
                "seed": 42,
            }
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            is_valid, msg = validate_injection_config(temp_path)
            assert is_valid, f"Expected valid, got: {msg}"
        finally:
            Path(temp_path).unlink()

    def test_file_not_found(self):
        """Test validation with non-existent file."""
        is_valid, msg = validate_injection_config("/nonexistent/path/config.json")
        assert not is_valid
        assert "not found" in msg.lower()
