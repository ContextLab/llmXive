"""
Tests for state management and checksum tracking.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest

# Import the functions we are testing
from state_manager import (
    log_unresolved_realization,
    get_unresolved_summary,
    clear_unresolved_log,
    _load_unresolved_log,
    _save_unresolved_log
)
from state_utils import (
    ensure_state_structure,
    compute_file_checksum,
    compute_directory_checksum,
    load_project_state,
    save_project_state,
    register_artifact,
    verify_artifact_integrity,
    get_artifact_summary,
    generate_state_report,
    STATE_DIR,
    PROJECTS_DIR,
    STATE_FILE
)

@pytest.fixture
def clean_state_dirs():
    """Fixture to clean up state directories before and after tests."""
    # Clean before
    if STATE_DIR.exists():
        import shutil
        shutil.rmtree(STATE_DIR)

    yield

    # Clean after
    if STATE_DIR.exists():
        import shutil
        shutil.rmtree(STATE_DIR)

def test_ensure_state_structure(clean_state_dirs):
    """Test that the state directory structure is created."""
    ensure_state_structure()
    assert STATE_DIR.exists()
    assert PROJECTS_DIR.exists()
    assert (STATE_DIR / "artifacts").exists()

def test_compute_file_checksum(clean_state_dirs):
    """Test file checksum computation."""
    ensure_state_structure()
    test_file = STATE_DIR / "test_checksum.txt"
    test_file.write_text("Hello, World!")

    checksum1 = compute_file_checksum(test_file)
    checksum2 = compute_file_checksum(test_file)

    assert checksum1 == checksum2
    assert len(checksum1) == 64  # SHA-256 hex digest

def test_compute_directory_checksum(clean_state_dirs):
    """Test directory checksum computation."""
    ensure_state_structure()
    test_dir = STATE_DIR / "test_dir"
    test_dir.mkdir()
    (test_dir / "file1.txt").write_text("Content 1")
    (test_dir / "file2.txt").write_text("Content 2")

    checksum1 = compute_directory_checksum(test_dir)
    checksum2 = compute_directory_checksum(test_dir)

    assert checksum1 == checksum2

def test_load_project_state(clean_state_dirs):
    """Test loading project state."""
    ensure_state_structure()
    state = load_project_state()

    assert "project_id" in state
    assert "version" in state
    assert "artifacts" in state
    assert "checksums" in state

def test_save_and_load_project_state(clean_state_dirs):
    """Test saving and loading project state."""
    ensure_state_structure()
    test_state = {
        "project_id": "TEST-001",
        "version": "1.0.0",
        "artifacts": {"test.txt": {"checksum": "abc123"}}
    }

    save_project_state(test_state)
    loaded_state = load_project_state()

    assert loaded_state["project_id"] == "TEST-001"
    assert loaded_state["version"] == "1.0.0"
    assert "test.txt" in loaded_state["artifacts"]

def test_register_artifact(clean_state_dirs):
    """Test artifact registration."""
    ensure_state_structure()
    test_file = STATE_DIR / "artifacts" / "test_data.csv"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("col1,col2\n1,2\n3,4")

    register_artifact(
        test_file,
        "csv",
        "Test data file",
        {"rows": 2}
    )

    state = load_project_state()
    rel_path = str(test_file.relative_to(Path(__file__).parent.parent))

    assert rel_path in state["artifacts"]
    assert state["artifacts"][rel_path]["type"] == "csv"
    assert "checksum" in state["artifacts"][rel_path]

def test_verify_artifact_integrity(clean_state_dirs):
    """Test artifact integrity verification."""
    ensure_state_structure()
    test_file = STATE_DIR / "artifacts" / "verify_test.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("Integrity test")

    register_artifact(test_file, "txt", "Integrity test file")
    assert verify_artifact_integrity(test_file) is True

    # Modify the file
    test_file.write_text("Modified content")
    assert verify_artifact_integrity(test_file) is False

def test_get_artifact_summary(clean_state_dirs):
    """Test getting artifact summary."""
    ensure_state_structure()
    test_file = STATE_DIR / "artifacts" / "summary_test.csv"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("a,b\n1,2")

    register_artifact(test_file, "csv", "Summary test file")

    rel_path = str(test_file.relative_to(Path(__file__).parent.parent))
    summary = get_artifact_summary(test_file)

    assert summary is not None
    assert summary["type"] == "csv"
    assert summary["description"] == "Summary test file"

def test_generate_state_report(clean_state_dirs):
    """Test state report generation."""
    ensure_state_structure()
    test_file = STATE_DIR / "artifacts" / "report_test.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("Report test")

    register_artifact(test_file, "txt", "Report test file")

    report_path = STATE_DIR / "state_report.txt"
    report = generate_state_report(report_path)

    assert "Project State Report" in report
    assert "Report test file" in report
    assert report_path.exists()

def test_unresolved_log_integration(clean_state_dirs):
    """Test the unresolved realization logging workflow."""
    # Log a single realization
    log_unresolved_realization(
        realization_id=1,
        delta=0.5,
        reason="Convergence failure",
        details={"iterations": 100}
    )

    # Log another
    log_unresolved_realization(
        realization_id=2,
        delta=0.5,
        reason="Convergence failure",
        details={"iterations": 150}
    )

    # Log a different reason
    log_unresolved_realization(
        realization_id=3,
        delta=0.8,
        reason="Memory overflow"
    )

    # Check summary
    summary = get_unresolved_summary()
    assert summary["total_unresolved"] == 3
    assert summary["by_reason"]["Convergence failure"] == 2
    assert summary["by_reason"]["Memory overflow"] == 1

    # Check by delta
    by_delta = [e for e in _load_unresolved_log() if e["delta"] == 0.5]
    assert len(by_delta) == 2

    # Clear log
    clear_unresolved_log()
    summary_after = get_unresolved_summary()
    assert summary_after["total_unresolved"] == 0
