import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import sys
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.ingestion import aggregate_seed_logs
from code.utils.io_utils import read_csv

def test_full_pipeline_edge_cases():
    """
    Integration test: Create a fake log file with edge cases, run pipeline, verify output.
    """
    # Create temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        log_dir = tmpdir / "raw"
        log_dir.mkdir()
        output_dir = tmpdir / "processed"
        output_dir.mkdir()
        
        # Create a synthetic log file with edge cases
        # Note: In real execution, this file would come from T013.
        # For this test, we simulate the file content to test the logic.
        data = {
            'step': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            't': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            'J_biased': [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0],
            'J_unbiased': [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0], # Zero variance
            'J_gold': [100.0] * 10,
            'seed_id': ['test_seed'] * 10,
            'bias_type': ['test_type'] * 10,
        }
        
        # Add a gap
        data['J_unbiased'][5] = np.nan # Step 6 is missing
        
        df = pd.DataFrame(data)
        log_file = log_dir / "seed_test.csv"
        df.to_csv(log_file, index=False)
        
        output_path = output_dir / "trajectories_divergence.csv"
        
        # Run the pipeline
        aggregate_seed_logs(log_dir, output_path)
        
        # Verify output
        assert output_path.exists(), "Output file was not created"
        
        result = read_csv(output_path)
        
        # Check columns exist
        assert 'G_t' in result.columns
        assert 'G_t_interp' in result.columns
        assert 'dG_t' in result.columns
        assert 'z_G_t' in result.columns
        
        # Check zero variance handling (all z_G_t should be 0)
        # Since J_biased and J_unbiased are constant, G_t is constant (5.0).
        # Variance is 0.
        assert all(result['z_G_t'] == 0.0), f"Expected all z-scores to be 0 for zero variance, got {result['z_G_t'].values}"
        
        # Check interpolation for the gap at step 6
        step6 = result[result['step'] == 6]
        assert len(step6) == 1
        # G_t should be 5.0 (interpolated from neighbors which are also 5.0)
        assert np.isclose(step6['G_t_interp'].values[0], 5.0)

def test_missing_data_skip():
    """
    Integration test: Verify that rows with un-interpolatable missing data are handled.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        log_dir = tmpdir / "raw"
        log_dir.mkdir()
        output_dir = tmpdir / "processed"
        output_dir.mkdir()
        
        # Create data with a large gap that cannot be interpolated
        data = {
            'step': [1, 2, 3, 4, 5],
            't': [1.0, 2.0, 3.0, 4.0, 5.0],
            'J_biased': [10.0, 10.0, 10.0, 10.0, 10.0],
            'J_unbiased': [5.0, np.nan, np.nan, np.nan, 1.0], # Steps 2,3,4 missing
            'J_gold': [100.0] * 5,
            'seed_id': ['test_seed'] * 5,
            'bias_type': ['test_type'] * 5,
        }
        
        df = pd.DataFrame(data)
        log_file = log_dir / "seed_gap.csv"
        df.to_csv(log_file, index=False)
        
        output_path = output_dir / "trajectories_divergence.csv"
        
        aggregate_seed_logs(log_dir, output_path)
        
        result = read_csv(output_path)
        
        # Steps 2, 3, 4 should have NaN for G_t_interp and dG_t
        for step in [2, 3, 4]:
            row = result[result['step'] == step]
            assert pd.isna(row['G_t_interp'].values[0]), f"Step {step} G_t_interp should be NaN"
            assert pd.isna(row['dG_t'].values[0]), f"Step {step} dG_t should be NaN"
            # z_G_t should be 0 or NaN depending on implementation, but not a calculated number
            # Our code sets it to 0 if std is NaN/0.
            # Since G_t_interp is NaN, the rolling window might be affected, but the row itself is skipped in calculation.
            # Actually, in our code, we drop NaNs for calculation, then map back.
            # So for these rows, z_G_t should be NaN because we didn't calculate it for them.
            # Let's verify the logic: valid_mask = df_result['G_t_interp'].notna().
            # If G_t_interp is NaN, it's not in valid_mask, so z_G_t remains NaN (initialized as NaN).
            assert pd.isna(row['z_G_t'].values[0]), f"Step {step} z_G_t should be NaN"