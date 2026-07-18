"""
Integration tests for the reproducibility verification module.
These tests verify that the reproducibility check works end-to-end.
"""
import os
import json
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import yaml

# Import the module under test
from utils.reproducibility import (
    load_previous_checksums,
    compute_current_checksums,
    compare_checksums,
    save_reproducibility_report,
    verify_reproducibility,
    get_previous_checksums_path
)
from config.settings import get_config


@pytest.fixture
def temp_project_state_dir(tmp_path):
    """Create a temporary project state directory structure."""
    # Create the directory structure
    project_id = "PROJ-139-the-influence-of-emotional-contagion-on-"
    state_dir = tmp_path / "state" / "projects" / project_id
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


@pytest.fixture
def sample_artifacts(tmp_path):
    """Create sample artifact files with known content."""
    # Create a temporary data directory
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Create sample files
    file1 = data_dir / "metrics_results.csv"
    file1.write_text("id,sentiment_slope,contagion_index\n1,0.5,0.8\n2,0.3,0.6\n")

    file2 = data_dir / "valid_threads.csv"
    file2.write_text("thread_id,valid,ground_truth\n1,true,0.9\n2,false,0.5\n")

    return [file1, file2]


@pytest.fixture
def previous_checksums_file(temp_project_state_dir, sample_artifacts):
    """Create a previous checksums file with matching hashes."""
    # Compute hashes for the sample artifacts
    hashes = {}
    for artifact in sample_artifacts:
        rel_path = str(artifact.relative_to(Path.cwd()))
        with open(artifact, 'rb') as f:
            content = f.read()
            hashes[rel_path] = hashlib.sha256(content).hexdigest()

    checksum_data = {
        "project_id": "PROJ-139-the-influence-of-emotional-contagion-on-",
        "artifact_hashes": hashes,
        "metadata": {
            "run_id": "previous_run_123",
            "timestamp": "2023-01-01T00:00:00Z"
        }
    }

    checksum_file = temp_project_state_dir / "checksums.yaml"
    with open(checksum_file, 'w') as f:
        yaml.dump(checksum_data, f)

    return checksum_file


def test_load_previous_checksums_success(previous_checksums_file):
    """Test that previous checksums can be loaded successfully."""
    result = load_previous_checksums()
    assert result is not None
    assert "artifact_hashes" in result
    assert len(result["artifact_hashes"]) > 0


def test_load_previous_checksums_missing_file(tmp_path, temp_project_state_dir):
    """Test handling of missing previous checksums file."""
    # Ensure the file doesn't exist
    checksum_file = get_previous_checksums_path()
    if checksum_file.exists():
        checksum_file.unlink()

    result = load_previous_checksums()
    assert result is None


def test_compare_checksums_perfect_match(previous_checksums_file, sample_artifacts):
    """Test comparison when all checksums match."""
    previous = load_previous_checksums()
    current = compute_current_checksums()

    is_match, differences = compare_checksums(previous, current)

    assert is_match is True
    assert len(differences) == 0


def test_compare_checksums_mismatch(tmp_path, previous_checksums_file, sample_artifacts):
    """Test comparison when a checksum mismatch is detected."""
    # Modify one of the artifact files
    modified_file = sample_artifacts[0]
    original_content = modified_file.read_text()
    modified_file.write_text(original_content + "\n# Modified")

    try:
        previous = load_previous_checksums()
        current = compute_current_checksums()

        is_match, differences = compare_checksums(previous, current)

        assert is_match is False
        assert len(differences) == 1
        assert differences[0]["status"] == "mismatch"
        assert differences[0]["path"] in str(sample_artifacts[0].relative_to(Path.cwd()))
    finally:
        # Restore original content
        modified_file.write_text(original_content)


def test_compare_checksums_missing_file(tmp_path, previous_checksums_file, sample_artifacts):
    """Test comparison when a file is missing in current."""
    # Remove one of the artifact files
    removed_file = sample_artifacts[1]
    removed_file.unlink()

    try:
        previous = load_previous_checksums()
        current = compute_current_checksums()

        is_match, differences = compare_checksums(previous, current)

        assert is_match is False
        assert len(differences) == 1
        assert differences[0]["status"] == "missing"
    finally:
        # Recreate the file
        removed_file.write_text("thread_id,valid,ground_truth\n1,true,0.9\n2,false,0.5\n")


def test_save_reproducibility_report(tmp_path, previous_checksums_file, sample_artifacts):
    """Test that a reproducibility report is saved correctly."""
    previous = load_previous_checksums()
    current = compute_current_checksums()
    is_match, differences = compare_checksums(previous, current)

    output_path = tmp_path / "reproducibility_report.json"
    save_reproducibility_report(is_match, differences, previous, current, output_path)

    assert output_path.exists()
    with open(output_path, 'r') as f:
        report = json.load(f)

    assert "reproducibility_verified" in report
    assert "differences" in report
    assert report["reproducibility_verified"] == is_match


@patch('utils.reproducibility.run_pipeline_if_needed')
@patch('utils.reproducibility.load_previous_checksums')
@patch('utils.reproducibility.compute_current_checksums')
@patch('utils.reproducibility.compare_checksums')
@patch('utils.reproducibility.save_reproducibility_report')
def test_verify_reproducibility_success(
    mock_save_report,
    mock_compare,
    mock_compute,
    mock_load,
    mock_run_pipeline
):
    """Test the full verify_reproducibility flow with success."""
    # Setup mocks
    mock_run_pipeline.return_value = True
    mock_load.return_value = {"artifact_hashes": {"file1.csv": "abc123"}}
    mock_compute.return_value = {"file1.csv": "abc123"}
    mock_compare.return_value = (True, [])
    mock_save_report.return_value = None

    result = verify_reproducibility()

    assert result is True
    mock_run_pipeline.assert_called_once()
    mock_load.assert_called_once()
    mock_compute.assert_called_once()
    mock_compare.assert_called_once()
    mock_save_report.assert_called_once()


@patch('utils.reproducibility.run_pipeline_if_needed')
def test_verify_reproducibility_pipeline_failure(mock_run_pipeline):
    """Test verify_reproducibility when pipeline run fails."""
    mock_run_pipeline.return_value = False

    result = verify_reproducibility()

    assert result is False
    mock_run_pipeline.assert_called_once()