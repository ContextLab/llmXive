"""
Test suite for T028: Verify reproducibility by re-running pipeline and matching checksums.

This test verifies that the full pipeline produces deterministic outputs
when re-run with the same inputs and random seeds.
"""
import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Import the reproducibility verification module
from code.data.verify_reproducibility import (
    compute_file_sha256,
    load_recorded_checksums,
    verify_artifacts,
    generate_report,
    main
)


class TestReproducibilityVerification:
    """Tests for the reproducibility verification functionality."""

    @pytest.fixture
    def temp_checksums_file(self, tmp_path):
        """Create a temporary checksums file for testing."""
        checksums = {
            "data/processed/valid_threads.csv": "abc123def456",
            "data/processed/thread_metrics.csv": "ghi789jkl012",
            "data/processed/sensitivity_analysis.csv": "mno345pqr678"
        }
        checksums_file = tmp_path / "checksums.json"
        with open(checksums_file, 'w') as f:
            json.dump(checksums, f)
        return str(checksums_file)

    @pytest.fixture
    def temp_artifact_files(self, tmp_path):
        """Create temporary artifact files for testing."""
        # Create directory structure
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)

        # Create test files with known content
        files = {
            "valid_threads.csv": processed_dir / "valid_threads.csv",
            "thread_metrics.csv": processed_dir / "thread_metrics.csv",
            "sensitivity_analysis.csv": processed_dir / "sensitivity_analysis.csv"
        }

        for filename, filepath in files.items():
            with open(filepath, 'w') as f:
                f.write(f"Test content for {filename}\n")

        return {
            "path": str(tmp_path),
            "files": files
        }

    def test_compute_file_sha256_basic(self, temp_artifact_files):
        """Test basic SHA256 computation for a file."""
        filepath = temp_artifact_files['files']['valid_threads.csv']
        hash_value = compute_file_sha256(filepath)
        
        assert len(hash_value) == 64  # SHA256 hex string length
        assert all(c in '0123456789abcdef' for c in hash_value)

    def test_compute_file_sha256_content_change(self, temp_artifact_files):
        """Test that changing file content changes the hash."""
        filepath = temp_artifact_files['files']['valid_threads.csv']
        hash1 = compute_file_sha256(filepath)

        # Modify file content
        with open(filepath, 'w') as f:
            f.write("Modified content\n")

        hash2 = compute_file_sha256(filepath)

        assert hash1 != hash2

    def test_load_recorded_checksums(self, temp_checksums_file):
        """Test loading checksums from a JSON file."""
        checksums = load_recorded_checksums(temp_checksums_file)
        
        assert isinstance(checksums, dict)
        assert "data/processed/valid_threads.csv" in checksums
        assert checksums["data/processed/valid_threads.csv"] == "abc123def456"

    def test_load_recorded_checksums_missing_file(self, tmp_path):
        """Test loading checksums from a non-existent file."""
        missing_file = str(tmp_path / "nonexistent.json")
        
        with pytest.raises(FileNotFoundError):
            load_recorded_checksums(missing_file)

    def test_verify_artifacts_matching(self, temp_checksums_file, temp_artifact_files):
        """Test verification when all artifacts match their recorded checksums."""
        # Create matching checksums
        matching_checksums = {}
        for rel_path, filepath in temp_artifact_files['files'].items():
            matching_checksums[rel_path] = compute_file_sha256(filepath)

        # Write matching checksums
        with open(temp_checksums_file, 'w') as f:
            json.dump(matching_checksums, f)

        # Verify artifacts
        results = verify_artifacts(
            recorded_checksums_file=temp_checksums_file,
        )

        # All should match
        assert results['all_match'] is True
        assert len(results['mismatches']) == 0
        assert len(results['missing']) == 0

    def test_verify_artifacts_mismatch(self, temp_checksums_file, temp_artifact_files):
        """Test verification when some artifacts don't match."""
        # Create mismatched checksums
        mismatched_checksums = {
            "valid_threads.csv": "wrong_hash_1",
            "thread_metrics.csv": "wrong_hash_2",
            "sensitivity_analysis.csv": compute_file_sha256(temp_artifact_files['files']['sensitivity_analysis.csv'])
        }

        # Write mismatched checksums
        with open(temp_checksums_file, 'w') as f:
            json.dump(mismatched_checksums, f)

        # Verify artifacts
        results = verify_artifacts(
            recorded_checksums_file=temp_checksums_file,
        )

        # Should detect mismatches
        assert results['all_match'] is False
        assert len(results['mismatches']) == 2
        assert len(results['missing']) == 0

    def test_verify_artifacts_missing(self, temp_checksums_file, temp_artifact_files):
        """Test verification when some artifacts are missing."""
        # Create checksums for files that don't exist
        missing_checksums = {
            "data/processed/valid_threads.csv": compute_file_sha256(temp_artifact_files['files']['valid_threads.csv']),
            "data/processed/nonexistent_file.csv": "some_hash"
        }

        # Write checksums
        with open(temp_checksums_file, 'w') as f:
            json.dump(missing_checksums, f)

        # Verify artifacts
        results = verify_artifacts(
            recorded_checksums_file=temp_checksums_file,
        )

        # Should detect missing file
        assert results['all_match'] is False
        assert len(results['mismatches']) == 0
        assert len(results['missing']) == 1
        assert "nonexistent_file.csv" in results['missing'][0]['path']

    def test_generate_report(self, temp_checksums_file, temp_artifact_files):
        """Test report generation for verification results."""
        # Create matching checksums
        matching_checksums = {}
        for rel_path, filepath in temp_artifact_files['files'].items():
            matching_checksums[rel_path] = compute_file_sha256(filepath)

        with open(temp_checksums_file, 'w') as f:
            json.dump(matching_checksums, f)

        # Generate report
        report = generate_report(
            recorded_checksums_file=temp_checksums_file,
        )

        assert 'status' in report
        assert 'timestamp' in report
        assert 'summary' in report
        assert report['status'] == 'PASS'

    def test_main_function(self, temp_checksums_file, temp_artifact_files, caplog):
        """Test the main function execution."""
        # Create matching checksums
        matching_checksums = {}
        for rel_path, filepath in temp_artifact_files['files'].items():
            matching_checksums[rel_path] = compute_file_sha256(filepath)

        with open(temp_checksums_file, 'w') as f:
            json.dump(matching_checksums, f)

        # Run main
        result = main(recorded_checksums_file=temp_checksums_file)

        assert result['status'] == 'PASS'
        assert result['all_match'] is True

    def test_main_function_with_mismatch(self, temp_checksums_file, temp_artifact_files, caplog):
        """Test main function when artifacts don't match."""
        # Create mismatched checksums
        mismatched_checksums = {
            "valid_threads.csv": "wrong_hash",
            "thread_metrics.csv": "wrong_hash2",
            "sensitivity_analysis.csv": compute_file_sha256(temp_artifact_files['files']['sensitivity_analysis.csv'])
        }

        with open(temp_checksums_file, 'w') as f:
            json.dump(mismatched_checksums, f)

        # Run main
        result = main(recorded_checksums_file=temp_checksums_file)

        assert result['status'] == 'FAIL'
        assert result['all_match'] is False

    def test_verify_artifacts_with_config_paths(self, temp_checksums_file, temp_artifact_files, mocker):
        """Test verification using actual project paths from config."""
        # Mock the config to return our temp directory
        mock_paths = MagicMock()
        mock_paths.PROCESSED_DATA_DIR = str(Path(temp_artifact_files['path']) / "data" / "processed")

        # Create matching checksums with correct relative paths
        matching_checksums = {
            "valid_threads.csv": compute_file_sha256(temp_artifact_files['files']['valid_threads.csv']),
            "thread_metrics.csv": compute_file_sha256(temp_artifact_files['files']['thread_metrics.csv']),
            "sensitivity_analysis.csv": compute_file_sha256(temp_artifact_files['files']['sensitivity_analysis.csv'])
        }

        with open(temp_checksums_file, 'w') as f:
            json.dump(matching_checksums, f)

        # Verify artifacts
        results = verify_artifacts(
            recorded_checksums_file=temp_checksums_file,
        )

        assert results['all_match'] is True
        assert len(results['mismatches']) == 0
        assert len(results['missing']) == 0

