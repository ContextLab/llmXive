"""
Tests for state management and metadata logging functionality.
"""
import json
import os
import pytest
from pathlib import Path

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from state_manager import (
    log_unresolved_realization,
    log_unresolved_batch,
    get_unresolved_summary,
    clear_unresolved_log,
    METADATA_FILE,
    UNRESOLVED_LOG_FILE,
    STATE_DIR,
    DATA_RAW_DIR
)

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Clean up before and after each test."""
    # Clean up before test
    clear_unresolved_log()
    yield
    # Clean up after test
    clear_unresolved_log()

class TestUnresolvedLogging:
    """Tests for unresolved realization logging functionality."""

    def test_unresolved_log_creation(self):
        """Test that unresolved log files are created when logging."""
        log_unresolved_realization(
            realization_id=1,
            delta=0.5,
            reason="TEBD did not converge",
            details={"iterations": 100, "final_energy": 0.123}
        )

        assert METADATA_FILE.exists(), "metadata.json should be created"
        assert UNRESOLVED_LOG_FILE.exists(), "unresolved_realizations.json should be created"

    def test_unresolved_log_content(self):
        """Test that unresolved log contains correct data."""
        log_unresolved_realization(
            realization_id=42,
            delta=0.3,
            reason="Numerical instability",
            details={"error": "divergence detected"}
        )

        metadata = json.loads(METADATA_FILE.read_text())
        assert metadata["unresolved_count"] == 1
        assert len(metadata["unresolved_realizations"]) == 1
        
        entry = metadata["unresolved_realizations"][0]
        assert entry["realization_id"] == 42
        assert entry["delta"] == 0.3
        assert entry["reason"] == "Numerical instability"
        assert "details" in entry
        assert entry["details"]["error"] == "divergence detected"
        assert "logged_at" in entry

    def test_multiple_unresolved_realizations(self):
        """Test logging multiple unresolved realizations."""
        log_unresolved_realization(1, 0.2, "Convergence failure")
        log_unresolved_realization(2, 0.2, "Energy divergence")
        log_unresolved_realization(3, 0.2, "Bond dimension exceeded")

        metadata = json.loads(METADATA_FILE.read_text())
        assert metadata["unresolved_count"] == 3
        assert len(metadata["unresolved_realizations"]) == 3

    def test_batch_logging(self):
        """Test batch logging of unresolved realizations."""
        unresolved_list = [
            {"realization_id": 10, "reason": "Test reason 1", "details": {"code": "ERR1"}},
            {"realization_id": 11, "reason": "Test reason 2"},
            {"realization_id": 12, "reason": "Test reason 3", "details": {"code": "ERR3"}}
        ]

        log_unresolved_batch(unresolved_list, delta=0.5)

        metadata = json.loads(METADATA_FILE.read_text())
        assert metadata["unresolved_count"] == 3
        
        unresolved_log = json.loads(UNRESOLVED_LOG_FILE.read_text())
        assert len(unresolved_log) == 3
        
        # Verify all deltas are set correctly
        for entry in unresolved_log:
            assert entry["delta"] == 0.5

    def test_summary_function(self):
        """Test get_unresolved_summary returns correct data."""
        log_unresolved_realization(1, 0.1, "Reason A")
        log_unresolved_realization(2, 0.1, "Reason B")

        summary = get_unresolved_summary()
        
        assert summary["unresolved_count"] == 2
        assert len(summary["unresolved_realizations"]) == 2
        assert "created_at" in summary

    def test_directory_structure(self):
        """Test that required directories are created."""
        log_unresolved_realization(1, 0.0, "Test")
        
        assert DATA_RAW_DIR.exists(), "data/raw directory should exist"
        assert STATE_DIR.exists(), "state directory should exist"

    def test_json_format_validity(self):
        """Test that logged files are valid JSON."""
        log_unresolved_realization(1, 0.0, "Test")
        
        # Should not raise any exceptions
        metadata = json.loads(METADATA_FILE.read_text())
        unresolved_log = json.loads(UNRESOLVED_LOG_FILE.read_text())
        
        assert isinstance(metadata, dict)
        assert isinstance(unresolved_log, list)
