"""
Unit tests for metadata validation logic in validation.py (US4).

This module tests the validation functions defined in `code/validation.py`
to ensure they correctly enforce data independence, source verification,
and system size constraints as per FR-006, FR-007, and Constitution Principle VI.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any

# Import the module under test
from validation import (
    ValidationResult,
    ValidationReport,
    validate_source_independence,
    validate_system_size,
    validate_convergence,
    validate_configuration,
    run_validation_on_configs,
    save_validation_report,
    check_validation_logic
)
from models.atomic_config import AtomicConfiguration


class TestValidationResult:
    """Tests for the ValidationResult dataclass."""

    def test_result_creation_success(self):
        result = ValidationResult(
            config_id="config_001",
            is_valid=True,
            source="Zenodo",
            size=2000,
            reasons=[]
        )
        assert result.is_valid is True
        assert result.source == "Zenodo"
        assert result.size == 2000
        assert len(result.reasons) == 0

    def test_result_creation_failure(self):
        result = ValidationResult(
            config_id="config_002",
            is_valid=False,
            source="Internal",
            size=500,
            reasons=["Size < 1000 atoms", "Source not independent"]
        )
        assert result.is_valid is False
        assert len(result.reasons) == 2
        assert "Size < 1000 atoms" in result.reasons


class TestValidateSourceIndependence:
    """Tests for validate_source_independence function."""

    def test_independent_source(self):
        """Test that Zenodo source is considered independent."""
        result = validate_source_independence("config_001", "Zenodo")
        assert result.is_valid is True
        assert "Source not independent" not in result.reasons

    def test_internal_source(self):
        """Test that Internal source is considered dependent."""
        result = validate_source_independence("config_002", "Internal")
        assert result.is_valid is False
        assert "Source not independent" in result.reasons

    def test_unknown_source(self):
        """Test that unknown sources trigger a warning/failure."""
        result = validate_source_independence("config_003", "UnknownDB")
        assert result.is_valid is False
        assert "Source not independent" in result.reasons


class TestValidateSystemSize:
    """Tests for validate_system_size function."""

    def test_large_system(self):
        """Test system with >= 1000 atoms passes."""
        result = validate_system_size("config_001", 2000)
        assert result.is_valid is True
        assert "Size < 1000 atoms" not in result.reasons

    def test_exact_threshold(self):
        """Test system with exactly 1000 atoms passes."""
        result = validate_system_size("config_001", 1000)
        assert result.is_valid is True

    def test_small_system(self):
        """Test system with < 1000 atoms fails."""
        result = validate_system_size("config_002", 999)
        assert result.is_valid is False
        assert "Size < 1000 atoms" in result.reasons

    def test_very_small_system(self):
        """Test very small system fails."""
        result = validate_system_size("config_003", 100)
        assert result.is_valid is False
        assert "Size < 1000 atoms" in result.reasons


class TestValidateConvergence:
    """Tests for validate_convergence function."""

    def test_converged(self):
        """Test converged system passes."""
        result = validate_convergence("config_001", "thermodynamic_limit")
        assert result.is_valid is True
        assert "Convergence not verified" not in result.reasons

    def test_preliminary(self):
        """Test preliminary system is flagged."""
        result = validate_convergence("config_002", "preliminary")
        assert result.is_valid is False
        assert "Convergence not verified" in result.reasons

    def test_unknown_status(self):
        """Test unknown convergence status fails."""
        result = validate_convergence("config_003", "unknown")
        assert result.is_valid is False
        assert "Convergence not verified" in result.reasons


class TestValidateConfiguration:
    """Tests for the combined validate_configuration function."""

    def test_valid_config(self):
        """Test a configuration that passes all checks."""
        result = validate_configuration(
            config_id="config_001",
            source="Zenodo",
            size=2000,
            convergence="thermodynamic_limit"
        )
        assert result.is_valid is True
        assert len(result.reasons) == 0

    def test_invalid_size(self):
        """Test configuration failing size check."""
        result = validate_configuration(
            config_id="config_002",
            source="Zenodo",
            size=500,
            convergence="thermodynamic_limit"
        )
        assert result.is_valid is False
        assert "Size < 1000 atoms" in result.reasons

    def test_invalid_source(self):
        """Test configuration failing source check."""
        result = validate_configuration(
            config_id="config_003",
            source="Internal",
            size=2000,
            convergence="thermodynamic_limit"
        )
        assert result.is_valid is False
        assert "Source not independent" in result.reasons

    def test_multiple_failures(self):
        """Test configuration failing multiple checks."""
        result = validate_configuration(
            config_id="config_004",
            source="Internal",
            size=500,
            convergence="preliminary"
        )
        assert result.is_valid is False
        assert len(result.reasons) == 3
        assert "Size < 1000 atoms" in result.reasons
        assert "Source not independent" in result.reasons
        assert "Convergence not verified" in result.reasons


class TestRunValidationOnConfigs:
    """Tests for the run_validation_on_configs function."""

    def test_run_validation_with_mixed_results(self):
        """Test validation loop on a list of configs."""
        configs = [
            AtomicConfiguration(id="c1", n_atoms=2000, metadata={"source": "Zenodo", "convergence": "thermodynamic_limit"}),
            AtomicConfiguration(id="c2", n_atoms=500, metadata={"source": "Zenodo", "convergence": "thermodynamic_limit"}),
            AtomicConfiguration(id="c3", n_atoms=2000, metadata={"source": "Internal", "convergence": "thermodynamic_limit"}),
        ]

        report = run_validation_on_configs(configs)

        assert len(report.validated_configs) == 1
        assert "c1" in report.validated_configs
        assert len(report.excluded_configs) == 2
        assert "c2" in report.excluded_configs
        assert "c3" in report.excluded_configs

        assert report.reasons["c2"] == "Size < 1000 atoms"
        assert report.reasons["c3"] == "Source not independent"

    def test_run_validation_empty_list(self):
        """Test validation on empty list."""
        report = run_validation_on_configs([])
        assert len(report.validated_configs) == 0
        assert len(report.excluded_configs) == 0


class TestSaveValidationReport:
    """Tests for save_validation_report function."""

    def test_save_report(self):
        """Test saving report to a file."""
        report = ValidationReport(
            validated_configs=["c1"],
            excluded_configs=["c2"],
            reasons={"c2": "Size < 1000 atoms"}
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "validation_report.json"
            save_validation_report(report, output_path)

            assert output_path.exists()
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data["validated_configs"] == ["c1"]
            assert data["excluded_configs"] == ["c2"]
            assert data["reasons"]["c2"] == "Size < 1000 atoms"

class TestCheckValidationLogic:
    """Tests for the check_validation_logic helper."""

    def test_check_logic_exists(self):
        """Ensure the helper function exists and returns a dict."""
        result = check_validation_logic()
        assert isinstance(result, dict)
        assert "source_independence" in result
        assert "system_size" in result
        assert "convergence" in result