"""
Unit tests for the terminology audit script.
"""

import os
import tempfile
import shutil
import yaml
from pathlib import Path
import pytest

# Import the functions to test
# Note: We need to add the parent directory to sys.path to import
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from utils.terminology_audit import (
    FORBIDDEN_PATTERNS,
    scan_file,
    load_state,
    save_state
)


class TestTerminologyAudit:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.state_file = Path(self.test_dir) / "test_state.yaml"

        # Mock the global STATE_FILE by patching
        import utils.terminology_audit as audit_module
        self.original_state_file = audit_module.STATE_FILE
        audit_module.STATE_FILE = self.state_file

        yield

        # Cleanup
        shutil.rmtree(self.test_dir)
        audit_module.STATE_FILE = self.original_state_file

    def test_forbidden_patterns_definition(self):
        """Test that forbidden patterns are defined correctly."""
        assert len(FORBIDDEN_PATTERNS) > 0
        for pattern, replacement in FORBIDDEN_PATTERNS:
            assert hasattr(pattern, 'search')
            assert isinstance(replacement, str)

    def test_scan_file_no_matches(self):
        """Test scanning a file with no forbidden terminology."""
        test_file = Path(self.test_dir) / "clean_file.txt"
        test_file.write_text("This is a clean file with no issues.\n")

        findings = scan_file(test_file)
        assert len(findings) == 0

        # File should remain unchanged
        assert test_file.read_text() == "This is a clean file with no issues.\n"

    def test_scan_file_with_first_principles(self):
        """Test scanning a file containing 'First-Principles'."""
        test_file = Path(self.test_dir) / "dirty_file.txt"
        content = "This model performs First-Principles calculations.\n"
        test_file.write_text(content)

        findings = scan_file(test_file)

        assert len(findings) == 1
        assert "First-Principles" in findings[0]['matched_text']
        assert findings[0]['replacement'] == "Surrogate"

        # File should be updated
        updated_content = test_file.read_text()
        assert "First-Principles" not in updated_content
        assert "Surrogate" in updated_content

    def test_scan_file_with_schrodinger(self):
        """Test scanning a file containing 'Schrödinger'."""
        test_file = Path(self.test_dir) / "schrodinger_file.txt"
        content = "We solve the Schrödinger equation for electrons.\n"
        test_file.write_text(content)

        findings = scan_file(test_file)

        assert len(findings) == 1
        assert "Schrödinger" in findings[0]['matched_text']
        assert findings[0]['replacement'] == "Quantum Mechanical"

        updated_content = test_file.read_text()
        assert "Schrödinger" not in updated_content
        assert "Quantum Mechanical" in updated_content

    def test_load_state_empty_file(self):
        """Test loading a non-existent state file."""
        # Ensure the file doesn't exist
        if self.state_file.exists():
            self.state_file.unlink()

        state = load_state()
        assert "artifact_hashes" in state
        assert "terminology_audit" in state
        assert state["artifact_hashes"] == {}
        assert state["terminology_audit"] == []

    def test_save_state_and_load(self):
        """Test saving and loading state."""
        test_state = {
            "artifact_hashes": {"data": "abc123"},
            "terminology_audit": [{"test": "value"}]
        }

        save_state(test_state)
        assert self.state_file.exists()

        loaded_state = load_state()
        assert loaded_state["artifact_hashes"]["data"] == "abc123"
        assert len(loaded_state["terminology_audit"]) == 1
        assert loaded_state["terminology_audit"][0]["test"] == "value"

    def test_case_insensitivity(self):
        """Test that patterns are case-insensitive."""
        test_file = Path(self.test_dir) / "case_test.txt"
        content = "FIRST-PRINCIPLES and first-principles and First-Principles are bad.\n"
        test_file.write_text(content)

        findings = scan_file(test_file)

        # Should find all 3 occurrences
        assert len(findings) == 3

        updated_content = test_file.read_text()
        assert "First-Principles" not in updated_content
        assert "Surrogate" in updated_content
        # Count replacements
        assert updated_content.count("Surrogate") == 3