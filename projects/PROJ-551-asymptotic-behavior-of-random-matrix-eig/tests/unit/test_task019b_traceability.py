"""
Unit tests for T019b traceability module.

These tests verify that the traceability logic correctly links checksums
to simulation run metadata.
"""

import json
import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone

import pytest

# Add code directory to path for imports
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_dir) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(code_dir))

from analysis.task019b_traceability import (
    load_checksum_manifest,
    load_single_run_results,
    find_checksum_for_run,
    update_run_metadata,
    save_updated_results,
)


class TestLoadChecksumManifest:
    def test_load_valid_manifest(self, tmp_path):
        """Test loading a valid checksum manifest."""
        manifest_data = {
            "matrix_N1000_seed42.npy": {
                "sha256": "abc123def456",
                "timestamp": "2026-01-01T00:00:00Z"
            }
        }

        manifest_file = tmp_path / "checksums_raw.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest_data, f)

        result = load_checksum_manifest(manifest_file)
        assert result == manifest_data

    def test_load_missing_manifest(self, tmp_path):
        """Test that loading a missing manifest raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_checksum_manifest(tmp_path / "nonexistent.json")


class TestLoadSingleRunResults:
    def test_load_valid_results(self, tmp_path):
        """Test loading valid single run results."""
        results_data = {
            "run_id": "run_001",
            "N": 1000,
            "seed": 42,
            "theta": 2.5,
            "eigenvalues": [2.5, 1.2, 0.8],
            "outlier_flag": True
        }

        results_file = tmp_path / "single_run_results.json"
        with open(results_file, 'w') as f:
            json.dump(results_data, f)

        result = load_single_run_results(results_file)
        assert result == results_data

    def test_load_missing_results(self, tmp_path):
        """Test that loading missing results raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_single_run_results(tmp_path / "nonexistent.json")


class TestFindChecksumForRun:
    def test_find_exact_match(self, tmp_path, caplog):
        """Test finding a checksum with exact filename match."""
        manifest = {
            "matrix_N1000_seed42.npy": {
                "sha256": "abc123def456",
                "timestamp": "2026-01-01T00:00:00Z"
            }
        }

        run_metadata = {"N": 1000, "seed": 42, "theta": 2.5}

        # Create a simple logger for testing
        import logging
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.INFO)

        result = find_checksum_for_run(manifest, run_metadata, logger)
        assert result == "abc123def456"

    def test_find_partial_match(self, tmp_path, caplog):
        """Test finding a checksum with partial filename match."""
        manifest = {
            "data/matrix_N1000_seed42.npy": {
                "sha256": "xyz789abc123",
                "timestamp": "2026-01-01T00:00:00Z"
            }
        }

        run_metadata = {"N": 1000, "seed": 42, "theta": 2.5}

        import logging
        logger = logging.getLogger("test_logger_partial")
        logger.setLevel(logging.INFO)

        result = find_checksum_for_run(manifest, run_metadata, logger)
        assert result == "xyz789abc123"

    def test_no_match_found(self, tmp_path, caplog):
        """Test when no matching checksum is found."""
        manifest = {
            "matrix_N500_seed42.npy": {
                "sha256": "abc123",
                "timestamp": "2026-01-01T00:00:00Z"
            }
        }

        run_metadata = {"N": 1000, "seed": 42, "theta": 2.5}

        import logging
        logger = logging.getLogger("test_logger_nomatch")
        logger.setLevel(logging.WARNING)

        result = find_checksum_for_run(manifest, run_metadata, logger)
        assert result is None

    def test_missing_metadata_fields(self, tmp_path, caplog):
        """Test when run metadata is missing N or seed."""
        manifest = {
            "matrix_N1000_seed42.npy": {
                "sha256": "abc123",
                "timestamp": "2026-01-01T00:00:00Z"
            }
        }

        run_metadata = {"N": 1000}  # Missing seed

        import logging
        logger = logging.getLogger("test_logger_missing")
        logger.setLevel(logging.WARNING)

        result = find_checksum_for_run(manifest, run_metadata, logger)
        assert result is None


class TestUpdateRunMetadata:
    def test_update_with_checksum(self):
        """Test updating run metadata with a checksum."""
        run_results = {
            "run_id": "run_001",
            "N": 1000,
            "seed": 42,
            "theta": 2.5,
            "eigenvalues": [2.5, 1.2, 0.8],
            "outlier_flag": True
        }

        checksum_hash = "abc123def456789"

        import logging
        logger = logging.getLogger("test_logger_update")
        logger.setLevel(logging.INFO)

        updated = update_run_metadata(run_results, checksum_hash, logger)

        assert "metadata" in updated
        assert updated["metadata"]["checksum_sha256"] == checksum_hash
        assert "checksum_verified_at" in updated["metadata"]
        assert updated["metadata"]["traceability_status"] == "linked"

    def test_update_preserves_existing_metadata(self):
        """Test that updating preserves existing metadata fields."""
        run_results = {
            "run_id": "run_001",
            "N": 1000,
            "seed": 42,
            "metadata": {
                "original_field": "value"
            }
        }

        checksum_hash = "abc123def456789"

        import logging
        logger = logging.getLogger("test_logger_preserve")
        logger.setLevel(logging.INFO)

        updated = update_run_metadata(run_results, checksum_hash, logger)

        assert updated["metadata"]["original_field"] == "value"
        assert updated["metadata"]["checksum_sha256"] == checksum_hash


class TestSaveUpdatedResults:
    def test_save_results(self, tmp_path):
        """Test saving updated results to a file."""
        updated_results = {
            "run_id": "run_001",
            "N": 1000,
            "metadata": {
                "checksum_sha256": "abc123",
                "traceability_status": "linked"
            }
        }

        output_file = tmp_path / "results_updated.json"

        import logging
        logger = logging.getLogger("test_logger_save")
        logger.setLevel(logging.INFO)

        save_updated_results(updated_results, output_file, logger)

        assert output_file.exists()

        with open(output_file, 'r') as f:
            loaded = json.load(f)

        assert loaded == updated_results

    def test_save_creates_directories(self, tmp_path):
        """Test that saving creates parent directories if needed."""
        updated_results = {"run_id": "run_001"}

        output_file = tmp_path / "subdir1" / "subdir2" / "results.json"

        import logging
        logger = logging.getLogger("test_logger_dirs")
        logger.setLevel(logging.INFO)

        save_updated_results(updated_results, output_file, logger)

        assert output_file.exists()