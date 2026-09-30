import os
import sys
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing.load_data import normalize_columns, load_raw_data_from_dataset
from config import load_config

class TestNormalizeColumns:
    def test_normalize_columns_basic(self):
        """Test basic column normalization."""
        # Create a mock raw dataframe
        data = {
            'time': [1, 2, 3, 4, 5],
            'x_coord': [10.0, 11.0, 12.0, 13.0, 14.0],
            'y_coord': [20.0, 21.0, 22.0, 23.0, 24.0],
            'pupil': [3.0, 3.1, 3.2, 3.3, 3.4]
        }
        df = pd.DataFrame(data)

        config = {
            'column_mapping': {
                'time': ['time', 'timestamp'],
                'x': ['x_coord', 'x'],
                'y': ['y_coord', 'y'],
                'pupil': ['pupil', 'pupil_diameter']
            }
        }

        result = normalize_columns(df, config)

        # Check that standard columns exist
        assert 'timestamp' in result.columns
        assert 'x' in result.columns
        assert 'y' in result.columns
        assert 'pupil_diameter' in result.columns

        # Check values are preserved
        assert result['timestamp'].tolist() == [1, 2, 3, 4, 5]
        assert result['x'].tolist() == [10.0, 11.0, 12.0, 13.0, 14.0]

    def test_normalize_columns_missing_data(self):
        """Test handling of missing data in normalization."""
        data = {
            'time': [1, None, 3],
            'x': [10.0, None, 12.0],
            'y': [20.0, 21.0, 22.0],
            'pupil_diameter': [3.0, None, 3.2]
        }
        df = pd.DataFrame(data)

        config = {
            'column_mapping': {
                'time': ['time'],
                'x': ['x'],
                'y': ['y'],
                'pupil': ['pupil_diameter']
            }
        }

        result = normalize_columns(df, config)

        # Should drop rows with missing critical data
        assert len(result) == 2

    def test_normalize_columns_invalid_names(self):
        """Test error when required columns cannot be found."""
        data = {
            'wrong_time': [1, 2, 3],
            'wrong_x': [10.0, 11.0, 12.0],
            'wrong_y': [20.0, 21.0, 22.0],
            'wrong_pupil': [3.0, 3.1, 3.2]
        }
        df = pd.DataFrame(data)

        config = {
            'column_mapping': {
                'time': ['time'],
                'x': ['x'],
                'y': ['y'],
                'pupil': ['pupil_diameter']
            }
        }

        with pytest.raises(ValueError):
            normalize_columns(df, config)

class TestConfigLoading:
    def test_config_structure(self):
        """Test that config.yaml has required structure."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            config = load_config(config_path)
            assert 'paths' in config
            assert 'processed' in config['paths']
            assert 'datasets' in config
        else:
            pytest.skip("config.yaml not found")
