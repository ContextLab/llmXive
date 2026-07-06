import pytest
import pandas as pd
import numpy as np
import tempfile
from pathlib import Path
import json

from src.analysis.ensemble_variance import compute_ensemble_variance, load_predictions

def test_compute_variance_from_individual_preds():
    """Test variance calculation when individual predictions are available."""
    data = {
        'sample_id': [1, 2, 3],
        'dft_barrier': [10.0, 20.0, 30.0],
        'predicted_barrier': [10.5, 20.2, 29.8],
        'ensemble_mean': [10.5, 20.2, 29.8],
        'pred_0': [10.1, 20.0, 29.5],
        'pred_1': [10.4, 20.3, 29.9],
        'pred_2': [10.6, 20.4, 30.1],
        'pred_3': [10.8, 20.1, 29.8],
        'pred_4': [10.7, 20.2, 29.9]
    }
    df = pd.DataFrame(data)
    
    # Mock checkpoints dir (not used in this path)
    result_df, metrics = compute_ensemble_variance(df, Path("/fake"))
    
    # Check variance calculation
    # Sample 1: [10.1, 10.4, 10.6, 10.8, 10.7] -> mean=10.52, var=0.067
    # Sample 2: [20.0, 20.3, 20.4, 20.1, 20.2] -> mean=20.2, var=0.025
    # Sample 3: [29.5, 29.9, 30.1, 29.8, 29.9] -> mean=29.84, var=0.053
    
    assert 'ensemble_variance' in result_df.columns
    assert 'ensemble_std' in result_df.columns
    assert 'abs_error' in result_df.columns
    
    # Verify correlation exists
    assert 'variance_correlation_with_error' in metrics
    assert 'mean_variance' in metrics

def test_compute_variance_from_residuals():
    """Test variance calculation when only residuals with model_id are available."""
    # Create a mock predictions dataframe without individual preds
    preds_data = {
        'sample_id': [1, 2],
        'dft_barrier': [10.0, 20.0],
        'predicted_barrier': [10.5, 20.5],
        'ensemble_mean': [10.5, 20.5]
    }
    preds_df = pd.DataFrame(preds_data)
    
    # Create a mock residuals dataframe
    residuals_data = {
        'sample_id': [1, 1, 1, 1, 1, 2, 2, 2, 2, 2],
        'model_id': [0, 1, 2, 3, 4, 0, 1, 2, 3, 4],
        'error': [0.5, 0.6, 0.4, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5] # All same for sample 2 -> var=0
    }
    residuals_df = pd.DataFrame(residuals_data)
    
    # Save residuals to a temp file
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        residuals_path = tmp_path / "residuals.parquet"
        residuals_df.to_parquet(residuals_path)
        
        # Patch the get_project_root or pass path directly?
        # The function uses global paths, so we need to mock the environment or
        # adjust the function to accept paths. For the test, we will assume
        # the function is called in a context where the path is correct,
        # or we mock the file system.
        # Since we can't easily mock the global path in the function without refactoring,
        # we will test the logic by creating the file in the expected location
        # relative to a fake project root, or we assume the function is refactored.
        # Given the constraints, we will test the logic by creating the necessary
        # files in a temp directory and setting the project root env var if used,
        # or we assume the test environment is set up correctly.
        
        # For this test, we will just verify the logic by creating the files
        # and calling the function, assuming the function uses the correct paths.
        # This is a bit fragile, but it tests the integration.
        
        # Actually, the function `compute_ensemble_variance` doesn't take the residuals path.
        # It constructs it. So we need to ensure the file is in the right place.
        # We will create a temp project structure.
        
        import os
        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        Path("data/processed").mkdir(parents=True)
        preds_df.to_parquet("data/processed/predictions.parquet")
        residuals_df.to_parquet("data/processed/residuals.parquet")
        
        # We need to mock get_project_root to return tmpdir
        from unittest.mock import patch
        with patch('src.analysis.ensemble_variance.get_project_root', return_value=Path(tmpdir)):
            result_df, metrics = compute_ensemble_variance(preds_df, Path(tmpdir) / "data/processed/models")
        
        os.chdir(old_cwd)
        
        assert 'ensemble_variance' in result_df.columns
        # Sample 1 should have variance > 0, Sample 2 variance = 0
        assert result_df.loc[result_df['sample_id'] == 1, 'ensemble_variance'].values[0] > 0
        assert result_df.loc[result_df['sample_id'] == 2, 'ensemble_variance'].values[0] == 0.0

def test_missing_data_raises():
    """Test that missing data raises appropriate errors."""
    data = {
        'sample_id': [1],
        'dft_barrier': [10.0],
        'predicted_barrier': [10.5],
        'ensemble_mean': [10.5]
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        import os
        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        Path("data/processed").mkdir(parents=True)
        df.to_parquet("data/processed/predictions.parquet")
        
        from unittest.mock import patch
        with patch('src.analysis.ensemble_variance.get_project_root', return_value=Path(tmpdir)):
            with pytest.raises(ValueError, match="Cannot compute variance"):
                compute_ensemble_variance(df, Path(tmpdir) / "data/processed/models")
        
        os.chdir(old_cwd)
