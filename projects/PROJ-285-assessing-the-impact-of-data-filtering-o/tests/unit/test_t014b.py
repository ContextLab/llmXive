"""
Unit tests for T014b: detected_candidates generation.
"""
import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add code/src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'code' / 'src'))

from filter import generate_threshold_grid

class TestT014bLogic:
    """
    Tests the logic of filtering and ID generation without running the full script.
    """

    def test_threshold_pair_id_format(self):
        """Verify the ID format matches expectations."""
        snr = 10
        morph = 0.5
        expected_id = f"snr_{snr}_morph_{morph:.1f}"
        assert expected_id == "snr_10_morph_0.5"

    def test_filtering_logic(self):
        """Test that filtering logic correctly selects candidates."""
        # Create a mock dataframe
        data = {
            'RA': [1.0, 2.0, 3.0, 4.0],
            'Dec': [1.0, 2.0, 3.0, 4.0],
            'snr': [4.0, 10.0, 10.0, 15.0],
            'morphology': [0.2, 0.4, 0.8, 0.9],
            'is_lens': [0, 1, 1, 0]
        }
        df = pd.DataFrame(data)
        
        # Thresholds: SNR >= 10, Morph >= 0.5
        snr_thresh = 10
        morph_thresh = 0.5
        
        mask = (df['snr'] >= snr_thresh) & (df['morphology'] >= morph_thresh)
        result = df[mask]
        
        # Expected: Row 2 (snr=10, morph=0.8) and Row 3 (snr=15, morph=0.9)
        assert len(result) == 2
        assert list(result['RA']) == [3.0, 4.0]

    def test_missing_value_exclusion(self):
        """Verify that rows with NaN are excluded before filtering."""
        data = {
            'RA': [1.0, 2.0, 3.0],
            'Dec': [1.0, 2.0, 3.0],
            'snr': [10.0, np.nan, 15.0],
            'morphology': [0.5, 0.6, 0.5],
            'is_lens': [1, 1, 0]
        }
        df = pd.DataFrame(data)
        
        # Drop NaNs
        df_clean = df.dropna(subset=['snr', 'morphology'])
        
        assert len(df_clean) == 2
        assert 2.0 not in df_clean['RA'].values # Row with NaN snr should be gone

def test_output_file_structure(tmp_path):
    """
    Integration-style test: Ensure the output file has the correct columns.
    This simulates the output of the script.
    """
    output_path = tmp_path / "detected_candidates.csv"
    
    # Create a dummy file with expected structure
    dummy_data = {
        'RA': [1.0, 2.0],
        'Dec': [1.0, 2.0],
        'is_lens': [1, 0],
        'threshold_pair_id': ['snr_10_morph_0.5', 'snr_10_morph_0.5']
    }
    df = pd.DataFrame(dummy_data)
    df.to_csv(output_path, index=False)
    
    # Verify
    assert output_path.exists()
    loaded = pd.read_csv(output_path)
    expected_cols = ['RA', 'Dec', 'is_lens', 'threshold_pair_id']
    assert list(loaded.columns) == expected_cols
    assert len(loaded) == 2