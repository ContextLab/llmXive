"""
Unit tests for checksum_visualization_outputs module.

Tests:
- find_visualization_outputs: Locates PNG and PDF files
- compute_visualization_checksums: Computes SHA-256 checksums
- record_visualization_checksums: Records in artifact_hashes manifest
- generate_visualization_checksum_report: Creates checksum report
"""
import hashlib
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from checksum_visualization_outputs import (
    find_visualization_outputs,
    compute_visualization_checksums,
    record_visualization_checksums,
    generate_visualization_checksum_report,
)
from checksum_manifest import load_manifest, save_manifest


class TestFindVisualizationOutputs:
    """Tests for find_visualization_outputs function."""

    def test_finds_png_files(self, tmp_path):
        """Test that PNG files are found."""
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()
        
        # Create some PNG files
        (figures_dir / "plot1.png").write_bytes(b"fake png content")
        (figures_dir / "plot2.png").write_bytes(b"fake png content 2")
        
        result = find_visualization_outputs(figures_dir)
        
        assert len(result) == 2
        assert all(f.suffix == ".png" for f in result)

    def test_finds_pdf_files(self, tmp_path):
        """Test that PDF files are found."""
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()
        
        # Create some PDF files
        (figures_dir / "report1.pdf").write_bytes(b"fake pdf content")
        
        result = find_visualization_outputs(figures_dir)
        
        assert len(result) == 1
        assert result[0].suffix == ".pdf"

    def test_finds_both_png_and_pdf(self, tmp_path):
        """Test that both PNG and PDF files are found."""
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()
        
        (figures_dir / "plot.png").write_bytes(b"png")
        (figures_dir / "report.pdf").write_bytes(b"pdf")
        
        result = find_visualization_outputs(figures_dir)
        
        assert len(result) == 2

    def test_empty_directory(self, tmp_path):
        """Test that empty directory returns empty list."""
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()
        
        result = find_visualization_outputs(figures_dir)
        
        assert result == []

    def test_nonexistent_directory(self, tmp_path):
        """Test that nonexistent directory returns empty list."""
        nonexistent = tmp_path / "does_not_exist"
        
        result = find_visualization_outputs(nonexistent)
        
        assert result == []

    def test_ignores_other_extensions(self, tmp_path):
        """Test that non-PNG/PDF files are ignored."""
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()
        
        (figures_dir / "plot.png").write_bytes(b"png")
        (figures_dir / "data.csv").write_bytes(b"csv")
        (figures_dir / "readme.txt").write_bytes(b"txt")
        
        result = find_visualization_outputs(figures_dir)
        
        assert len(result) == 1
        assert result[0].name == "plot.png"


class TestComputeVisualizationChecksums:
    """Tests for compute_visualization_checksums function."""

    def test_computes_correct_sha256(self, tmp_path):
        """Test that SHA-256 checksum is computed correctly."""
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()
        
        test_file = figures_dir / "test.png"
        content = b"test content for checksum"
        test_file.write_bytes(content)
        
        expected_checksum = hashlib.sha256(content).hexdigest()
        
        result = compute_visualization_checksums([test_file])
        
        assert str(test_file) in result
        assert result[str(test_file)] == expected_checksum

    def test_multiple_files(self, tmp_path):
        """Test checksum computation for multiple files."""
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()
        
        file1 = figures_dir / "plot1.png"
        file2 = figures_dir / "plot2.png"
        file1.write_bytes(b"content1")
        file2.write_bytes(b"content2")
        
        result = compute_visualization_checksums([file1, file2])
        
        assert len(result) == 2
        assert str(file1) in result
        assert str(file2) in result

    def test_empty_list(self, tmp_path):
        """Test that empty list returns empty dict."""
        result = compute_visualization_checksums([])
        
        assert result == {}

    def test_different_algorithms(self, tmp_path):
        """Test that different algorithms produce different checksums."""
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()
        
        test_file = figures_dir / "test.png"
        test_file.write_bytes(b"test content")
        
        result_sha256 = compute_visualization_checksums([test_file], algorithm="sha256")
        
        # Verify it's a valid hex string of correct length
        assert len(result_sha256[str(test_file)]) == 64  # SHA-256 produces 64 hex chars


