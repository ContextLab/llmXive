"""
Unit tests for the report verification script (T038a).
"""

import json
import tempfile
from pathlib import Path
import pytest
import sys
import os

# Add parent directory to path for imports if running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis.verify_report import load_report, verify_disclaimers


class TestLoadReport:
    """Tests for the load_report function."""

    def test_load_valid_report(self, tmp_path: Path):
        """Test loading a valid report file."""
        report_data = {
            "report_text": "This study presents an associational analysis of network topology.",
            "metadata": {"version": "1.0"}
        }
        report_file = tmp_path / "report.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f)

        text = load_report(report_file)
        assert "associational" in text

    def test_load_missing_file(self, tmp_path: Path):
        """Test loading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_report(tmp_path / "non_existent.json")

    def test_load_missing_key(self, tmp_path: Path):
        """Test loading a file missing the 'report_text' key raises KeyError."""
        report_data = {
            "some_other_key": "value"
        }
        report_file = tmp_path / "report.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f)

        with pytest.raises(KeyError):
            load_report(report_file)


class TestVerifyDisclaimers:
    """Tests for the verify_disclaimers function."""

    def test_term_present(self):
        """Test that verification passes when term is present."""
        text = "This is an associational study."
        assert verify_disclaimers(text, ["associational"]) is True

    def test_term_case_insensitive(self):
        """Test that verification is case-insensitive."""
        text = "This is an Associational Study."
        assert verify_disclaimers(text, ["associational"]) is True

    def test_term_missing(self):
        """Test that verification fails when term is missing."""
        text = "This is a causal study."
        assert verify_disclaimers(text, ["associational"]) is False

    def test_multiple_terms_all_present(self):
        """Test verification with multiple terms, all present."""
        text = "This associational study also includes a cautionary note."
        assert verify_disclaimers(text, ["associational", "cautionary"]) is True

    def test_multiple_terms_one_missing(self):
        """Test verification with multiple terms, one missing."""
        text = "This associational study."
        assert verify_disclaimers(text, ["associational", "cautionary"]) is False

    def test_default_terms(self):
        """Test that default term is 'associational'."""
        text = "This is an associational study."
        # Call without providing terms argument
        assert verify_disclaimers(text) is True

        text_missing = "This is a causal study."
        assert verify_disclaimers(text_missing) is False
