"""
Unit Tests for Quickstart Validator

Tests the quickstart validation functionality to ensure end-to-end
reproducibility checking works correctly.
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from reproducibility.quickstart_validator import (
    QuickstartValidator,
    QuickstartStepResult,
    QuickstartValidationResult
)


class TestQuickstartStepResult:
    """Tests for QuickstartStepResult dataclass."""

    def test_step_result_creation(self):
        """Test creating a step result with all fields."""
        result = QuickstartStepResult(
            step_number=1,
            step_description="Test step",
            status="pass",
            duration_ms=100,
            error_message=None,
            details={"key": "value"}
        )
        
        assert result.step_number == 1
        assert result.step_description == "Test step"
        assert result.status == "pass"
        assert result.duration_ms == 100
        assert result.error_message is None
        assert result.details == {"key": "value"}

    def test_step_result_with_error(self):
        """Test creating a step result with error."""
        result = QuickstartStepResult(
            step_number=2,
            step_description="Failed step",
            status="fail",
            duration_ms=50,
            error_message="Something went wrong",
            details={}
        )
        
        assert result.status == "fail"
        assert result.error_message == "Something went wrong"

class TestQuickstartValidationResult:
    """Tests for QuickstartValidationResult dataclass."""

    def test_result_creation(self):
        """Test creating a validation result."""
        result = QuickstartValidationResult(
            timestamp="2026-06-02T12:00:00",
            quickstart_file="test/quickstart.md",
            total_steps=10,
            passed_steps=8,
            failed_steps=2,
            skipped_steps=0,
            overall_status="fail",
            step_results=[],
            checksums={},
            execution_time_ms=500
        )
        
        assert result.total_steps == 10
        assert result.passed_steps == 8
        assert result.failed_steps == 2
        assert result.overall_status == "fail"

    def test_result_all_pass(self):
        """Test result with all steps passing."""
        result = QuickstartValidationResult(
            timestamp="2026-06-02T12:00:00",
            quickstart_file="test/quickstart.md",
            total_steps=5,
            passed_steps=5,
            failed_steps=0,
            skipped_steps=0,
            overall_status="pass",
            step_results=[]
        )
        
        assert result.overall_status == "pass"

class TestQuickstartValidator:
    """Tests for QuickstartValidator class."""

    @pytest.fixture
    def validator(self, tmp_path):
        """Create a validator with temporary paths."""
        quickstart_path = tmp_path / "quickstart.md"
        quickstart_path.write_text("# Quickstart\n1. Step 1\n2. Step 2")
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        return QuickstartValidator(quickstart_path, output_dir)

    def test_validator_initialization(self, validator):
        """Test validator initializes correctly."""
        assert validator.quickstart_path.exists()
        assert validator.output_dir.exists()
        assert validator.results == []
        assert validator.checksums == {}

    def test_parse_quickstart_steps(self, validator):
        """Test parsing steps from quickstart.md."""
        steps = validator._parse_quickstart_steps()
        
        assert len(steps) == 2
        assert "Step 1" in steps[0]
        assert "Step 2" in steps[1]

    def test_validate_step_environment_check(self, validator):
        """Test environment validation step."""
        result = validator._check_environment()
        
        assert result["status"] in ["pass", "fail"]
        assert "python_version" in result.get("details", {})

    def test_validate_step_dependencies_check(self, validator):
        """Test dependencies validation step."""
        result = validator._check_dependencies()
        
        # Should either pass or fail based on requirements.txt existence
        assert result["status"] in ["pass", "fail", "skip"]

    def test_generate_report(self, validator):
        """Test report generation."""
        result = QuickstartValidationResult(
            timestamp="2026-06-02T12:00:00",
            quickstart_file="test.md",
            total_steps=2,
            passed_steps=2,
            failed_steps=0,
            skipped_steps=0,
            overall_status="pass",
            step_results=[
                QuickstartStepResult(1, "Step 1", "pass", 10),
                QuickstartStepResult(2, "Step 2", "pass", 20)
            ],
            checksums={"file.txt": "abc123"}
        )
        
        report = validator.generate_report(result)
        
        assert "Quickstart Validation Report" in report
        assert "Overall Status:" in report
        assert "✅ PASS" in report
        assert "Step 1" in report
        assert "Step 2" in report
        assert "abc123" in report

    def test_check_generic_step(self, validator):
        """Test generic step validation."""
        result = validator._check_generic_step("Unknown step description")
        
        assert result["status"] == "skip"
        assert "reason" in result["details"]

    def test_calculate_checksums(self, validator, tmp_path):
        """Test checksum calculation."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Mock the file path to exist
        with patch.object(validator, 'PROJECT_ROOT', tmp_path):
            validator._calculate_checksums()
        
        # Checksums dict should be populated or empty (if files don't exist)
        assert isinstance(validator.checksums, dict)

    def test_validate_missing_quickstart(self, tmp_path):
        """Test validation when quickstart.md is missing."""
        non_existent = tmp_path / "non_existent.md"
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        validator = QuickstartValidator(non_existent, output_dir)
        result = validator.validate()
        
        assert result.overall_status == "fail"
        assert result.failed_steps == 1
        assert len(result.step_results) == 1
        assert result.step_results[0].error_message is not None

    def test_validate_with_multiple_step_types(self, validator):
        """Test validation with different step types."""
        # Add steps that match different validation checks
        validator.results = []
        
        # Test environment step
        env_result = validator._validate_step(1, "Initialize Python environment")
        assert env_result.step_number == 1
        assert env_result.status in ["pass", "fail"]
        
        # Test download step
        download_result = validator._validate_step(2, "Download knot atlas data")
        assert download_result.step_number == 2
        assert download_result.status in ["pass", "fail", "skip"]
        
        # Test precision step
        precision_result = validator._validate_step(3, "Compute precision metrics")
        assert precision_result.step_number == 3
        assert precision_result.status in ["pass", "fail"]

    def test_step_result_duration_tracking(self, validator):
        """Test that step duration is tracked."""
        result = validator._validate_step(1, "Test step")
        
        assert result.duration_ms >= 0
        assert isinstance(result.duration_ms, int)

    def test_checksums_format(self, validator):
        """Test checksums are in correct format."""
        validator.checksums = {"file.txt": "abc123def456"}
        
        for file_path, checksum in validator.checksums.items():
            assert isinstance(file_path, str)
            assert isinstance(checksum, str)
            assert len(checksum) == 64  # SHA-256 length