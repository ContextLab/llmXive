"""
Unit tests for visualization checksum computation (T044).

Tests the checksum_visualization_outputs module to ensure:
1. Visualization files are correctly discovered
2. Checksums are computed correctly
3. Checksums are recorded in the manifest
4. Edge cases are handled properly
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from checksum_visualization_outputs import (
    find_visualization_outputs,
    compute_visualization_checksums,
    record_visualization_checksums,
    generate_visualization_checksum_report,
    VISUALIZATION_DIR,
    VISUALIZATION_EXTENSIONS
)

from checksum_manifest import DEFAULT_ALGORITHM

class TestFindVisualizationOutputs:
    """Tests for find_visualization_outputs function."""
    
    def test_find_in_empty_directory(self, tmp_path):
        """Should return empty list when no visualization files exist."""
        result = find_visualization_outputs(tmp_path)
        assert result == []
    
    def test_find_png_files(self, tmp_path):
        """Should find PNG files in directory."""
        # Create test PNG files
        (tmp_path / "scatter.png").touch()
        (tmp_path / "plot.png").touch()
        
        result = find_visualization_outputs(tmp_path)
        
        assert len(result) == 2
        assert all(f.suffix == '.png' for f in result)
    
    def test_find_multiple_extensions(self, tmp_path):
        """Should find files with multiple supported extensions."""
        (tmp_path / "fig1.png").touch()
        (tmp_path / "fig2.pdf").touch()
        (tmp_path / "fig3.svg").touch()
        (tmp_path / "not_an_image.txt").touch()
        
        result = find_visualization_outputs(tmp_path)
        
        assert len(result) == 3
        assert not any(f.suffix == '.txt' for f in result)
    
    def test_find_in_subdirectories(self, tmp_path):
        """Should find visualization files in subdirectories."""
        sub_dir = tmp_path / "subdir"
        sub_dir.mkdir()
        
        (tmp_path / "root.png").touch()
        (sub_dir / "nested.png").touch()
        
        result = find_visualization_outputs(tmp_path)
        
        assert len(result) == 2
    
    def test_nonexistent_directory(self, tmp_path):
        """Should return empty list for non-existent directory."""
        nonexistent = tmp_path / "does_not_exist"
        result = find_visualization_outputs(nonexistent)
        assert result == []

class TestComputeVisualizationChecksums:
    """Tests for compute_visualization_checksums function."""
    
    def test_compute_checksum_valid_file(self, tmp_path):
        """Should compute valid checksum for existing file."""
        test_file = tmp_path / "test.png"
        test_file.write_bytes(b"fake png content")
        
        checksums = compute_visualization_checksums([test_file])
        
        assert str(test_file) in checksums
        assert len(checksums[str(test_file)]) == 64  # SHA256 hex length
    
    def test_compute_checksum_multiple_files(self, tmp_path):
        """Should compute checksums for multiple files."""
        file1 = tmp_path / "fig1.png"
        file2 = tmp_path / "fig2.png"
        file1.write_bytes(b"content1")
        file2.write_bytes(b"content2")
        
        checksums = compute_visualization_checksums([file1, file2])
        
        assert len(checksums) == 2
    
    def test_different_content_different_checksum(self, tmp_path):
        """Different file content should produce different checksums."""
        file1 = tmp_path / "fig1.png"
        file2 = tmp_path / "fig2.png"
        file1.write_bytes(b"content1")
        file2.write_bytes(b"content2")
        
        checksums = compute_visualization_checksums([file1, file2])
        
        assert checksums[str(file1)] != checksums[str(file2)]
    
    def test_same_content_same_checksum(self, tmp_path):
        """Same file content should produce same checksum."""
        file1 = tmp_path / "fig1.png"
        file2 = tmp_path / "fig2.png"
        file1.write_bytes(b"identical content")
        file2.write_bytes(b"identical content")
        
        checksums = compute_visualization_checksums([file1, file2])
        
        assert checksums[str(file1)] == checksums[str(file2)]
    
    def test_missing_file_skipped(self, tmp_path):
        """Missing files should be skipped with warning."""
        missing_file = tmp_path / "nonexistent.png"
        existing_file = tmp_path / "existing.png"
        existing_file.write_bytes(b"content")
        
        checksums = compute_visualization_checksums([missing_file, existing_file])
        
        # Only existing file should be in results
        assert str(existing_file) in checksums
        assert str(missing_file) not in checksums

class TestRecordVisualizationChecksums:
    """Tests for record_visualization_checksums function."""
    
    def test_record_creates_manifest(self, tmp_path):
        """Should create manifest file if it doesn't exist."""
        manifest_path = tmp_path / "manifest.json"
        viz_dir = tmp_path / "figures"
        viz_dir.mkdir()
        (viz_dir / "test.png").write_bytes(b"content")
        
        record_visualization_checksums(
            manifest_path=manifest_path,
            visualization_dir=viz_dir
        )
        
        assert manifest_path.exists()
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        assert 'artifact_hashes' in manifest
        assert 'metadata' in manifest
    
    def test_record_updates_existing_manifest(self, tmp_path):
        """Should update existing manifest with new checksums."""
        manifest_path = tmp_path / "manifest.json"
        viz_dir = tmp_path / "figures"
        viz_dir.mkdir()
        
        # Create initial manifest
        initial_manifest = {
            'artifact_hashes': {'existing': 'checksum123'},
            'metadata': {'created': '2024-01-01'}
        }
        with open(manifest_path, 'w') as f:
            json.dump(initial_manifest, f)
        
        # Add visualization file
        (viz_dir / "test.png").write_bytes(b"content")
        
        record_visualization_checksums(
            manifest_path=manifest_path,
            visualization_dir=viz_dir
        )
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        # Should preserve existing entries
        assert 'existing' in manifest['artifact_hashes']
        # Should add new visualization
        assert any('test.png' in k for k in manifest['artifact_hashes'].keys())
    
    def test_record_adds_metadata(self, tmp_path):
        """Should add visualization-specific metadata to manifest."""
        manifest_path = tmp_path / "manifest.json"
        viz_dir = tmp_path / "figures"
        viz_dir.mkdir()
        (viz_dir / "test.png").write_bytes(b"content")
        
        record_visualization_checksums(
            manifest_path=manifest_path,
            visualization_dir=viz_dir
        )
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        metadata = manifest.get('metadata', {})
        assert 'last_visualization_check' in metadata
        assert 'visualization_files_checked' in metadata
        assert 'visualization_algorithm' in metadata

