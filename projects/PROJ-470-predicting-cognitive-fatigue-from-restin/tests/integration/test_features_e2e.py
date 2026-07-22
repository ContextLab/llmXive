import pytest
import os
import sys
import pandas as pd
import numpy as np
import mne
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from features import main as run_features_pipeline

@pytest.fixture(scope="module")
def sample_eeg_file(tmp_path_factory):
    """
    Create a minimal valid FIF file for integration testing.
    This simulates the output of the preprocessing step (T010).
    """
    out_dir = tmp_path_factory.mktemp("data")
    data_dir = out_dir / "processed"
    data_dir.mkdir()
    
    # Create synthetic EEG data: 30 participants (simulated as 1 long file for this test)
    # In reality, this would be multiple files, but for integration we test the reader logic.
    # We create one file with multiple channels.
    
    n_channels = 2
    n_samples = 10000
    sfreq = 250.0
    
    # Generate data: Channel 0 is white noise, Channel 1 is sine wave
    np.random.seed(42)
    data = np.zeros((n_channels, n_samples))
    data[0] = np.random.randn(n_samples) * 10  # White noise
    data[1] = np.sin(2 * np.pi * 10 * np.arange(n_samples) / sfreq) * 10  # 10Hz sine
    
    ch_names = ['EEG001', 'EEG002']
    info = mne.create_info(ch_names, sfreq, ch_types='eeg')
    raw = mne.io.RawArray(data, info)
    
    # Save as FIF
    output_path = data_dir / "cleaned_eeg.fif"
    raw.save(output_path, overwrite=True)
    
    return output_path

def test_features_pipeline_writes_lzc_file(sample_eeg_file, tmp_path):
    """
    End-to-end test: Run features.py and assert data/processed/lzc_metrics.csv exists
    and contains the correct schema.
    """
    # Change to a temporary directory to simulate project root
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Create necessary directory structure
        (Path("data") / "processed").mkdir(parents=True, exist_ok=True)
        
        # Copy the sample file to the expected location
        import shutil
        shutil.copy(sample_eeg_file, "data/processed/cleaned_eeg.fif")
        
        # Run the pipeline
        run_features_pipeline()
        
        # Assert output file exists
        lzc_path = Path("data/processed/lzc_metrics.csv")
        assert lzc_path.exists(), "LZC metrics file was not created."
        
        # Load and validate schema
        df = pd.read_csv(lzc_path)
        
        # Check columns
        required_cols = ["participant_id", "channel", "lzc_value"]
        assert list(df.columns) == required_cols, f"Columns mismatch: {list(df.columns)} vs {required_cols}"
        
        # Check non-empty
        assert len(df) > 0, "LZC metrics file is empty."
        
        # Check data types
        assert df['participant_id'].dtype == object or df['participant_id'].dtype == str
        assert df['channel'].dtype == object or df['channel'].dtype == str
        assert pd.api.types.is_float_dtype(df['lzc_value'])
        
    finally:
        os.chdir(original_cwd)

def test_features_pipeline_writes_pe_file(sample_eeg_file, tmp_path):
    """
    End-to-end test: Run features.py and assert data/processed/pe_metrics.csv exists
    and contains the correct schema.
    """
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        (Path("data") / "processed").mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.copy(sample_eeg_file, "data/processed/cleaned_eeg.fif")
        
        run_features_pipeline()
        
        pe_path = Path("data/processed/pe_metrics.csv")
        assert pe_path.exists(), "PE metrics file was not created."
        
        df = pd.read_csv(pe_path)
        
        required_cols = ["participant_id", "channel", "pe_value"]
        assert list(df.columns) == required_cols, f"Columns mismatch: {list(df.columns)} vs {required_cols}"
        
        assert len(df) > 0, "PE metrics file is empty."
        
        assert pd.api.types.is_float_dtype(df['pe_value'])
        
    finally:
        os.chdir(original_cwd)
