import os
import sys
import json
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd

# Add code to path if not already
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from features.save_features import load_raw_data, save_features, main
from config import get_config

@pytest.fixture
def mock_config():
    """Mock the config to use temp directories."""
    with patch('features.save_features.get_config') as mock_get_config:
        mock_config = MagicMock()
        # Create temp dirs
        temp_root = Path(tempfile.mkdtemp())
        mock_config.data_raw_dir = temp_root / "data" / "raw"
        mock_config.data_raw_dir.mkdir(parents=True, exist_ok=True)
        mock_config.data_processed_dir = temp_root / "data" / "processed"
        mock_config.data_processed_dir.mkdir(parents=True, exist_ok=True)
        
        mock_get_config.return_value = mock_config
        yield mock_config
        # Cleanup
        import shutil
        shutil.rmtree(temp_root)

@pytest.fixture
def sample_raw_data(mock_config):
    """Create a sample raw data file."""
    data = [
        {
            "participant_id": "P001",
            "trial_id": 1,
            "gaze_coordinates": [{"x": 100, "y": 100, "time": 0}, {"x": 105, "y": 105, "time": 100}],
            "response_times": 500,
            "emotion_labels": "happy",
            "roi_annotations": {"eye": [0, 0, 50, 50], "mouth": [0, 50, 50, 100]}
        },
        {
            "participant_id": "P001",
            "trial_id": 2,
            "gaze_coordinates": [{"x": 120, "y": 120, "time": 0}, {"x": 125, "y": 125, "time": 100}],
            "response_times": 450,
            "emotion_labels": "sad",
            "roi_annotations": {"eye": [0, 0, 50, 50], "mouth": [0, 50, 50, 100]}
        }
    ]
    data_file = mock_config.data_raw_dir / "sample_data.json"
    with open(data_file, 'w') as f:
        json.dump(data, f)
    return data_file

def test_load_raw_data_valid(mock_config, sample_raw_data):
    """Test loading valid raw data."""
    logger = logging.getLogger("test")
    data = load_raw_data(logger)
    assert data is not None
    assert len(data) == 2
    assert data[0]["participant_id"] == "P001"

def test_load_raw_data_missing_dir(mock_config):
    """Test loading when raw directory is missing."""
    mock_config.data_raw_dir = Path("/nonexistent/path")
    logger = logging.getLogger("test")
    data = load_raw_data(logger)
    assert data is None

def test_save_features(tmp_path):
    """Test saving features to CSV."""
    df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
    output_path = tmp_path / "test_features.csv"
    
    logger = logging.getLogger("test")
    success = save_features(df, output_path, logger)
    
    assert success
    assert output_path.exists()
    
    # Verify content
    loaded_df = pd.read_csv(output_path)
    assert len(loaded_df) == 2
    assert "col1" in loaded_df.columns

@patch('features.save_features.load_raw_data')
@patch('features.save_features.process_participant_record')
@patch('features.save_features.calculate_continuous_ratio')
@patch('features.save_features.save_features')
def test_main_flow(mock_save, mock_calc, mock_process, mock_load, mock_config):
    """Test the main flow of T019."""
    # Setup mocks
    mock_load.return_value = [{"id": 1}, {"id": 2}]
    mock_process.return_value = {"id": 1, "feature": 10.0}
    mock_calc.return_value = pd.DataFrame({"id": [1], "feature": [10.0], "ratio": [0.5]})
    mock_save.return_value = True

    logger = logging.getLogger("test")
    with patch('features.save_features.get_logger', return_value=logger):
        result = main()
    
    assert result == 0
    mock_load.assert_called_once()
    mock_process.assert_called()
    mock_calc.assert_called_once()
    mock_save.assert_called_once()
