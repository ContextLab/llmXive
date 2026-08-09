"""
Unit tests for code/data/loader.py
"""
import os
import tempfile
import yaml
import pytest
from pathlib import Path

# Mocking datasets for unit tests
from unittest.mock import patch, MagicMock
import pyarrow as pa
import pyarrow.parquet as pq

from data.loader import (
    compute_file_checksum,
    load_class_config,
    FilteredAudioDataset,
    FilteredDataLoader
)
from utils.logger import DataLoadError

class TestChecksum:
    def test_compute_file_checksum(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = f.name
        
        try:
            checksum = compute_file_checksum(temp_path)
            assert len(checksum) == 64 # SHA256 hex length
        finally:
            os.unlink(temp_path)

    def test_compute_file_checksum_not_found(self):
        with pytest.raises(DataLoadError):
            compute_file_checksum("/nonexistent/file.txt")

class TestClassConfig:
    def test_load_valid_config(self, tmp_path):
        config_data = {
            "subtle_classes": [0, 1],
            "control_classes": [2, 3]
        }
        config_file = tmp_path / "class_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        subtle, control = load_class_config(str(config_file))
        assert subtle == {0, 1}
        assert control == {2, 3}

    def test_load_missing_keys(self, tmp_path):
        config_data = {"subtle_classes": [0]} # Missing control
        config_file = tmp_path / "class_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        with pytest.raises(DataLoadError):
            load_class_config(str(config_file))

class TestFilteredDataLoader:
    @patch("data.loader.load_dataset")
    def test_run_streaming_and_writes_parquet(self, mock_load_dataset, tmp_path):
        # Setup mock dataset
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=iter([
            {"class_id": 0, "audio": {"bytes": b"fake_audio_data"}, "file_name": "f1.wav", "subset_type": "subtle"},
            {"class_id": 5, "audio": {"bytes": b"fake_audio_data_2"}, "file_name": "f2.wav", "subset_type": "control"}, # 5 not in config
            {"class_id": 1, "audio": {"bytes": b"fake_audio_data_3"}, "file_name": "f3.wav", "subset_type": "subtle"},
        ]))
        mock_load_dataset.return_value = mock_ds

        # Setup config
        config_data = {
            "subtle_classes": [0, 1],
            "control_classes": [5]
        }
        config_file = tmp_path / "class_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        output_file = tmp_path / "subset.parquet"
        state_dir = tmp_path / "state"

        loader = FilteredDataLoader(
            config_path=str(config_file),
            output_path=str(output_file)
        )
        # Override state dir for test
        loader.state_dir = str(state_dir)

        # Run
        result_path = loader.run()

        # Verify output exists
        assert os.path.exists(result_path)
        
        # Verify content
        table = pq.read_table(result_path)
        assert len(table) == 2 # Only 0 and 1 should be kept (5 is control, but wait: 5 is in control_classes)
        # Correction: 0 is subtle, 1 is subtle, 5 is control. All 3 are in allowed_classes.
        # Wait, my mock data:
        # 0 -> subtle (allowed)
        # 5 -> control (allowed)
        # 1 -> subtle (allowed)
        # So 3 rows should be written.
        assert len(table) == 3

        # Verify columns
        assert "class_id" in table.column_names
        assert "subset_type" in table.column_names

        # Verify checksum file created
        assert os.path.exists(os.path.join(state_dir, "subset.parquet.yaml"))