import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.download import check_schema_pass, download_dataset
from config import DataConfig

class TestDownload:
    @pytest.fixture
    def mock_config(self, tmp_path):
        """Create a mock config with temporary directories."""
        config = MagicMock(spec=DataConfig)
        config.raw_data_dir = tmp_path / "raw"
        config.processed_data_dir = tmp_path / "processed"
        config.raw_data_dir.mkdir(parents=True, exist_ok=True)
        config.processed_data_dir.mkdir(parents=True, exist_ok=True)
        return config

    def test_check_schema_pass_missing_file(self, mock_config, tmp_path):
        """Test that check_schema_pass returns False if log is missing."""
        result = check_schema_pass(tmp_path / "nonexistent.log")
        assert result is False

    def test_check_schema_pass_success_marker(self, mock_config, tmp_path):
        """Test that check_schema_pass returns True if success marker is found."""
        log_path = tmp_path / "schema_check.log"
        log_path.write_text("Schema validation passed")
        assert check_schema_pass(log_path) is True

    def test_check_schema_pass_failure_marker(self, mock_config, tmp_path):
        """Test that check_schema_pass returns False if fatal error is found."""
        log_path = tmp_path / "schema_check.log"
        log_path.write_text("FATAL: Missing columns")
        assert check_schema_pass(log_path) is False

    @patch('data.download.load_dataset')
    @patch('data.download.pq.ParquetWriter')
    def test_download_dataset_streaming(self, mock_writer_class, mock_load_dataset, mock_config, tmp_path):
        """Test download_dataset with streaming enabled."""
        # Mock dataset iterator
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=iter([
            {"smiles": "C1=CC=CC=C1", "rate": 1.0},
            {"smiles": "CC(C)Br", "rate": 2.0}
        ]))
        mock_load_dataset.return_value = mock_ds

        # Mock ParquetWriter
        mock_writer = MagicMock()
        mock_writer_class.return_value = mock_writer

        # Call function
        output_path = download_dataset(mock_config, MagicMock())

        # Verify load_dataset called with streaming=True
        mock_load_dataset.assert_called_once()
        call_kwargs = mock_load_dataset.call_args
        assert call_kwargs.kwargs.get('streaming') is True

        # Verify output path
        assert output_path.exists()
        assert "sn1_raw.parquet" in str(output_path)

        # Verify writer was closed
        mock_writer.close.assert_called_once()