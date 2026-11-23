"""
Unit tests for T082: Audit Data Integrity
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from src.evaluation.audit_data_integrity import (
    check_file_for_synthetic_markers,
    verify_real_data_source,
    audit_directory,
    load_data_sources
)

class TestAuditDataIntegrity:
    def test_check_file_for_synthetic_markers_filename(self, tmp_path):
        """Test detection of synthetic markers in filename."""
        fake_file = tmp_path / "dummy_adapter.safetensors"
        fake_file.touch()
        result = check_file_for_synthetic_markers(fake_file)
        assert result is not None
        assert "synthetic marker" in result

    def test_check_file_for_synthetic_markers_content(self, tmp_path):
        """Test detection of synthetic markers in file content."""
        fake_file = tmp_path / "real_data.json"
        fake_file.write_text('{"status": "synthetic", "data": []}')
        result = check_file_for_synthetic_markers(fake_file)
        assert result is not None
        assert "synthetic" in result.lower()

    def test_check_file_for_synthetic_markers_clean(self, tmp_path):
        """Test clean file passes."""
        clean_file = tmp_path / "adapter_model.safetensors"
        clean_file.write_bytes(b"\x00\x01\x02") # Binary data
        result = check_file_for_synthetic_markers(clean_file)
        assert result is None

    def test_verify_real_data_source_safetensors(self, tmp_path):
        """Test verification of a valid safetensors file."""
        real_file = tmp_path / "adapter_model.safetensors"
        real_file.touch()
        result = verify_real_data_source(real_file, {})
        assert result is True

    def test_verify_real_data_source_unknown_ext(self, tmp_path):
        """Test verification of an unknown extension."""
        unknown_file = tmp_path / "unknown.xyz"
        unknown_file.touch()
        result = verify_real_data_source(unknown_file, {})
        assert result is False

    def test_audit_directory_missing(self):
        """Test audit of a non-existent directory."""
        result = audit_directory(Path("/nonexistent/path"), {})
        assert result["status"] == "missing_directory"
        assert "issues" in result

    def test_audit_directory_with_synthetic(self, tmp_path):
        """Test audit detecting synthetic files."""
        synthetic_file = tmp_path / "dummy_weights.npz"
        synthetic_file.touch()
        
        result = audit_directory(tmp_path, {})
        
        assert result["status"] == "complete"
        assert len(result["synthetic_files"]) == 1
        assert "dummy" in result["synthetic_files"][0]["path"]