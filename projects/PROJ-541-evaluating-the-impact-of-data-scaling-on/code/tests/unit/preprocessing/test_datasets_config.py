import pytest
import yaml
import os
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock
import logging
from preprocessing.ingestion import validate_dataset_availability, load_dataset_config

# Ensure we can import from the code directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'code'))

class TestDatasetConfigValidation:
    """Tests for the dataset availability validation logic (T027a)."""

    def test_validate_with_existing_config(self, tmp_path):
        """Test validation with a valid config file containing multiple datasets."""
        # Create a temporary config file
        config_data = [
            {"name": "dataset_a", "source": "ucimlrepo/iris", "config": {"split": "train"}},
            {"name": "dataset_b", "source": "ucimlrepo/iris", "config": {"split": "train"}},
            {"name": "dataset_c", "source": "ucimlrepo/iris", "config": {"split": "train"}},
            {"name": "dataset_d", "source": "ucimlrepo/iris", "config": {"split": "train"}},
            {"name": "dataset_e", "source": "ucimlrepo/iris", "config": {"split": "train"}},
            {"name": "dataset_f", "source": "ucimlrepo/iris", "config": {"split": "train"}},
            {"name": "dataset_g", "source": "ucimlrepo/iris", "config": {"split": "train"}},
            {"name": "dataset_h", "source": "ucimlrepo/iris", "config": {"split": "train"}},
            {"name": "dataset_i", "source": "ucimlrepo/iris", "config": {"split": "train"}},
            {"name": "dataset_j", "source": "ucimlrepo/iris", "config": {"split": "train"}},
        ]
        
        config_file = tmp_path / "datasets.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Mock the load_dataset to simulate success for all
        with patch('preprocessing.ingestion.load_dataset') as mock_load:
            mock_ds = MagicMock()
            mock_load.return_value = mock_ds
            
            available, failed = validate_dataset_availability(str(config_file))
            
            assert len(available) == 10
            assert len(failed) == 0
            assert all(name in available for name in [f"dataset_{chr(97+i)}" for i in range(10)])

    def test_validate_with_failing_datasets(self, tmp_path, caplog):
        """Test validation when some datasets fail to load."""
        config_data = [
            {"name": "good_ds", "source": "ucimlrepo/iris", "config": {"split": "train"}},
            {"name": "bad_ds", "source": "non_existent_dataset_xyz", "config": {"split": "train"}},
            {"name": "good_ds_2", "source": "ucimlrepo/iris", "config": {"split": "train"}},
        ]
        
        config_file = tmp_path / "datasets.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Mock load_dataset to fail for bad_ds
        def mock_load_side_effect(name, **kwargs):
            if "non_existent" in name:
                raise ValueError("Dataset not found")
            return MagicMock()
        
        with patch('preprocessing.ingestion.load_dataset', side_effect=mock_load_side_effect):
            with caplog.at_level(logging.WARNING):
                available, failed = validate_dataset_availability(str(config_file))
                
                assert len(available) == 2
                assert len(failed) == 1
                assert "bad_ds" in failed
                assert "good_ds" in available
                assert "good_ds_2" in available
                
                # Check that a warning was logged about the failure
                assert any("NOT available" in record.message for record in caplog.records)

    def test_validate_less_than_10_triggers_warning(self, tmp_path, caplog):
        """Test that a warning is logged if fewer than 10 datasets are available."""
        # Create a config with only 5 datasets
        config_data = [
            {"name": f"ds_{i}", "source": "ucimlrepo/iris", "config": {"split": "train"}}
            for i in range(5)
        ]
        
        config_file = tmp_path / "datasets.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        with patch('preprocessing.ingestion.load_dataset') as mock_load:
            mock_load.return_value = MagicMock()
            
            with caplog.at_level(logging.WARNING):
                available, failed = validate_dataset_availability(str(config_file))
                
                assert len(available) == 5
                assert len(failed) == 0
                
                # Verify the specific warning message about insufficient datasets
                warning_messages = [r.message for r in caplog.records if r.levelname == "WARNING"]
                assert any("Insufficient number of available datasets" in msg for msg in warning_messages)
                
                # Verify that the function did NOT raise an error (it should proceed)
                # This is the key requirement of T027a: "MUST NOT raise a RuntimeError"

    def test_validate_missing_config_file(self, tmp_path, caplog):
        """Test behavior when the config file does not exist."""
        non_existent_path = str(tmp_path / "non_existent.yaml")
        
        with caplog.at_level(logging.WARNING):
            available, failed = validate_dataset_availability(non_existent_path)
            
            assert available == []
            assert failed == []
            
            assert any("Dataset configuration file not found" in r.message for r in caplog.records)

    def test_validate_sklearn_mapping(self, tmp_path):
        """Test that 'sklearn' source is correctly mapped for validation."""
        config_data = [
            {"name": "iris", "source": "sklearn", "config": {"split": "train"}}
        ]
        
        config_file = tmp_path / "datasets.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Mock load_dataset to verify it's called with the mapped ID
        with patch('preprocessing.ingestion.load_dataset') as mock_load:
            mock_load.return_value = MagicMock()
            
            available, failed = validate_dataset_availability(str(config_file))
            
            # Check that load_dataset was called with 'ucimlrepo/iris' not 'sklearn'
            mock_load.assert_called_once()
            call_args = mock_load.call_args
            assert call_args[0][0] == "ucimlrepo/iris"
            assert len(available) == 1