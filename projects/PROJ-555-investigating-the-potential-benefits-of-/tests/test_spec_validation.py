"""
Unit tests for spec validation logic (T001b).
"""
import os
import tempfile
import pytest
from pathlib import Path
import logging

# Import the function to test
from code.spec_validation import verify_sc001_spec_requirement

class TestSpecValidation:
    def test_sc001_passes(self):
        """Test that verification passes when phrase is present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = Path(tmpdir) / "spec.md"
            log_path = Path(tmpdir) / "state" / "spec_validation.log"
            
            # Write a mock spec with the required phrase
            spec_path.parent.mkdir(parents=True, exist_ok=True)
            with open(spec_path, 'w') as f:
                f.write("# Spec Document\n\n## SC-001\nThe system supports up to 30 valid sites.")
            
            # This should not raise
            result = verify_sc001_spec_requirement(
                spec_path=str(spec_path),
                required_phrase="up to 30 valid sites",
                log_path=str(log_path)
            )
            assert result is True

    def test_sc001_fails_missing_phrase(self):
        """Test that verification raises RuntimeError when phrase is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = Path(tmpdir) / "spec.md"
            log_path = Path(tmpdir) / "state" / "spec_validation.log"
            
            spec_path.parent.mkdir(parents=True, exist_ok=True)
            with open(spec_path, 'w') as f:
                f.write("# Spec Document\n\n## SC-001\nThe system supports 50 valid sites.")
            
            with pytest.raises(RuntimeError, match="SC-001 Validation FAILED"):
                verify_sc001_spec_requirement(
                    spec_path=str(spec_path),
                    required_phrase="up to 30 valid sites",
                    log_path=str(log_path)
                )

    def test_sc001_fails_file_not_found(self):
        """Test that verification raises RuntimeError when file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = Path(tmpdir) / "non_existent.md"
            log_path = Path(tmpdir) / "state" / "spec_validation.log"
            
            with pytest.raises(RuntimeError, match="Spec file not found"):
                verify_sc001_spec_requirement(
                    spec_path=str(spec_path),
                    required_phrase="up to 30 valid sites",
                    log_path=str(log_path)
                )
