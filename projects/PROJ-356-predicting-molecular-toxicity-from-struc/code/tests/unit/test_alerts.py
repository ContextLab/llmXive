"""
Unit tests for the alerts validation and feature extraction module.
"""
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd

from src.features.alerts import (
    validate_alert_config,
    load_and_validate_alerts,
    generate_alert_vectors,
    compile_patterns
)
from src.utils.logger import setup_default_logger

# Setup logger for tests
setup_default_logger(level="WARNING")

class TestAlertValidation:
    """Tests for alert configuration validation logic."""

    def test_valid_config(self):
        """Test validation passes for a valid configuration."""
        config = {
            "patterns": [
                {
                    "pattern_id": "TEST_01",
                    "smarts_string": "[Cl]",
                    "weight": 1.0,
                    "source": "Test",
                    "description": "Chlorine"
                }
            ]
        }
        schema = {"type": "object"}  # Minimal schema for test
        is_valid, errors = validate_alert_config(config, schema)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_required_field(self):
        """Test validation fails when required field is missing."""
        config = {
            "patterns": [
                {
                    "pattern_id": "TEST_01",
                    "weight": 1.0
                    # Missing smarts_string
                }
            ]
        }
        schema = {"type": "object"}
        is_valid, errors = validate_alert_config(config, schema)
        
        assert is_valid is False
        assert any("smarts_string" in e for e in errors)

    def test_invalid_smarts(self):
        """Test validation fails for invalid SMARTS syntax."""
        config = {
            "patterns": [
                {
                    "pattern_id": "TEST_01",
                    "smarts_string": "[Cl",  # Unclosed bracket
                    "weight": 1.0
                }
            ]
        }
        schema = {"type": "object"}
        is_valid, errors = validate_alert_config(config, schema)
        
        assert is_valid is False
        assert any("invalid SMARTS" in e for e in errors)

    def test_duplicate_pattern_id(self):
        """Test validation fails for duplicate pattern IDs."""
        config = {
            "patterns": [
                {
                    "pattern_id": "TEST_01",
                    "smarts_string": "[Cl]",
                    "weight": 1.0
                },
                {
                    "pattern_id": "TEST_01",  # Duplicate
                    "smarts_string": "[Br]",
                    "weight": 1.0
                }
            ]
        }
        schema = {"type": "object"}
        is_valid, errors = validate_alert_config(config, schema)
        
        assert is_valid is False
        assert any("Duplicate pattern_id" in e for e in errors)

    def test_negative_weight(self):
        """Test validation fails for negative weight."""
        config = {
            "patterns": [
                {
                    "pattern_id": "TEST_01",
                    "smarts_string": "[Cl]",
                    "weight": -1.0
                }
            ]
        }
        schema = {"type": "object"}
        is_valid, errors = validate_alert_config(config, schema)
        
        assert is_valid is False
        assert any("negative weight" in e for e in errors)

class TestAlertVectors:
    """Tests for alert vector generation."""

    def test_generate_vectors_basic(self):
        """Test basic vector generation."""
        smiles = ["CCl", "CCBr", "C"]
        patterns = [
            {"pattern_id": "CHLORINE", "smarts_string": "[Cl]", "weight": 1.0},
            {"pattern_id": "BROMINE", "smarts_string": "[Br]", "weight": 1.0}
        ]
        
        df = generate_alert_vectors(smiles, patterns, log_missing=False)
        
        assert len(df) == 3
        assert list(df.columns) == ["smiles", "CHLORINE", "BROMINE"]
        
        # Check matches
        assert df.iloc[0]["CHLORINE"] == 1
        assert df.iloc[0]["BROMINE"] == 0
        assert df.iloc[1]["CHLORINE"] == 0
        assert df.iloc[1]["BROMINE"] == 1
        assert df.iloc[2]["CHLORINE"] == 0
        assert df.iloc[2]["BROMINE"] == 0

    def test_invalid_smiles_handling(self):
        """Test handling of invalid SMILES."""
        smiles = ["CCl", "INVALID_SMILES", "C"]
        patterns = [
            {"pattern_id": "CHLORINE", "smarts_string": "[Cl]", "weight": 1.0}
        ]
        
        df = generate_alert_vectors(smiles, patterns, log_missing=False)
        
        # Should skip invalid SMILES
        assert len(df) == 2
        assert "INVALID_SMILES" not in df["smiles"].values

    def test_empty_patterns(self):
        """Test error when no valid patterns."""
        smiles = ["CCl"]
        patterns = []
        
        with pytest.raises(ValueError, match="No valid patterns"):
            generate_alert_vectors(smiles, patterns)

class TestLoadAndValidate:
    """Tests for file loading and validation integration."""

    def test_load_valid_files(self):
        """Test loading valid config and schema files."""
        # Create temp config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "patterns": [
                    {"pattern_id": "TEST", "smarts_string": "[Cl]", "weight": 1.0, "source": "Test"}
                ]
            }, f)
            config_path = Path(f.name)

        # Create temp schema
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("type: object\n")
            schema_path = Path(f.name)

        try:
            patterns = load_and_validate_alerts(config_path, schema_path)
            assert len(patterns) == 1
            assert patterns[0]["pattern_id"] == "TEST"
        finally:
            config_path.unlink()
            schema_path.unlink()

    def test_missing_config_file(self):
        """Test error when config file is missing."""
        with pytest.raises(FileNotFoundError):
            load_and_validate_alerts(Path("/nonexistent/config.json"), Path("/nonexistent/schema.yaml"))