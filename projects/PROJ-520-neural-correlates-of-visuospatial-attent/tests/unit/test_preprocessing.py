import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocessing import (
    download_and_validate_dataset,
    apply_filters,
    run_ica,
    segment_epochs,
    validate_sample_size,
    preprocess_pipeline
)

def test_download_and_validate_dataset():
    """Test that the dataset download and validation function runs without error."""
    # This test verifies FR-001 implementation
    # We expect it to run with the sample dataset
    try:
        path, report = download_and_validate_dataset("sample-ica")
        assert path.exists(), "Dataset path does not exist"
        assert report["bids_compliant"], "Dataset is not BIDS compliant"
        assert report["event_markers_found"], "Event markers not found"
        assert "validation_report.json" in [f.name for f in path.glob("*.json")]
    except ImportError as e:
        pytest.skip(f"MNE not installed: {e}")

def test_validate_sample_size_pass():
    """Test sample size validation with sufficient epochs."""
    # Create a mock epochs object
    import mne
    sfreq = 1000.0
    info = mne.create_info(ch_names=['MEG 001', 'MEG 002'], sfreq=sfreq, ch_types='mag')
    data = np.random.randn(100, 2, 2000) # 100 epochs, 2 chs, 2s
    events = np.array([[i*1000, 0, 1] for i in range(100)]) # 100 events
    event_id = {'test': 1}
    
    epochs = mne.EpochsArray(data, info, events, event_id=event_id)
    
    report = validate_sample_size(epochs, min_epochs=50)
    assert report["is_valid"]
    assert report["total_epochs"] == 100

def test_validate_sample_size_fail():
    """Test sample size validation with insufficient epochs."""
    import mne
    sfreq = 1000.0
    info = mne.create_info(ch_names=['MEG 001'], sfreq=sfreq, ch_types='mag')
    data = np.random.randn(20, 1, 2000) # 20 epochs
    events = np.array([[i*1000, 0, 1] for i in range(20)])
    event_id = {'test': 1}
    
    epochs = mne.EpochsArray(data, info, events, event_id=event_id)
    
    with pytest.raises(ValueError):
        validate_sample_size(epochs, min_epochs=50)

def test_preprocess_pipeline_integration():
    """Integration test for the full pipeline."""
    # This is a lightweight integration test
    # It may be skipped if MNE is not installed or if the download takes too long in CI
    try:
        result = preprocess_pipeline("sample-ica")
        assert result["status"] == "success"
        assert result["epochs_count"] > 0
        assert "validation" in result
    except ImportError:
        pytest.skip("MNE not installed")
    except Exception as e:
        # If the specific dataset is not available, skip
        if "download" in str(e).lower() or "not found" in str(e).lower():
            pytest.skip("Dataset download failed or not found")
        else:
            raise