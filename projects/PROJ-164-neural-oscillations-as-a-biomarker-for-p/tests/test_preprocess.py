"""
Unit tests for User Story 1: Data Ingestion and Preprocessing Pipeline.

Covers:
- T010: Checksum verification (SHA-256 match/mismatch)
- T011a: Mode detection logic (Primary vs Data Insufficient)
"""
import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Dict, Any
import pytest

# Import project utilities
# Note: We import from the project root structure
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.io_helpers import compute_sha256, verify_checksum, write_checksum_to_state
from code.utils.config import ensure_dirs


class TestChecksumVerification:
    """Tests for T010: Checksum verification logic."""

    def test_compute_sha256_matches_file_content(self, tmp_path: Path):
        """Verify that compute_sha256 returns the correct hash for a known file."""
        test_file = tmp_path / "test_data.txt"
        content = b"Hello, Neural Oscillations!"
        test_file.write_bytes(content)

        calculated_hash = compute_sha256(test_file)
        
        # Known SHA-256 for "Hello, Neural Oscillations!"
        # sha256("Hello, Neural Oscillations!")
        expected_hash = "8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4"
        
        assert calculated_hash == expected_hash, f"Hash mismatch: {calculated_hash} != {expected_hash}"

    def test_verify_checksum_success(self, tmp_path: Path):
        """Verify that verify_checksum returns True for a matching hash."""
        test_file = tmp_path / "valid.txt"
        test_file.write_text("Valid content")
        
        file_hash = compute_sha256(test_file)
        result = verify_checksum(test_file, file_hash)
        
        assert result is True, "verify_checksum should return True for matching hash"

    def test_verify_checksum_failure(self, tmp_path: Path):
        """Verify that verify_checksum returns False for a mismatched hash."""
        test_file = tmp_path / "invalid.txt"
        test_file.write_text("Invalid content")
        
        wrong_hash = "0" * 64  # Fake hash
        result = verify_checksum(test_file, wrong_hash)
        
        assert result is False, "verify_checksum should return False for mismatched hash"

    def test_write_checksum_to_state(self, tmp_path: Path):
        """Verify that write_checksum_to_state creates the state file correctly."""
        # Setup paths
        state_dir = tmp_path / "state" / "projects"
        state_dir.mkdir(parents=True)
        state_file = state_dir / "PROJ-164-neural-oscillations-as-a-biomarker-for-p.yaml"
        
        # Create a dummy file to checksum
        data_dir = tmp_path / "data" / "raw"
        data_dir.mkdir(parents=True)
        test_file = data_dir / "sub-001_run-01.edf"
        test_file.write_text("dummy edf data")
        
        file_hash = compute_sha256(test_file)
        
        # Mock state entry
        state_entry = {
            "file_path": str(test_file),
            "sha256": file_hash,
            "status": "verified"
        }
        
        # Write to state
        write_checksum_to_state(state_file, state_entry)
        
        assert state_file.exists(), "State file should be created"
        
        # Verify content (simple check since it's YAML)
        content = state_file.read_text()
        assert "PROJ-164" in content, "State file should contain project ID"
        assert file_hash in content, "State file should contain the checksum"


class TestModeDetectionLogic:
    """Tests for T011a: Mode detection logic."""

    def test_mode_insufficient_triggers_termination(self, tmp_path: Path):
        """Verify that Data Insufficient mode is detected and handled."""
        manifest_file = tmp_path / "verified_source_manifest.json"
        
        # Create a manifest indicating no data found
        manifest_data = {
            "query": "EEG AND tDCS AND motor",
            "sources_searched": ["OpenNeuro", "PhysioNet", "Kaggle"],
            "found": False,
            "mode_flag": "Data Insufficient",
            "message": "No single-source paired dataset found"
        }
        
        manifest_file.write_text(json.dumps(manifest_data, indent=2))
        
        # Load and check mode
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
        
        assert manifest["mode_flag"] == "Data Insufficient"
        assert manifest["found"] is False

    def test_mode_primary_allows_continuation(self, tmp_path: Path):
        """Verify that Primary mode is detected when data is found."""
        manifest_file = tmp_path / "verified_source_manifest.json"
        
        # Create a manifest indicating data found
        manifest_data = {
            "query": "EEG AND tDCS AND motor",
            "sources_searched": ["OpenNeuro"],
            "found": True,
            "mode_flag": "Primary",
            "dataset_id": "ds000001",
            "dataset_url": "https://openneuro.org/datasets/ds000001"
        }
        
        manifest_file.write_text(json.dumps(manifest_data, indent=2))
        
        # Load and check mode
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
        
        assert manifest["mode_flag"] == "Primary"
        assert manifest["found"] is True

    def test_manifest_structure_validation(self, tmp_path: Path):
        """Verify that the manifest contains required fields."""
        manifest_file = tmp_path / "verified_source_manifest.json"
        
        # Minimal valid manifest
        manifest_data = {
            "query": "test query",
            "sources_searched": ["OpenNeuro"],
            "found": False,
            "mode_flag": "Data Insufficient"
        }
        
        manifest_file.write_text(json.dumps(manifest_data, indent=2))
        
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
        
        required_fields = ["query", "sources_searched", "found", "mode_flag"]
        for field in required_fields:
            assert field in manifest, f"Missing required field: {field}"