import json
import os
from pathlib import Path
import tempfile
import pytest
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.data_hygiene_audit import (
    compute_file_hash,
    get_generated_workflow_ids,
    get_processed_workflow_ids,
    get_results_workflow_ids,
    check_for_non_generated_files,
    check_derivation_consistency,
)

@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary data directories."""
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    results_dir = tmp_path / "data" / "results"
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir()
    results_dir.mkdir()
    return {
        "raw": raw_dir,
        "processed": processed_dir,
        "results": results_dir,
    }

def test_compute_file_hash(temp_dirs):
    """Test SHA-256 hash computation."""
    test_file = temp_dirs["raw"] / "test.json"
    test_file.write_text("test content")
    hash1 = compute_file_hash(test_file)
    hash2 = compute_file_hash(test_file)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length

def test_get_generated_workflow_ids(temp_dirs):
    """Test extraction of workflow IDs from generated files."""
    # Create a valid generated workflow file
    workflow_data = [
        {"workflow_id": "wf-001", "nodes": [], "edges": []},
        {"workflow_id": "wf-002", "nodes": [], "edges": []},
    ]
    (temp_dirs["raw"] / "workflows.json").write_text(json.dumps(workflow_data))

    ids = get_generated_workflow_ids(temp_dirs["raw"])
    assert "wf-001" in ids
    assert "wf-002" in ids
    assert len(ids) == 2

def test_get_processed_workflow_ids(temp_dirs):
    """Test extraction of workflow IDs from processed logs."""
    # Create a processed log file
    log_data = [
        {"workflow_id": "wf-001", "status": "success"},
        {"workflow_id": "wf-003", "status": "failed"},
    ]
    (temp_dirs["processed"] / "log.json").write_text(json.dumps(log_data))

    ids = get_processed_workflow_ids(temp_dirs["processed"])
    assert "wf-001" in ids
    assert "wf-003" in ids

def test_get_results_workflow_ids(temp_dirs):
    """Test extraction of workflow IDs from results."""
    # Create a results file
    result_data = {
        "threshold": 0.5,
        "workflows_analyzed": ["wf-001", "wf-002"],
    }
    (temp_dirs["results"] / "analysis.json").write_text(json.dumps(result_data))

    ids = get_results_workflow_ids(temp_dirs["results"])
    assert "wf-001" in ids
    assert "wf-002" in ids

def test_check_for_non_generated_files_valid(temp_dirs):
    """Test detection of valid generated files."""
    valid_data = {"workflow_id": "wf-001", "nodes": [], "edges": []}
    (temp_dirs["raw"] / "valid.json").write_text(json.dumps(valid_data))

    is_clean, suspicious = check_for_non_generated_files(temp_dirs["raw"])
    assert is_clean
    assert len(suspicious) == 0

def test_check_for_non_generated_files_invalid(temp_dirs):
    """Test detection of non-generated files."""
    # Create a non-JSON file
    (temp_dirs["raw"] / "notes.txt").write_text("hand edited notes")

    # Create a JSON file without workflow_id
    bad_data = {"random_key": "value"}
    (temp_dirs["raw"] / "bad.json").write_text(json.dumps(bad_data))

    is_clean, suspicious = check_for_non_generated_files(temp_dirs["raw"])
    assert not is_clean
    assert len(suspicious) == 2

def test_check_derivation_consistency(temp_dirs):
    """Test derivation consistency check."""
    raw_ids = {"wf-001", "wf-002"}
    processed_ids = {"wf-001"}
    results_ids = {"wf-001"}

    is_consistent, details = check_derivation_consistency(raw_ids, processed_ids, results_ids)
    assert is_consistent
    assert len(details) == 1  # Warning about missing processed

def test_check_derivation_consistency_orphans(temp_dirs):
    """Test detection of orphan IDs in processed/results."""
    raw_ids = {"wf-001"}
    processed_ids = {"wf-001", "wf-999"}  # wf-999 is orphan
    results_ids = {"wf-001"}

    is_consistent, details = check_derivation_consistency(raw_ids, processed_ids, results_ids)
    assert not is_consistent
    assert any("unknown workflow IDs" in d for d in details)