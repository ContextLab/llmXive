import os
import json
import yaml
import tempfile
import shutil
import pytest
from pathlib import Path

# Import the module under test
from reference_validator import ReferenceValidator, VerificationStatus

class TestReferenceValidator:
    """Unit tests for the Reference Validator Agent."""

    @pytest.fixture
    def temp_project(self):
        """Creates a temporary project directory structure for testing."""
        temp_dir = tempfile.mkdtemp()
        project_root = Path(temp_dir)
        
        # Create necessary directories
        (project_root / "data" / "metadata").mkdir(parents=True)
        (project_root / "data" / "citations").mkdir(parents=True)
        
        yield project_root
        
        # Cleanup
        shutil.rmtree(temp_dir)

    def test_synthetic_mode_passes_logic_only(self, temp_project):
        """Test that synthetic mode flag results in LOGIC_ONLY status."""
        # Create validation_mode_flag.json
        flag_file = temp_project / "data" / "metadata" / "validation_mode_flag.json"
        flag_data = {
            "active": True,
            "reason": "Pipeline Validation Study",
            "timestamp": "2023-10-27T10:00:00Z"
        }
        with open(flag_file, 'w') as f:
            json.dump(flag_data, f)

        validator = ReferenceValidator(project_root=temp_project)
        result = validator.validate_citations()

        assert result.status == VerificationStatus.LOGIC_ONLY
        assert result.score == 1.0
        assert "Synthetic mode active" in result.message

    def test_real_mode_empty_dois_fails(self, temp_project):
        """Test that real mode with empty/missing verified_dois.yaml fails."""
        # Ensure validation mode is OFF (or file missing)
        flag_file = temp_project / "data" / "metadata" / "validation_mode_flag.json"
        if flag_file.exists():
            flag_file.unlink()

        # Ensure verified_dois.yaml is empty or missing
        dois_file = temp_project / "data" / "citations" / "verified_dois.yaml"
        if dois_file.exists():
            dois_file.unlink()

        validator = ReferenceValidator(project_root=temp_project)
        result = validator.validate_citations()

        assert result.status == VerificationStatus.FAILED
        assert result.score == 0.0
        assert "Constitution Principle II violation" in result.message

    def test_real_mode_with_dois_passes(self, temp_project):
        """Test that real mode with valid DOIs passes."""
        # Ensure validation mode is OFF
        flag_file = temp_project / "data" / "metadata" / "validation_mode_flag.json"
        if flag_file.exists():
            flag_file.unlink()

        # Create verified_dois.yaml with data
        dois_file = temp_project / "data" / "citations" / "verified_dois.yaml"
        dois_data = {
            "dois": [
                "10.1038/s41586-021-03844-4",
                "10.1016/j.cell.2020.05.012"
            ]
        }
        with open(dois_file, 'w') as f:
            yaml.dump(dois_data, f)

        validator = ReferenceValidator(project_root=temp_project)
        result = validator.validate_citations()

        assert result.status == VerificationStatus.PASSED
        assert result.score == 1.0
        assert "Citation verification passed" in result.message

    def test_run_gate_returns_exit_codes(self, temp_project):
        """Test that run_gate returns correct exit codes."""
        # Test Failure Case
        validator_fail = ReferenceValidator(project_root=temp_project)
        exit_code_fail = validator_fail.run_gate()
        assert exit_code_fail == 1

        # Test Success Case (Synthetic)
        flag_file = temp_project / "data" / "metadata" / "validation_mode_flag.json"
        with open(flag_file, 'w') as f:
            json.dump({"active": True}, f)
        
        validator_pass = ReferenceValidator(project_root=temp_project)
        exit_code_pass = validator_pass.run_gate()
        assert exit_code_pass == 0
