import os
import sys
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Mock the config to use temp directories
import src.config
import src.models.evaluate

@pytest.fixture
def temp_data_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create structure
        data_root = Path(tmpdir) / "data"
        processed = data_root / "processed"
        models = data_root / "models"
        processed.mkdir(parents=True)
        models.mkdir(parents=True)
        
        # Mock config functions temporarily
        original_get_processed = src.config.get_processed_data_dir
        original_get_model = src.config.get_model_dir
        original_get_data_root = src.config.get_data_root
        
        src.config.get_processed_data_dir = lambda: str(processed)
        src.config.get_model_dir = lambda: str(models)
        src.config.get_data_root = lambda: str(data_root)
        
        yield {
            "data_root": str(data_root),
            "processed": str(processed),
            "models": str(models)
        }
        
        # Restore
        src.config.get_processed_data_dir = original_get_processed
        src.config.get_model_dir = original_get_model
        src.config.get_data_root = original_get_data_root

def test_compute_mean_predictor_metrics(temp_data_dirs):
    """Test that Mean Predictor calculates correct RMSE and R2."""
    from src.models.evaluate import compute_mean_predictor_metrics
    
    # Create mock data
    df = pd.DataFrame({
        'dimension': ['A', 'A', 'A'],
        'human_score': [10.0, 20.0, 30.0]
    })
    
    rmse, r2 = compute_mean_predictor_metrics(df, 'A')
    
    # Mean = 20.0
    # Errors: -10, 0, 10 -> Squared: 100, 0, 100 -> MSE = 200/3 = 66.66
    # RMSE = sqrt(66.66) = 8.165
    expected_rmse = np.sqrt(200/3)
    
    # R2 for mean predictor should be 0.0
    expected_r2 = 0.0
    
    assert np.isclose(rmse, expected_rmse, atol=0.01)
    assert np.isclose(r2, expected_r2, atol=0.01)

def test_compute_shuffled_feature_metrics(temp_data_dirs):
    """Test that Shuffled Features baseline runs and returns values."""
    from src.models.evaluate import compute_shuffled_feature_metrics
    
    df = pd.DataFrame({
        'dimension': ['B', 'B', 'B'],
        'human_score': [5.0, 15.0, 25.0]
    })
    
    rmse, r2 = compute_shuffled_feature_metrics(df, 'B')
    
    # Should not raise
    assert isinstance(rmse, float)
    assert isinstance(r2, float)
    # RMSE should be roughly close to std(y) since it predicts mean + noise
    std_y = np.std(df['human_score'])
    assert rmse > 0.0

def test_run_baseline_comparisons_creates_file(temp_data_dirs):
    """Test that T019 main creates the output file."""
    from src.models.evaluate import run_baseline_comparisons
    import src.utils
    
    # Create mock scores.csv
    scores_path = os.path.join(temp_data_dirs["processed"], "scores.csv")
    scores_df = pd.DataFrame({
        'clip_id': ['1', '2', '3', '4', '5'],
        'dimension': ['Dim1', 'Dim1', 'Dim2', 'Dim2', 'Dim2'],
        'human_score': [10.0, 20.0, 5.0, 15.0, 25.0],
        'vlm_proxy_score': [10.0, 20.0, 5.0, 15.0, 25.0]
    })
    scores_df.to_csv(scores_path, index=False)
    
    # Run
    run_baseline_comparisons()
    
    # Check output
    output_path = os.path.join(temp_data_dirs["data_root"], "baseline_results.csv")
    assert os.path.exists(output_path)
    
    result_df = pd.read_csv(output_path)
    assert 'dimension' in result_df.columns
    assert 'predictor_type' in result_df.columns
    assert 'rmse' in result_df.columns
    assert 'r2' in result_df.columns
    
    # Check that we have entries for Dim1 and Dim2
    assert 'Dim1' in result_df['dimension'].values
    assert 'Dim2' in result_df['dimension'].values