# Integration test for the full reproducibility workflow
@pytest.mark.integration
def test_full_reproducibility_workflow(tmp_path):
    """
    Integration test: Simulate the full reproducibility verification workflow.
    
    This test:
    1. Creates sample artifacts
    2. Records their checksums
    3. Modifies one artifact
    4. Verifies that the modification is detected
    """
    # Setup directories
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    checksums_file = tmp_path / "checksums.json"

    # Create sample artifacts
    artifacts = {
        "valid_threads.csv": processed_dir / "valid_threads.csv",
        "thread_metrics.csv": processed_dir / "thread_metrics.csv",
        "sensitivity_analysis.csv": processed_dir / "sensitivity_analysis.csv"
    }

    for filename, filepath in artifacts.items():
        with open(filepath, 'w') as f:
            f.write(f"Original content for {filename}\n")

    # Record checksums
    recorded_checksums = {}
    for rel_path, filepath in artifacts.items():
        recorded_checksums[rel_path] = compute_file_sha256(filepath)

    with open(checksums_file, 'w') as f:
        json.dump(recorded_checksums, f)

    # Modify one artifact
    with open(artifacts['valid_threads.csv'], 'w') as f:
        f.write("Modified content\n")

    # Verify artifacts
    results = verify_artifacts(
        recorded_checksums_file=str(checksums_file),
    )

    # Check results
    assert results['all_match'] is False
    assert len(results['mismatches']) == 1
    assert results['mismatches'][0]['path'] == 'valid_threads.csv'
    assert results['mismatches'][0]['expected'] == recorded_checksums['valid_threads.csv']
    assert results['mismatches'][0]['actual'] != recorded_checksums['valid_threads.csv']

    # Generate and verify report
    report = generate_report(
        recorded_checksums_file=str(checksums_file),
    )

    assert report['status'] == 'FAIL'
    assert '1 artifact mismatch' in report['summary']