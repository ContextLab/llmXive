"""
Unit tests for the Framing Validator module.
"""

import pytest
import tempfile
from pathlib import Path
from utils.framing_validator import (
    scan_for_causal_verbs,
    validate_report,
    generate_validation_report,
    CAUSAL_VERBS
)

class TestScanForCausalVerbs:
    """Tests for the scan_for_causal_verbs function."""

    def test_detects_simple_causal_verb(self):
        """Test detection of a simple causal verb."""
        text = "Social exclusion causes reduced activation."
        violations = scan_for_causal_verbs(text)
        assert len(violations) == 1
        assert violations[0]["verb"] == "causes"
        assert "causes" in violations[0]["context"]

    def test_detects_multiple_causal_verbs(self):
        """Test detection of multiple causal verbs in one text."""
        text = """
        Social exclusion causes reduced activation.
        This leads to lower reward processing.
        """
        violations = scan_for_causal_verbs(text)
        assert len(violations) == 2
        verbs = [v["verb"] for v in violations]
        assert "causes" in verbs
        assert "leads to" in verbs

    def test_case_insensitive_detection(self):
        """Test that detection is case-insensitive."""
        text = "Social Exclusion CAUSES reduced activation."
        violations = scan_for_causal_verbs(text)
        assert len(violations) == 1
        assert violations[0]["verb"] == "CAUSES"

    def test_ignores_non_causal_language(self):
        """Test that associational language is not flagged."""
        text = "Social exclusion is associated with reduced activation."
        violations = scan_for_causal_verbs(text)
        assert len(violations) == 0

    def test_word_boundary_matching(self):
        """Test that verbs are matched as whole words."""
        text = "The social exclusion causes problems. However, 'caused' is also flagged."
        violations = scan_for_causal_verbs(text)
        assert len(violations) == 2

class TestValidateReport:
    """Tests for the validate_report function."""

    def test_valid_report(self):
        """Test validation of a report without causal language."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("Social exclusion is associated with reduced activation.\n")
            f.write("There is a correlation between exclusion and reward processing.\n")
            temp_path = Path(f.name)

        try:
            is_valid, violations = validate_report(temp_path)
            assert is_valid is True
            assert len(violations) == 0
        finally:
            temp_path.unlink()

    def test_invalid_report(self):
        """Test validation of a report with causal language."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("Social exclusion causes reduced activation.\n")
            temp_path = Path(f.name)

        try:
            is_valid, violations = validate_report(temp_path)
            assert is_valid is False
            assert len(violations) == 1
        finally:
            temp_path.unlink()

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            validate_report(Path("/nonexistent/file.md"))

class TestGenerateValidationReport:
    """Tests for the generate_validation_report function."""

    def test_empty_violations(self):
        """Test report generation with no violations."""
        report = generate_validation_report([])
        assert "No causal language violations found" in report

    def test_violations_report(self):
        """Test report generation with violations."""
        violations = [
            {
                "verb": "causes",
                "line": 5,
                "context": "Social exclusion causes reduced activation",
                "full_line": "Social exclusion causes reduced activation."
            }
        ]
        report = generate_validation_report(violations)
        assert "1 causal language violation" in report
        assert "causes" in report
        assert "Line: 5" in report

class TestCausalVerbsList:
    """Tests for the CAUSAL_VERBS constant."""

    def test_required_verbs_present(self):
        """Test that all required causal verbs are in the list."""
        required_verbs = ["causes", "leads to", "results in", "induces", "forces"]
        for verb in required_verbs:
            assert verb in CAUSAL_VERBS