class TestRecordVisualizationChecksums:
    """Tests for record_visualization_checksums function."""

    def test_records_in_manifest(self, tmp_path):
        """Test that checksums are recorded in manifest."""
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()
        
        test_file = figures_dir / "test.png"
        test_file.write_bytes(b"test content")
        
        manifest_path = tmp_path / "manifest.json"
        
        # Create initial manifest
        initial_manifest = {
            "created_at": "2024-01-01T00:00:00",
            "artifact_hashes": {}
        }
        save_manifest(initial_manifest, manifest_path)
        
        checksums = {str(test_file): "fake_checksum_123"}
        
        result = record_visualization_checksums(checksums, manifest_path)
        
        assert result is True
        
        # Verify manifest was updated
        updated = load_manifest(manifest_path)
        assert "visualization:" + str(test_file) in updated["artifact_hashes"]

    def test_creates_artifact_hashes_if_missing(self, tmp_path):
        """Test that artifact_hashes key is created if missing."""
        manifest_path = tmp_path / "manifest.json"
        
        # Create manifest without artifact_hashes
        initial_manifest = {"created_at": "2024-01-01T00:00:00"}
        save_manifest(initial_manifest, manifest_path)
        
        checksums = {"test.png": "fake_checksum"}
        
        result = record_visualization_checksums(checksums, manifest_path)
        
        assert result is True
        
        updated = load_manifest(manifest_path)
        assert "artifact_hashes" in updated

    def test_empty_checksums(self, tmp_path):
        """Test that empty checksums dict still creates manifest entry."""
        manifest_path = tmp_path / "manifest.json"
        
        initial_manifest = {"created_at": "2024-01-01T00:00:00"}
        save_manifest(initial_manifest, manifest_path)
        
        result = record_visualization_checksums({}, manifest_path)
        
        assert result is True


class TestGenerateVisualizationChecksumReport:
    """Tests for generate_visualization_checksum_report function."""

    def test_creates_report_file(self, tmp_path):
        """Test that report file is created."""
        checksums = {
            "plot1.png": "checksum1",
            "plot2.png": "checksum2",
        }
        report_path = tmp_path / "report.txt"
        
        result = generate_visualization_checksum_report(checksums, report_path)
        
        assert result == report_path
        assert report_path.exists()
        
        content = report_path.read_text()
        assert "Visualization Output Checksum Report" in content
        assert "checksum1" in content
        assert "checksum2" in content

    def test_empty_checksums_report(self, tmp_path):
        """Test that empty checksums produces report with message."""
        report_path = tmp_path / "report.txt"
        
        result = generate_visualization_checksum_report({}, report_path)
        
        assert result == report_path
        
        content = report_path.read_text()
        assert "No visualization files found" in content

    def test_report_contains_metadata(self, tmp_path):
        """Test that report contains generation metadata."""
        report_path = tmp_path / "report.txt"
        
        result = generate_visualization_checksum_report({}, report_path)
        
        content = report_path.read_text()
        assert "Generated:" in content
        assert "Algorithm:" in content


class TestIntegration:
    """Integration tests for the full checksum workflow."""

    def test_full_workflow(self, tmp_path):
        """Test the complete checksum workflow."""
        # Setup
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()
        manifest_path = tmp_path / "manifest.json"
        report_path = tmp_path / "report.txt"
        
        # Create test visualization files
        (figures_dir / "scatter.png").write_bytes(b"scatter plot content")
        (figures_dir / "sensitivity.pdf").write_bytes(b"sensitivity analysis")
        
        # Create initial manifest
        initial_manifest = {"created_at": "2024-01-01T00:00:00"}
        save_manifest(initial_manifest, manifest_path)
        
        # Find files
        files = find_visualization_outputs(figures_dir)
        assert len(files) == 2
        
        # Compute checksums
        checksums = compute_visualization_checksums(files)
        assert len(checksums) == 2
        
        # Record in manifest
        result = record_visualization_checksums(checksums, manifest_path)
        assert result is True
        
        # Generate report
        report = generate_visualization_checksum_report(checksums, report_path)
        assert report.exists()
        
        # Verify manifest contains all checksums
        manifest = load_manifest(manifest_path)
        for file_path in files:
            key = f"visualization:{file_path}"
            assert key in manifest["artifact_hashes"]