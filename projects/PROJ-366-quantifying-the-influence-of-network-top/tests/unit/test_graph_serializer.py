"""
Unit tests for graph serialization (T015a).

Verifies that graphs are correctly serialized to pickle files
and that the output conforms to expectations.
"""
import os
import json
import pickle
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from ingest.graph_serializer import (
    calculate_checksum,
    serialize_graph,
    serialize_directory_graphs,
    save_checksum_manifest
)
from config import get_config, get_paths


class TestChecksum:
    """Tests for checksum calculation."""

    def test_calculate_checksum_consistency(self, tmp_path):
        """Checksum of same file should be identical."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        checksum1 = calculate_checksum(test_file)
        checksum2 = calculate_checksum(test_file)
        
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA-256 hex length

    def test_calculate_checksum_uniqueness(self, tmp_path):
        """Different files should have different checksums."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content A")
        file2.write_text("Content B")
        
        checksum1 = calculate_checksum(file1)
        checksum2 = calculate_checksum(file2)
        
        assert checksum1 != checksum2


class TestGraphSerialization:
    """Tests for graph serialization logic."""

    def test_serialize_graph_creates_file(self, tmp_path):
        """Serialization should create a valid pickle file."""
        graph_data = {
            "nodes": [{"id": 0, "coords": [0.0, 0.0, 0.0], "degree": 4}],
            "edges": [[0, 1]],
            "metadata": {"sample_id": "test"}
        }
        output_path = tmp_path / "graph_test.pkl"
        
        checksum = serialize_graph(graph_data, output_path)
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        assert len(checksum) == 64

    def test_serialize_graph_loadable(self, tmp_path):
        """Serialized graph should be loadable and match original."""
        original_data = {
            "nodes": [
                {"id": 0, "coords": [1.0, 2.0, 3.0], "degree": 4, "clustering": 0.5},
                {"id": 1, "coords": [4.0, 5.0, 6.0], "degree": 3, "clustering": 0.0}
            ],
            "edges": [[0, 1]],
            "metadata": {"cutoff": 3.0}
        }
        output_path = tmp_path / "graph_loadable.pkl"
        
        serialize_graph(original_data, output_path)
        
        with open(output_path, 'rb') as f:
            loaded_data = pickle.load(f)
            
        assert loaded_data == original_data
        assert len(loaded_data['nodes']) == 2
        assert len(loaded_data['edges']) == 1


class TestDirectorySerialization:
    """Tests for batch directory serialization."""

    @patch('ingest.graph_serializer.build_graph_from_xyz')
    @patch('ingest.graph_serializer.get_paths')
    @patch('ingest.graph_serializer.get_config')
    def test_serialize_directory_graphs_integration(
        self, mock_config, mock_paths, mock_builder, tmp_path
    ):
        """
        Verify end-to-end serialization of multiple samples.
        
        This test mocks the graph builder to avoid needing real LAMMPS/ASE
        dependencies while verifying the file I/O and structure.
        """
        # Setup paths
        raw_dir = tmp_path / "raw"
        proc_dir = tmp_path / "processed"
        raw_dir.mkdir()
        
        # Create fake XYZ files
        sample_ids = ["01", "02"]
        for sid in sample_ids:
            xyz_file = raw_dir / f"sample_{sid}.xyz"
            xyz_file.write_text(f"2\nSample {sid}\nSi 0.0 0.0 0.0\nSi 1.0 1.0 1.0\n")
        
        # Mock configuration
        mock_paths.return_value = {
            'raw_data': raw_dir,
            'processed_graphs': proc_dir,
            'root': tmp_path / 'data'
        }
        mock_config.return_value = {'graph_builder': {'cutoff': 3.0}}
        
        # Mock graph builder to return valid structure
        mock_builder.return_value = {
            "nodes": [
                {"id": 0, "coords": [0.0, 0.0, 0.0], "degree": 1, "clustering": 0.0},
                {"id": 1, "coords": [1.0, 1.0, 1.0], "degree": 1, "clustering": 0.0}
            ],
            "edges": [[0, 1]],
            "metadata": {"source": "mock"}
        }
        
        # Run serialization
        results = serialize_directory_graphs()
        
        # Verify outputs
        assert len(results) == 2
        for sid in sample_ids:
            assert sid in results
            file_path = Path(results[sid]['file'])
            assert file_path.exists()
            assert file_path.suffix == '.pkl'
            assert results[sid]['nodes'] == 2
            assert results[sid]['edges'] == 1

    def test_serialize_directory_graphs_no_files(self, tmp_path):
        """Should raise error if no XYZ files found."""
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        
        with pytest.raises(FileNotFoundError):
            serialize_directory_graphs(raw_dir=raw_dir, output_dir=tmp_path / "out")

    def test_save_checksum_manifest(self, tmp_path):
        """Verify manifest JSON structure."""
        results = {
            "01": {
                "file": "graph_01.pkl",
                "checksum": "abc123...",
                "nodes": 100,
                "edges": 200
            }
        }
        manifest_path = tmp_path / "checksums.json"
        
        save_checksum_manifest(results, manifest_path)
        
        assert manifest_path.exists()
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            
        assert "01" in manifest
        assert "checksum" in manifest["01"]
        assert "file" in manifest["01"]
        assert "nodes" in manifest["01"]
        assert "edges" in manifest["01"]
