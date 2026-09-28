import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

# Ensure code is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.ingestion import download_dataset, load_config, RAW_DATA_PATH

def test_download_fails_loudly():
    """Test that download_dataset raises RuntimeError on failure, not synthetic fallback."""
    dataset_id = "non_existent_dataset_xyz"
    
    with patch('data.ingestion.load_dataset') as mock_load:
        # Simulate a failure in loading
        mock_load.side_effect = Exception("Dataset not found or network error")
        
        with pytest.raises(RuntimeError) as excinfo:
            download_dataset(dataset_id, Path("data/raw/test.csv"))
        
        assert "Aborting to prevent synthetic data fabrication" in str(excinfo.value)
        assert "Real data fetch failed" in str(excinfo.value)

def test_missing_config_raises_error():
    """Test that missing config raises an error."""
    with patch('data.ingestion.CONFIG_PATH', Path("non_existent_config.yaml")):
        with pytest.raises(FileNotFoundError):
            load_config()
