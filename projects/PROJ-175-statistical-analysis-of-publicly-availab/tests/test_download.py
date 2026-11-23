import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.download import (
    DataUnavailableError,
    ensure_directories,
    verify_url_status,
    load_verification_report,
    download_recipe1m_streaming,
    save_manifest
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_ensure_directories(temp_dir):
    """Test that ensure_directories creates the required folders."""
    ensure_directories(temp_dir)
    
    expected_dirs = ["raw", "processed", "final", "logs"]
    for dir_name in expected_dirs:
        assert (temp_dir / dir_name).exists(), f"Directory {dir_name} was not created"

def test_load_verification_report_missing(temp_dir):
    """Test that load_verification_report raises FileNotFoundError when report is missing."""
    with pytest.raises(FileNotFoundError):
        load_verification_report(temp_dir)

def test_load_verification_report_success(temp_dir):
    """Test loading a valid verification report."""
    # Create a mock verification report
    report_path = temp_dir / "download_status.json"
    report_data = {
        "recipe1m": {"status": "SUCCESS"},
        "flavordb": {"status": "FAILED"},
        "counterfactual": {"status": "SUCCESS"}
    }
    with open(report_path, 'w') as f:
        json.dump(report_data, f)
    
    report = load_verification_report(temp_dir)
    assert report["recipe1m"]["status"] == "SUCCESS"
    assert report["flavordb"]["status"] == "FAILED"

def test_download_recipe1m_streaming_missing_verification(temp_dir):
    """Test that download_recipe1m_streaming raises DataUnavailableError if verification fails."""
    # Create a verification report with recipe1m as FAILED
    report_path = temp_dir / "download_status.json"
    report_data = {"recipe1m": {"status": "FAILED"}}
    with open(report_path, 'w') as f:
        json.dump(report_data, f)
    
    with pytest.raises(DataUnavailableError, match="Recipe1M dataset is marked as unavailable"):
        download_recipe1m_streaming(temp_dir)

@patch('code.data.download.load_dataset')
@patch('code.data.download.pd.DataFrame')
def test_download_recipe1m_streaming_success(mock_dataframe, mock_load_dataset, temp_dir):
    """Test successful streaming download with mocked dependencies."""
    # Setup verification report
    report_path = temp_dir / "download_status.json"
    with open(report_path, 'w') as f:
        json.dump({"recipe1m": {"status": "SUCCESS"}}, f)
    
    # Mock dataset
    mock_dataset = MagicMock()
    mock_dataset.keys.return_value = ['train']
    mock_split = MagicMock()
    mock_split.iter.return_value = [
        {'ingredient': ['salt', 'pepper'], 'amount': [1, 2]},
        {'ingredient': ['sugar'], 'amount': [3]}
    ]
    mock_dataset.__getitem__.return_value = mock_split
    mock_load_dataset.return_value = mock_dataset
    
    # Mock DataFrame to avoid actual pandas operations
    mock_df = MagicMock()
    mock_dataframe.return_value = mock_df
    mock_df.__len__.return_value = 2
    mock_df.__add__.return_value = mock_df
    mock_df.columns = ['ingredient', 'amount']
    
    # Run the function
    result = download_recipe1m_streaming(temp_dir)
    
    # Verify results
    assert result is True
    assert (temp_dir / "raw" / "recipe1m_raw.parquet").exists()
    mock_load_dataset.assert_called_once_with('recipe1m', streaming=True)
    mock_split.iter.assert_called_once_with(batch_size=10000)

def test_save_manifest(temp_dir):
    """Test saving a manifest file."""
    manifest_data = {
        "dataset_name": "recipe1m",
        "total_rows": 1000,
        "columns": ["ingredient", "amount"]
    }
    save_manifest(temp_dir, "recipe1m", manifest_data)
    
    manifest_path = temp_dir / "raw" / "recipe1m_manifest.json"
    assert manifest_path.exists()
    
    with open(manifest_path, 'r') as f:
        saved_manifest = json.load(f)
    
    assert saved_manifest["dataset_name"] == "recipe1m"
    assert saved_manifest["total_rows"] == 1000
