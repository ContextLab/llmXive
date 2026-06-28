"""
Unit tests for checksum_visualizations.py

Tests checksum computation for visualization outputs.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from checksum_visualizations import (
    find_visualization_outputs,
    compute_visualization_checksums,
    record_visualization_checksums,
)


class TestFindVisualizationOutputs:
    """Tests for find_visualization_outputs function"""

    def test_empty_directory(self, tmp_path):
        """Test with empty figures directory"""
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()

        result = find_visualization_outputs(figures_dir)
        assert result == []

    def test_finds_png_files(self, tmp_path):
        """Test that PNG files are found"""
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()

        # Create test PNG files
        (figures_dir / "scatter_plot.png").write_bytes(b"fake png content")
        (figures_dir / "clone_density_perplexity.png").write_bytes(b"fake png content")

        result = find_visualization_outputs(figures_dir)

        assert len(result) == 2
        assert any("scatter_plot.png" in str(p) for p in result)
        assert any("clone_density_perplexity.png" in str(p) for p in result)

    def test_finds_pdf_files(self, tmp_path):
        """Test that PDF files are found"""
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()

        # Create test PDF files
        (figures_dir / "sensitivity_analysis.pdf").write_bytes(b"fake pdf content")

        result = find_visualization_outputs(figures_dir)

        assert len(result) == 1
        assert "sensitivity_analysis.pdf" in str(result[0])

    def test_nonexistent_directory(self, tmp_path):
        """Test with non-existent directory"""
        figures_dir = tmp_path / "nonexistent" / "figures"

        result = find_visualization_outputs(figures_dir)
        assert result == []


class TestComputeVisualizationChecksums:
    """Tests for compute_visualization_checksums function"""

    def test_computes_checksums(self, tmp_path):
        """Test that checksums are computed for files"""
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()

        # Create test file with known content
        test_file = figures_dir / "test.png"
        test_content = b"test content for checksum"
        test_file.write_bytes(test_content)

        checksums = compute_visualization_checksums(figures_dir)

        assert len(checksums) == 1
        assert checksums[0][0].endswith("figures/test.png")
        assert len(checksums[0][1]) == 64  # SHA-256 hex string

    def test_empty_directory(self, tmp_path):
        """Test with empty directory"""
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()

        checksums = compute_visualization_checksums(figures_dir)
        assert checksums == []

    def test_handles_multiple_files(self, tmp_path):
        """Test with multiple files"""
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()

        # Create multiple test files
        (figures_dir / "file1.png").write_bytes(b"content1")
        (figures_dir / "file2.png").write_bytes(b"content2")
        (figures_dir / "file3.pdf").write_bytes(b"content3")

        checksums = compute_visualization_checksums(figures_dir)

        assert len(checksums) == 3
        # Verify all checksums are different (different content)
        checksum_values = [c[1] for c in checksums]
        assert len(set(checksum_values)) == 3


class TestRecordVisualizationChecksums:
    """Tests for record_visualization_checksums function"""

    def test_records_in_manifest(self, tmp_path):
        """Test that checksums are recorded in manifest"""
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()

        # Create test file
        (figures_dir / "test.png").write_bytes(b"test content")

        manifest_path = tmp_path / "artifact_hashes.json"

        # Create initial manifest
        initial_manifest = {
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00Z",
            "artifact_hashes": {},
        }
        with open(manifest_path, "w") as f:
            json.dump(initial_manifest, f)

        success = record_visualization_checksums(
            figures_dir,
            manifest_path,
            "sha256",
        )

        assert success is True
        assert manifest_path.exists()

        # Verify manifest was updated
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        assert "visualizations" in manifest["artifact_hashes"]
        assert "artifacts" in manifest["artifact_hashes"]["visualizations"]

    def test_creates_manifest_if_missing(self, tmp_path):
        """Test that manifest is created if it doesn't exist"""
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()

        # Create test file
        (figures_dir / "test.png").write_bytes(b"test content")

        manifest_path = tmp_path / "artifact_hashes.json"

        # Don't create manifest first
        success = record_visualization_checksums(
            figures_dir,
            manifest_path,
            "sha256",
        )

        assert success is True
        assert manifest_path.exists()

    def test_empty_directory_returns_false(self, tmp_path):
        """Test that empty directory returns False"""
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()

        manifest_path = tmp_path / "artifact_hashes.json"

        success = record_visualization_checksums(
            figures_dir,
            manifest_path,
            "sha256",
        )

        # Should return False since no files to checksum
        assert success is False
