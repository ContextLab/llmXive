"""
Tests for T020: Correlation analysis.

Verifies that code/08_correlation_analysis.py correctly computes Pearson correlations
and produces the expected output file.
"""
import os
import sys
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code.config import get_path, set_global_seed, ensure_dirs
from code import code_08_correlation_analysis as corr_module


def test_run_correlations_logic():
    """Test the core correlation logic with known data."""
    # Create a synthetic dataset with a known correlation
    np.random.seed(42)
    n = 100
    # Create a negative correlation: as power increases, RT decreases
    power = np.random.normal(0.5, 0.1, n)
    rt = 500 - 200 * power + np.random.normal(0, 10, n)
    
    df = pd.DataFrame({
        'participant_id': range(n),
        'median_rt': rt,
        'rel_alpha_power': power,
        'rel_delta_power': np.random.normal(0.3, 0.05, n),
        'rel_theta_power': np.random.normal(0.2, 0.05, n),
        'rel_low_beta_power': np.random.normal(0.15, 0.05, n),
        'rel_high_beta_power': np.random.normal(0.1, 0.05, n),
        'rel_gamma_power': np.random.normal(0.05, 0.05, n),
    })
    
    results = corr_module.run_correlations(df)
    
    assert 'alpha' in results['band'].values
    assert 'r' in results.columns
    assert 'p' in results.columns
    
    # Check alpha correlation (should be negative)
    alpha_row = results[results['band'] == 'alpha'].iloc[0]
    assert alpha_row['r'] < 0, "Expected negative correlation for alpha"
    assert alpha_row['n'] == n
    
    # Verify p-value calculation roughly matches
    expected_r, expected_p = stats.pearsonr(power, rt)
    assert np.isclose(alpha_row['r'], expected_r, rtol=1e-5)
    assert np.isclose(alpha_row['p'], expected_p, rtol=1e-5)


def test_load_features_missing_file():
    """Test that load_features raises error if file missing."""
    # Temporarily rename the file if it exists
    features_path = get_path("processed", "features.csv")
    backup_path = features_path + ".bak"
    
    if os.path.exists(features_path):
        shutil.move(features_path, backup_path)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock get_path to return non-existent path
            original_get_path = corr_module.get_path
            def mock_get_path(subdir, filename):
                if subdir == "processed" and filename == "features.csv":
                    return os.path.join(tmpdir, "nonexistent.csv")
                return original_get_path(subdir, filename)
            
            corr_module.get_path = mock_get_path
            try:
                corr_module.load_features()
                assert False, "Expected FileNotFoundError"
            except FileNotFoundError:
                pass
            finally:
                corr_module.get_path = original_get_path
    finally:
        # Restore file
        if os.path.exists(backup_path):
            shutil.move(backup_path, features_path)


def test_output_file_creation(tmp_path):
    """Test that the main function creates the output file."""
    # This test assumes features.csv exists (created by T015/T016)
    # If not, we skip or mock
    features_path = get_path("processed", "features.csv")
    if not os.path.exists(features_path):
        print("Skipping output test: features.csv not found. Run T015/T016 first.")
        return

    output_file = tmp_path / "test_correlations.csv"
    
    # Mock get_path to write to tmp_path
    original_get_path = corr_module.get_path
    def mock_get_path(subdir, filename):
        if subdir == "processed" and filename == "correlations.csv":
            return str(output_file)
        if subdir == "processed" and filename == "features.csv":
            return features_path
        return original_get_path(subdir, filename)
    
    corr_module.get_path = mock_get_path
    
    try:
        result = corr_module.main()
        assert result == 0
        assert output_file.exists()
        
        df = pd.read_csv(output_file)
        assert 'band' in df.columns
        assert 'r' in df.columns
        assert 'p' in df.columns
        assert len(df) == 6  # 6 bands
    finally:
        corr_module.get_path = original_get_path
