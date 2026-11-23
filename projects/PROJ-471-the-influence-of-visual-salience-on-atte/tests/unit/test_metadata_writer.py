"""
Unit tests for code/ingestion/metadata_writer.py
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
# We need to ensure the imports resolve correctly in the test environment
from ingestion.metadata_writer import scan_salience_maps_directory, write_metadata_file, main


class TestScanSalienceMapsDirectory:
    def test_scans_correct_directory(self, tmp_path):
        """Test that the function finds .npy files in the provided directory."""
        # Create dummy .npy files
        (tmp_path / "img_001.npy").touch()
        (tmp_path / "img_002.npy").touch()
        (tmp_path / "ignore.txt").touch() # Should be ignored

        entries = scan_salience_maps_directory(tmp_path)

        assert len(entries) == 2
        stimulus_ids = [e["stimulus_id"] for e in entries]
        assert "img_001" in stimulus_ids
        assert "img_002" in stimulus_ids

    def test_handles_empty_directory(self, tmp_path):
        """Test behavior when no .npy files exist."""
        entries = scan_salience_maps_directory(tmp_path)
        assert entries == []

    def test_handles_nonexistent_directory(self):
        """Test behavior when directory does not exist."""
        entries = scan_salience_maps_directory(Path("/nonexistent/path"))
        assert entries == []


class TestWriteMetadataFile:
    def test_writes_valid_json(self, tmp_path):
        """Test that the function writes a valid JSON file."""
        entries = [
            {"stimulus_id": "img_001", "map_path": "salience_maps/img_001.npy", "status": "generated"},
            {"stimulus_id": "img_002", "map_path": "salience_maps/img_002.npy", "status": "generated"}
        ]
        output_file = tmp_path / "metadata.json"

        write_metadata_file(entries, output_file)

        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            data = json.load(f)

        assert data["total_maps"] == 2
        assert len(data["maps"]) == 2
        assert "version" in data
        assert "description" in data

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        entries = []
        nested_path = tmp_path / "deep" / "nested" / "dir" / "metadata.json"

        write_metadata_file(entries, nested_path)

        assert nested_path.exists()


class TestMain:
    @patch('ingestion.metadata_writer.get_paths')
    @patch('ingestion.metadata_writer.load_config')
    @patch('ingestion.metadata_writer.scan_salience_maps_directory')
    @patch('ingestion.metadata_writer.write_metadata_file')
    def test_main_executes_flow(self, mock_write, mock_scan, mock_load_config, mock_get_paths, tmp_path):
        """Test that main() orchestrates the scan and write correctly."""
        # Setup mocks
        mock_config = MagicMock()
        mock_paths = MagicMock()
        mock_paths.processed = tmp_path / "processed"
        mock_paths.processed.mkdir(parents=True, exist_ok=True)
        
        # Create a dummy salience_maps directory
        salience_dir = mock_paths.processed / "salience_maps"
        salience_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a dummy .npy file in the mock directory
        (salience_dir / "test_img.npy").touch()

        mock_load_config.return_value = mock_config
        mock_get_paths.return_value = mock_paths
        mock_scan.return_value = [{"stimulus_id": "test_img", "map_path": "test.npy", "status": "generated"}]

        # Run main
        main()

        # Verify interactions
        mock_get_paths.assert_called_once()
        mock_scan.assert_called_once() # Called with the correct path
        mock_write.assert_called_once()
        
        # Verify the file was actually written to the correct location
        expected_output = salience_dir / "metadata.json"
        assert expected_output.exists()