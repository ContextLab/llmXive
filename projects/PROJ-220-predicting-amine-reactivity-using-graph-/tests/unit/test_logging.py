"""
Unit tests for the audit logging infrastructure (T005).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# We need to mock the get_project_root to use a temp directory for tests
# to avoid polluting the actual project data directory during unit tests.
@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project root for testing."""
    # Create the expected subdirectories
    data_raw = tmp_path / "data" / "raw"
    data_raw.mkdir(parents=True)
    return tmp_path

@pytest.fixture
def mock_versioning(temp_project_root):
    """Patch get_project_root to return our temp directory."""
    with patch("src.utils.logging.get_project_root", return_value=temp_project_root):
        with patch("src.utils.logging.update_state"):
            yield temp_project_root

def test_audit_logger_initialization(mock_versioning):
    """Test that the AuditLogger initializes the log file correctly."""
    from src.utils.logging import AuditLogger

    logger = AuditLogger(project_id="TEST-001")
    
    # Check that the file was created
    log_path = mock_versioning / "data" / "raw" / "audit_log.json"
    assert log_path.exists()

    # Check content structure
    with open(log_path, "r") as f:
        data = json.load(f)

    assert data["log_version"] == "1.0"
    assert data["project_id"] == "TEST-001"
    assert "entries" in data
    assert len(data["entries"]) == 0

def test_log_exclusion(mock_versioning):
    """Test logging an exclusion event."""
    from src.utils.logging import AuditLogger

    logger = AuditLogger(project_id="TEST-002")
    
    entry_id = logger.log_exclusion(
        reason="Invalid SMILES",
        record_id="CHEMBL_123",
        data_source="ChEMBL",
        details={"smiles": "invalid", "error": "Valence error"},
        severity="WARNING"
    )

    assert entry_id is not None
    assert len(entry_id) == 36  # UUID length

    # Verify persistence
    log_path = mock_versioning / "data" / "raw" / "audit_log.json"
    with open(log_path, "r") as f:
        data = json.load(f)

    assert len(data["entries"]) == 1
    entry = data["entries"][0]
    
    assert entry["type"] == "exclusion"
    assert entry["reason"] == "Invalid SMILES"
    assert entry["record_id"] == "CHEMBL_123"
    assert entry["data_source"] == "ChEMBL"
    assert entry["severity"] == "WARNING"
    assert entry["details"]["smiles"] == "invalid"

def test_log_event(mock_versioning):
    """Test logging a general pipeline event."""
    from src.utils.logging import AuditLogger

    logger = AuditLogger(project_id="TEST-003")
    
    entry_id = logger.log_event(
        event_type="START",
        message="Pipeline execution started",
        details={"version": "1.0.0"}
    )

    assert entry_id is not None

    log_path = mock_versioning / "data" / "raw" / "audit_log.json"
    with open(log_path, "r") as f:
        data = json.load(f)

    assert len(data["entries"]) == 1
    entry = data["entries"][0]
    
    assert entry["type"] == "event"
    assert entry["event_type"] == "START"
    assert entry["message"] == "Pipeline execution started"

def test_get_exclusion_summary(mock_versioning):
    """Test the exclusion summary calculation."""
    from src.utils.logging import AuditLogger

    logger = AuditLogger(project_id="TEST-004")
    
    # Log multiple exclusions
    logger.log_exclusion(reason="Invalid SMILES", record_id="A")
    logger.log_exclusion(reason="Invalid SMILES", record_id="B")
    logger.log_exclusion(reason="Missing Kinetics", record_id="C")
    logger.log_event(event_type="INFO", message="Ignored")

    summary = logger.get_exclusion_summary()

    assert summary["Invalid SMILES"] == 2
    assert summary["Missing Kinetics"] == 1
    assert len(summary) == 2

def test_get_total_exclusions(mock_versioning):
    """Test the total exclusion count."""
    from src.utils.logging import AuditLogger

    logger = AuditLogger(project_id="TEST-005")
    
    logger.log_exclusion(reason="Test", record_id="1")
    logger.log_exclusion(reason="Test", record_id="2")
    logger.log_event(event_type="INFO", message="Ignored")

    assert logger.get_total_exclusions() == 2

def test_convenience_function(mock_versioning):
    """Test the top-level log_exclusion function."""
    from src.utils.logging import log_exclusion

    entry_id = log_exclusion(
        reason="Test Convenience",
        record_id="CONV_1",
        project_id="TEST-006"
    )

    assert entry_id is not None

    # Verify it was logged to the correct temp location
    log_path = mock_versioning / "data" / "raw" / "audit_log.json"
    with open(log_path, "r") as f:
        data = json.load(f)

    # Note: The module might have cached the logger if not re-imported,
    # but since we are mocking the path, the file should be written there.
    # However, the convenience function creates a new instance every time.
    # We need to ensure the file path matches the mocked root.
    # Since the mock is active, the file is written to the temp dir.
    
    # Check if the entry exists (might be in a different run context if not careful,
    # but here we assume the mock persists for the function call).
    # To be safe, we re-read the file written by the convenience function.
    # The convenience function uses the mocked get_project_root.
    
    found = False
    for entry in data.get("entries", []):
        if entry.get("reason") == "Test Convenience":
            found = True
            break
    
    assert found, "Convenience function did not log to the expected file"