import os
import sys
import pytest
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

# Import the function under test
from src.data.align import run_lagged_alignment, calculate_mmn_amplitude, bin_behavioral_data

class TestT024LaggedAlignment:
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory with mock data for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            
            # Create preprocessed directory
            preprocessed_dir = data_dir / "preprocessed"
            preprocessed_dir.mkdir()
            
            # Create mock epochs for a subject
            # Format: trial_id, condition, time, C3, C4, CP3, CP4
            n_trials = 100
            trials = np.arange(n_trials)
            conditions = np.random.choice(['standard', 'deviant'], n_trials)
            times = np.linspace(-0.2, 0.5, 50) # 50 time points
            
            # Create a long-format dataframe for epochs
            # Each row is a trial x time point
            rows = []
            for trial in trials:
                cond = conditions[trial]
                # Simulate signal: deviant has slightly higher amplitude in CP3/CP4
                base_signal = np.random.randn(50) * 0.1
                if cond == 'deviant':
                    # Add a small MMN-like deflection
                    base_signal += 0.05 
                
                for t_idx, t in enumerate(times):
                    rows.append({
                        'trial_id': trial,
                        'condition': cond,
                        'time': t,
                        'C3': base_signal[t_idx] + np.random.randn() * 0.01,
                        'C4': base_signal[t_idx] + np.random.randn() * 0.01,
                        'CP3': base_signal[t_idx] + np.random.randn() * 0.01,
                        'CP4': base_signal[t_idx] + np.random.randn() * 0.01,
                        'subject_id': 'sub-001'
                    })
            
            epochs_df = pd.DataFrame(rows)
            epochs_path = preprocessed_dir / "sub-001_epochs.csv"
            epochs_df.to_csv(epochs_path, index=False)
            
            # Create mock behavioral data
            behavioral_data = []
            for i in range(n_trials):
                behavioral_data.append({
                    'trial_id': i,
                    'correct': np.random.choice([0, 1]),
                    'subject_id': 'sub-001'
                })
            
            behavioral_df = pd.DataFrame(behavioral_data)
            behavioral_path = data_dir / "behavioral_logs.csv"
            behavioral_df.to_csv(behavioral_path, index=False)
            
            yield data_dir

    def test_lagged_alignment_schema_and_logic(self, temp_data_dir):
        """
        Test that run_lagged_alignment produces the correct schema and logic.
        """
        output_path = temp_data_dir / "interim_lagged_mmns.csv"
        config = {
            'sfreq': 1000.0,
            'channels': ['C3', 'C4', 'CP3', 'CP4'],
            't_min': -0.2,
            't_max': 0.2,
            'lag_window_size': 50,
            'block_size': 20
        }
        
        run_lagged_alignment(temp_data_dir, output_path, config)
        
        # Check that the output file exists
        assert output_path.exists(), "Output file not created"
        
        # Load the output
        results_df = pd.read_csv(output_path)
        
        # Check schema
        expected_columns = ['subject_id', 'block_id', 'mmn_amplitude', 'source_window_start_trial']
        assert list(results_df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(results_df.columns)}"
        
        # Check that we have results for multiple blocks
        assert len(results_df) > 0, "No results generated"
        
        # Check that source_window_start_trial is consistent with the lag logic
        # For block 0, start_trial is 0, source_window should be [0-50, 0-10] -> clamped to [0, 0] if negative
        # But in our test, block_size=20, so block 0 is trials 0-19.
        # Source window for block 0: [0-50, 0-10] -> [0, 0] (clamped) -> invalid window?
        # Let's check block 1: start_trial=20, source_window=[20-50, 20-10] = [0, 10]
        # So source_window_start_trial should be 0 for block 1.
        
        # Verify that mmn_amplitude is a float and not NaN for valid blocks
        assert results_df['mmn_amplitude'].notna().all(), "Some MMN amplitudes are NaN"
        
        # Verify that source_window_start_trial is non-negative
        assert (results_df['source_window_start_trial'] >= 0).all(), "Negative source_window_start_trial"
        
        print("Lagged alignment test passed")

    def test_mmn_amplitude_calculation(self, temp_data_dir):
        """
        Test the MMN amplitude calculation function directly.
        """
        epochs_path = temp_data_dir / "preprocessed" / "sub-001_epochs.csv"
        epochs_df = pd.read_csv(epochs_path)
        
        # Filter for a specific trial range to simulate a window
        window_epochs = epochs_df[epochs_df['trial_id'].isin(range(0, 10))]
        
        mmn_amp = calculate_mmn_amplitude(
            window_epochs,
            ['C3', 'C4', 'CP3', 'CP4'],
            -0.2,
            0.2,
            1000.0
        )
        
        # MMN amplitude should be a float
        assert isinstance(mmn_amp, float) or isinstance(mmn_amp, np.floating), "MMN amplitude is not a float"
        
        # It should not be NaN if there is data
        assert not np.isnan(mmn_amp), "MMN amplitude is NaN"
        
        print("MMN amplitude calculation test passed")
