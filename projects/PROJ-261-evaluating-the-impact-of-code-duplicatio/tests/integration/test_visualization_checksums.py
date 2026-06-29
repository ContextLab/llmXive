"""Integration tests for visualization checksum computation.

These tests verify that visualization outputs are properly checksummed
and recorded in the artifact manifest as required by SC-006 (checksum tracking).

Per Constitution Principle III (Data Hygiene) and V (Versioning Discipline).
"""
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / 'code'
DATA_DIR = PROJECT_ROOT / 'data'

import sys
sys.path.insert(0, str(CODE_DIR))

from checksum_visualization_outputs import (
    find_visualization_outputs,
    compute_visualization_checksums,
    record_visualization_checksums,
    generate_visualization_checksum_report
)
from checksum_manifest import load_manifest, save_manifest
from config import get_checksum_algorithm


class TestVisualizationChecksums:
    """Test suite for visualization checksum computation."""

    @pytest.fixture
    def temp_figures_dir(self, tmp_path):
        """Create a temporary figures directory with test files."""
        figures_dir = tmp_path / 'figures'
        figures_dir.mkdir()
        
        # Create test visualization files
        (figures_dir / 'test_plot.png').write_bytes(b'fake png content')
        (figures_dir / 'test_plot.pdf').write_bytes(b'fake pdf content')
        
        return figures_dir

    @pytest.fixture
    def temp_manifest(self, tmp_path):
        """Create a temporary manifest file."""
        manifest_path = tmp_path / 'checksum_manifest.json'
        manifest = {
            'version': '1.0',
            'created_at': '2024-01-01T00:00:00',
            'artifact_hashes': {}
        }
        save_manifest(manifest_path, manifest)
        return manifest_path

    def test_find_visualization_outputs_png(self, temp_figures_dir):
        """Test finding PNG visualization files."""
        files = find_visualization_outputs(temp_figures_dir, ['.png'])
        assert len(files) == 1
        assert files[0].name == 'test_plot.png'
    
    def test_find_visualization_outputs_pdf(self, temp_figures_dir):
        """Test finding PDF visualization files."""
        files = find_visualization_outputs(temp_figures_dir, ['.pdf'])
        assert len(files) == 1
        assert files[0].name == 'test_plot.pdf'
    
    def test_find_visualization_outputs_all(self, temp_figures_dir):
        """Test finding all visualization files."""
        files = find_visualization_outputs(temp_figures_dir)
        assert len(files) == 2
        names = {f.name for f in files}
        assert 'test_plot.png' in names
        assert 'test_plot.pdf' in names
    
    def test_find_visualization_outputs_empty_dir(self, tmp_path):
        """Test finding files in empty directory."""
        empty_dir = tmp_path / 'empty_figures'
        empty_dir.mkdir()
        
        files = find_visualization_outputs(empty_dir)
        assert len(files) == 0
    
    def test_find_visualization_outputs_nonexistent_dir(self, tmp_path):
        """Test finding files in nonexistent directory."""
        nonexistent = tmp_path / 'does_not_exist'
        
        files = find_visualization_outputs(nonexistent)
        assert len(files) == 0
    
    def test_compute_visualization_checksums(self, temp_figures_dir):
        """Test checksum computation for visualization files."""
        files = find_visualization_outputs(temp_figures_dir)
        checksums = compute_visualization_checksums(files)
        
        assert len(checksums) == 2
        
        # Verify checksums are valid hex strings
        for file_path, checksum in checksums.items():
            assert len(checksum) == 64  # SHA256 hex length
            assert all(c in '0123456789abcdef' for c in checksum)
    
    def test_compute_visualization_checksums_missing_file(self, tmp_path):
        """Test checksum computation with missing file."""
        missing_file = tmp_path / 'missing.png'
        
        checksums = compute_visualization_checksums([missing_file])
        assert len(checksums) == 0  # Missing files should be skipped
    
    def test_record_visualization_checksums(self, temp_figures_dir, temp_manifest):
        """Test recording checksums in manifest."""
        files = find_visualization_outputs(temp_figures_dir)
        checksums = compute_visualization_checksums(files)
        
        success = record_visualization_checksums(checksums, temp_manifest)
        assert success is True
        
        # Verify manifest was updated
        manifest = load_manifest(temp_manifest)
        assert 'visualization_outputs' in manifest['artifact_hashes']
        assert len(manifest['artifact_hashes']['visualization_outputs']) == 2
    
    def test_record_visualization_checksums_creates_category(self, temp_figures_dir, temp_manifest):
        """Test that recording creates the category if it doesn't exist."""
        files = find_visualization_outputs(temp_figures_dir)
        checksums = compute_visualization_checksums(files)
        
        # Ensure category doesn't exist
        manifest = load_manifest(temp_manifest)
        assert 'visualization_outputs' not in manifest.get('artifact_hashes', {})
        
        success = record_visualization_checksums(checksums, temp_manifest)
        assert success is True
        
        manifest = load_manifest(temp_manifest)
        assert 'visualization_outputs' in manifest['artifact_hashes']
    
    def test_generate_visualization_checksum_report(self, temp_figures_dir, tmp_path):
        """Test checksum report generation."""
        files = find_visualization_outputs(temp_figures_dir)
        checksums = compute_visualization_checksums(files)
        
        report_path = tmp_path / 'report.txt'
        report = generate_visualization_checksum_report(checksums, report_path)
        
        assert report_path.exists()
        assert 'Visualization Outputs Checksum Report' in report
        assert 'test_plot.png' in report
        assert 'test_plot.pdf' in report
        assert len(checksums) == 2
    
    def test_generate_visualization_checksum_report_no_output_path(self, temp_figures_dir):
        """Test checksum report generation without output path."""
        files = find_visualization_outputs(temp_figures_dir)
        checksums = compute_visualization_checksums(files)
        
        report = generate_visualization_checksum_report(checksums)
        
        assert 'Visualization Outputs Checksum Report' in report
        assert len(checksums) == 2
    
    def test_checksum_algorithm_from_config(self, temp_figures_dir):
        """Test that the correct checksum algorithm is used from config."""
        algorithm = get_checksum_algorithm()
        
        files = find_visualization_outputs(temp_figures_dir)
        checksums = compute_visualization_checksums(files, algorithm)
        
        assert len(checksums) == 2
        for file_path, checksum in checksums.items():
            assert len(checksum) == 64  # SHA256
    
    def test_manifest_timestamp_format(self, temp_figures_dir, temp_manifest):
        """Test that timestamps in manifest are in ISO format."""
        files = find_visualization_outputs(temp_figures_dir)
        checksums = compute_visualization_checksums(files)
        
        record_visualization_checksums(checksums, temp_manifest)
        
        manifest = load_manifest(temp_manifest)
        for file_path, entry in manifest['artifact_hashes']['visualization_outputs'].items():
            assert 'timestamp' in entry
            assert 'T' in entry['timestamp']  # ISO format has 'T' separator
            assert 'category' in entry
            assert entry['category'] == 'visualization_outputs'

if __name__ == '__main__':
    pytest.main([__file__, '-v'])