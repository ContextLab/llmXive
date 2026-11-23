import os
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# We need to ensure the src path is available
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data.verify_dataset import verify_dataset_existence, main

class TestVerifyDataset:
    @patch('src.data.verify_dataset.load_dataset')
    @patch('src.data.verify_dataset.get_dataset_names')
    def test_all_datasets_available(self, mock_get_names, mock_load):
        """Test scenario where all datasets are available."""
        # Mock get_dataset_names to return both climate datasets
        mock_get_names.return_value = ["noaa/prism", "daymet/annual"]
        
        # Mock load_dataset to return a mock dataset that yields a dummy item
        mock_dataset_iter = iter([{"dummy": "data"}])
        mock_load.return_value = mock_dataset_iter

        with patch('src.data.verify_dataset.setup_logging') as mock_log:
            # Mock logger to avoid file writes during test
            mock_logger = MagicMock()
            mock_log.return_value = mock_logger

            # Ensure output directory exists for the test
            output_dir = Path("data/provenance")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "data_availability_report.json"

            # Run the function
            result = verify_dataset_existence()

            # Assertions
            assert result["ebird_available"] is True
            assert result["noaa_available"] is True
            assert result["daymet_available"] is True
            
            # Verify file was written
            assert output_path.exists()
            with open(output_path, "r") as f:
                saved_report = json.load(f)
                assert saved_report["ebird_available"] is True

    @patch('src.data.verify_dataset.load_dataset')
    @patch('src.data.verify_dataset.get_dataset_names')
    def test_ebird_missing_raises_error(self, mock_get_names, mock_load):
        """Test that a RuntimeError is raised if eBird is missing."""
        # Mock get_dataset_names
        mock_get_names.return_value = ["noaa/prism"]
        
        # Mock load_dataset to raise an exception for eBird, succeed for others
        def side_effect(dataset_id, *args, **kwargs):
            if dataset_id == "vvud/eb-data":
                raise ConnectionError("Dataset not found")
            return iter([{"dummy": "data"}])

        mock_load.side_effect = side_effect

        with patch('src.data.verify_dataset.setup_logging') as mock_log:
            mock_logger = MagicMock()
            mock_log.return_value = mock_logger

            output_dir = Path("data/provenance")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Should raise RuntimeError
            with pytest.raises(RuntimeError, match="CRITICAL FAILURE"):
                verify_dataset_existence()

    @patch('src.data.verify_dataset.load_dataset')
    @patch('src.data.verify_dataset.get_dataset_names')
    def test_only_daymet_available(self, mock_get_names, mock_load):
        """Test scenario where only Daymet is available as climate source."""
        mock_get_names.return_value = ["daymet/annual"]
        
        def side_effect(dataset_id, *args, **kwargs):
            if dataset_id == "vvud/eb-data" or dataset_id == "daymet/annual":
                return iter([{"dummy": "data"}])
            raise KeyError("Not found")

        mock_load.side_effect = side_effect

        with patch('src.data.verify_dataset.setup_logging') as mock_log:
            mock_logger = MagicMock()
            mock_log.return_value = mock_logger

            output_dir = Path("data/provenance")
            output_dir.mkdir(parents=True, exist_ok=True)

            result = verify_dataset_existence()

            assert result["ebird_available"] is True
            assert result["noaa_available"] is False
            assert result["daymet_available"] is True

    def test_main_entry_point(self):
        """Test that main() calls verify_dataset_existence without erroring on import."""
        # This is a basic smoke test to ensure the entry point exists
        assert callable(main)