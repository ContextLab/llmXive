import os
import tempfile
import hashlib
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

import pytest

# Assuming the module is importable
from generate_ingested_cohort import calculate_file_checksum, main


class TestCalculateFileChecksum:
    def test_calculate_file_checksum(self, tmp_path):
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = calculate_file_checksum(test_file)

        assert actual_hash == expected_hash

    def test_calculate_file_checksum_empty(self, tmp_path):
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")

        expected_hash = hashlib.sha256(b"").hexdigest()
        actual_hash = calculate_file_checksum(test_file)

        assert actual_hash == expected_hash


class TestMain:
    @patch('generate_ingested_cohort.ingestion_main')
    @patch('generate_ingested_cohort.register_file')
    @patch('generate_ingested_cohort.save_state')
    @patch('generate_ingested_cohort.load_state')
    @patch('generate_ingested_cohort.get_project_root')
    @patch('generate_ingested_cohort.get_config_dict')
    def test_main_success(
        self,
        mock_get_config,
        mock_get_root,
        mock_load_state,
        mock_save_state,
        mock_register_file,
        mock_ingestion_main,
        tmp_path
    ):
        # Setup mocks
        mock_root = tmp_path
        mock_get_root.return_value = mock_root
        mock_get_config.return_value = {}
        
        # Mock state
        mock_state = {"files": {}}
        mock_load_state.return_value = mock_state

        # Mock ingestion result
        mock_df = pd.DataFrame({"track_id": [1, 2], "score": [0.5, 0.8]})
        mock_ingestion_main.return_value = mock_df

        # Run main
        result = main()

        # Assertions
        assert result == 0
        mock_ingestion_main.assert_called_once()
        mock_register_file.assert_called_once()
        mock_save_state.assert_called_once()
        
        # Verify file exists
        output_path = mock_root / "data" / "processed" / "ingested_cohort.parquet"
        assert output_path.exists()

    @patch('generate_ingested_cohort.ingestion_main')
    @patch('generate_ingested_cohort.register_file')
    @patch('generate_ingested_cohort.save_state')
    @patch('generate_ingested_cohort.load_state')
    @patch('generate_ingested_cohort.get_project_root')
    @patch('generate_ingested_cohort.get_config_dict')
    def test_main_empty_result(
        self,
        mock_get_config,
        mock_get_root,
        mock_load_state,
        mock_save_state,
        mock_register_file,
        mock_ingestion_main,
        tmp_path
    ):
        # Setup mocks
        mock_root = tmp_path
        mock_get_root.return_value = mock_root
        mock_get_config.return_value = {}
        
        # Mock state
        mock_state = {"files": {}}
        mock_load_state.return_value = mock_state

        # Mock ingestion result (empty)
        mock_df = pd.DataFrame()
        mock_ingestion_main.return_value = mock_df

        # Run main
        result = main()

        # Assertions
        assert result == 0
        output_path = mock_root / "data" / "processed" / "ingested_cohort.parquet"
        assert output_path.exists()
        # Verify it's a valid parquet file even if empty
        loaded_df = pd.read_parquet(output_path)
        assert loaded_df.empty