class TestGenerateVisualizationChecksumReport:
    """Tests for generate_visualization_checksum_report function."""
    
    def test_report_contains_checksums(self, tmp_path):
        """Report should contain checksum information."""
        manifest_path = tmp_path / "manifest.json"
        output_path = tmp_path / "report.txt"
        
        # Create manifest with checksums
        manifest = {
            'artifact_hashes': {
                'data/analysis/figures/test.png': 'abc123checksum'
            },
            'metadata': {
                'visualization_algorithm': 'sha256'
            }
        }
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f)
        
        report = generate_visualization_checksum_report(
            manifest_path, output_path
        )
        
        assert 'abc123checksum' in report
        assert 'test.png' in report
    
    def test_report_generated_to_file(self, tmp_path):
        """Should write report to specified output file."""
        manifest_path = tmp_path / "manifest.json"
        output_path = tmp_path / "report.txt"
        
        manifest = {
            'artifact_hashes': {},
            'metadata': {}
        }
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f)
        
        generate_visualization_checksum_report(
            manifest_path, output_path
        )
        
        assert output_path.exists()
        with open(output_path) as f:
            content = f.read()
        assert 'VISUALIZATION OUTPUT CHECKSUM REPORT' in content
    
    def test_report_returns_string(self, tmp_path):
        """Should return report as string when no output path."""
        manifest_path = tmp_path / "manifest.json"
        
        manifest = {
            'artifact_hashes': {},
            'metadata': {}
        }
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f)
        
        report = generate_visualization_checksum_report(manifest_path)
        
        assert isinstance(report, str)
        assert len(report) > 0
        assert 'VISUALIZATION OUTPUT CHECKSUM REPORT' in report

class TestVisualizationChecksumIntegration:
    """Integration tests for visualization checksum workflow."""
    
    def test_full_workflow(self, tmp_path):
        """Test complete workflow: find -> compute -> record."""
        manifest_path = tmp_path / "manifest.json"
        viz_dir = tmp_path / "figures"
        viz_dir.mkdir()
        
        # Create test visualization files
        (viz_dir / "scatter.png").write_bytes(b"scatter data")
        (viz_dir / "density_plot.png").write_bytes(b"density data")
        (viz_dir / "sensitivity.pdf").write_bytes(b"sensitivity data")
        
        # Find files
        files = find_visualization_outputs(viz_dir)
        assert len(files) == 3
        
        # Compute checksums
        checksums = compute_visualization_checksums(files)
        assert len(checksums) == 3
        
        # Record in manifest
        record_visualization_checksums(
            manifest_path=manifest_path,
            visualization_dir=viz_dir
        )
        
        # Verify manifest
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        assert len(manifest['artifact_hashes']) == 3
        assert manifest['metadata']['visualization_files_checked'] == 3
    
    def test_no_files_empty_manifest(self, tmp_path):
        """Should handle case where no visualization files exist."""
        manifest_path = tmp_path / "manifest.json"
        viz_dir = tmp_path / "figures"
        viz_dir.mkdir()
        
        record_visualization_checksums(
            manifest_path=manifest_path,
            visualization_dir=viz_dir
        )
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        assert manifest['metadata']['visualization_files_checked'] == 0