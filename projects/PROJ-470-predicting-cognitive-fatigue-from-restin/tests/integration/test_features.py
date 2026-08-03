import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
import mne

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from features import calculate_lzc, calculate_permutation_entropy, process_eeg_segments, save_metrics_to_csv

def test_pe_integration():
    """
    Integration test for Permutation Entropy calculation on simulated EEG data.
    This test creates a minimal preprocessed EEG file (FIF format) and runs
    the feature extraction pipeline to ensure it produces valid output files.
    
    Per T016 verification:
    - Use real data structure (FIF file) if available, otherwise simulate minimal valid structure for integration.
    - Assert output file exists and contains correct schema.
    - If real dataset N < 30, skip (but here we simulate a small batch to test the pipeline logic).
    """
    # Create a temporary directory for this test's artifacts
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup paths
        data_dir = Path(tmpdir) / "data" / "processed"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a synthetic EEG file (simulating data/processed/cleaned_eeg.fif)
        # We generate a minimal Raw object with 2 channels and 120 seconds of data
        # to mimic the output of T011 (preprocess.py)
        sampling_rate = 256
        duration = 120  # seconds
        n_channels = 2
        n_samples = duration * sampling_rate
        
        # Generate synthetic EEG data (white noise + low amplitude 50Hz noise)
        # Using seed for reproducibility in integration test
        np.random.seed(42)
        data = np.random.normal(0, 10e-6, (n_channels, n_samples))
        
        # Add a small 50Hz component to make it realistic
        time_vec = np.arange(n_samples) / sampling_rate
        data[0] += 50e-6 * np.sin(2 * np.pi * 50 * time_vec)
        
        # Create channel names and info
        ch_names = [f'EEG {i:03d}' for i in range(n_channels)]
        sfreq = sampling_rate
        info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
        
        # Create Raw object
        raw = mne.io.RawArray(data, info)
        
        # Save to FIF
        eeg_file = data_dir / "cleaned_eeg.fif"
        raw.save(eeg_file, overwrite=True)
        
        # Create a minimal metadata file for the participant
        metadata_dir = Path(tmpdir) / "data" / "raw"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = metadata_dir / "metadata.csv"
        pd.DataFrame({
            'participant_id': ['P001'],
            'file_path': [str(eeg_file)],
            'pre_fatigue': [3.0],
            'post_fatigue': [5.0]
        }).to_csv(metadata_file, index=False)
        
        # Now run the feature extraction pipeline on this simulated data
        # We call process_eeg_segments directly to simulate what main() does
        try:
            # Process the EEG segments
            lzc_results, pe_results = process_eeg_segments(
                raw_file=eeg_file,
                participant_id='P001',
                order=3,
                delay=1
            )
            
            # Save results to CSV (simulating what main() does)
            lzc_csv_path = Path(tmpdir) / "data" / "processed" / "lzc_metrics.csv"
            pe_csv_path = Path(tmpdir) / "data" / "processed" / "pe_metrics.csv"
            
            save_metrics_to_csv(lzc_results, str(lzc_csv_path), metric_type='LZC')
            save_metrics_to_csv(pe_results, str(pe_csv_path), metric_type='PE')
            
            # Verify LZC output
            assert lzc_csv_path.exists(), "LZC metrics CSV must be created"
            df_lzc = pd.read_csv(lzc_csv_path)
            assert 'participant_id' in df_lzc.columns
            assert 'channel' in df_lzc.columns
            assert 'lzc_value' in df_lzc.columns
            assert len(df_lzc) > 0
            
            # Verify PE output
            assert pe_csv_path.exists(), "PE metrics CSV must be created"
            df_pe = pd.read_csv(pe_csv_path)
            assert 'participant_id' in df_pe.columns
            assert 'channel' in df_pe.columns
            assert 'pe_value' in df_pe.columns
            assert len(df_pe) > 0
            
            # Verify values are numeric and within expected ranges
            assert df_pe['pe_value'].notna().all(), "PE values must not be NaN"
            assert (df_pe['pe_value'] >= 0).all(), "PE values must be non-negative"
            
            # Theoretical max for order=3 is log2(3!) = log2(6) ≈ 2.58
            import math
            max_pe = math.log2(math.factorial(3))
            assert (df_pe['pe_value'] <= max_pe).all(), f"PE values must not exceed {max_pe}"
            
        except Exception as e:
            pytest.fail(f"Feature extraction pipeline failed: {str(e)}")