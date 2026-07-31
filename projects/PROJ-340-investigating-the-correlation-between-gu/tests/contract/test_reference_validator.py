"""
Contract tests for the Reference Validator Agent (T009b).

These tests verify that the Reference Validator correctly validates
the pipeline structure and operates in "Logic Only" mode for the
synthetic data study.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from code.reference_validator import ReferenceValidator, VerificationStatus

def test_validate_structure_passes_with_valid_files():
    """Test that validation passes when all required files exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        # Create required directories
        (root / "data" / "config").mkdir(parents=True)
        (root / "code").mkdir()
        (root / "data" / "results").mkdir()
        
        # Create required files
        (root / "data" / "config" / "required_variables.yaml").write_text("required_predictors: []\nrequired_outcomes: []\n")
        (root / "data" / "config" / "verified_data_sources.yaml").write_text("sources: []\n")
        (root / "code" / "ingest.py").write_text("# mock")
        (root / "code" / "analysis.py").write_text("# mock")
        (root / "code" / "diagnostics.py").write_text("# mock")
        (root / "code" / "report.py").write_text("# mock")
        (root / "code" / "data_generator.py").write_text("# mock")
        
        validator = ReferenceValidator(root)
        result = validator.validate_structure()
        
        assert result.status == VerificationStatus.PASSED
        assert "missing" not in result.details

def test_validate_structure_fails_with_missing_config():
    """Test that validation fails if config files are missing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        (root / "data" / "config").mkdir(parents=True)
        (root / "code").mkdir()
        (root / "data" / "results").mkdir()
        
        # Missing required_variables.yaml
        
        validator = ReferenceValidator(root)
        result = validator.validate_structure()
        
        assert result.status == VerificationStatus.FAILED
        assert "required_variables.yaml" in str(result.details.get("missing", []))

def test_validate_synthetic_mode_passes_without_real_data():
    """Test that validation passes (with warning/info) when no real data is registered."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        (root / "data" / "config").mkdir(parents=True)
        (root / "code").mkdir()
        (root / "data" / "results").mkdir()
        
        # Create required files but empty sources
        (root / "data" / "config" / "required_variables.yaml").write_text("required_predictors: []\nrequired_outcomes: []\n")
        (root / "data" / "config" / "verified_data_sources.yaml").write_text("sources: []\n")
        
        validator = ReferenceValidator(root)
        result = validator.validate_synthetic_mode()
        
        # Should pass or warn, but not fail
        assert result.status in [VerificationStatus.PASSED, VerificationStatus.WARNING]

def test_validate_code_integrity_fails_with_missing_module():
    """Test that validation fails if a critical module is missing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        (root / "data" / "config").mkdir(parents=True)
        (root / "code").mkdir()
        (root / "data" / "results").mkdir()
        
        (root / "data" / "config" / "required_variables.yaml").write_text("required_predictors: []\nrequired_outcomes: []\n")
        (root / "data" / "config" / "verified_data_sources.yaml").write_text("sources: []\n")
        
        # Only create some modules, missing 'analysis.py'
        (root / "code" / "ingest.py").write_text("# mock")
        (root / "code" / "diagnostics.py").write_text("# mock")
        
        validator = ReferenceValidator(root)
        result = validator.validate_code_integrity()
        
        assert result.status == VerificationStatus.FAILED
        assert "analysis.py" in str(result.details.get("missing", []))

def test_validate_references_aggregates_results():
    """Test that the main validate_references method aggregates all checks."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        (root / "data" / "config").mkdir(parents=True)
        (root / "code").mkdir()
        (root / "data" / "results").mkdir()
        
        (root / "data" / "config" / "required_variables.yaml").write_text("required_predictors: []\nrequired_outcomes: []\n")
        (root / "data" / "config" / "verified_data_sources.yaml").write_text("sources: []\n")
        (root / "code" / "ingest.py").write_text("# mock")
        (root / "code" / "analysis.py").write_text("# mock")
        (root / "code" / "diagnostics.py").write_text("# mock")
        (root / "code" / "report.py").write_text("# mock")
        (root / "code" / "data_generator.py").write_text("# mock")
        
        validator = ReferenceValidator(root)
        result = validator.validate_references()
        
        assert result.status == VerificationStatus.PASSED
        assert "structure" in result.details
        assert "mode" in result.details
        assert "code_integrity" in result.details