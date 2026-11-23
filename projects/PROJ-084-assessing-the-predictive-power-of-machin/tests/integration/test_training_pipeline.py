"""
Integration test for the training pipeline (T024).
Tests that the training script runs end-to-end on a small subset
and produces the expected output artifacts.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import shutil
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from modeling.train import train_random_forest_grid_search, main
from utils.io import save_parquet

@pytest.fixture
def sample_data(tmp_path):
    """Create a small synthetic dataset for testing purposes only in CI."""
    # Note: This is a TEST FIXTURE for integration testing.
    # It generates a tiny, deterministic dataset to verify the pipeline logic.
    # It does NOT replace real data for the actual run.
    
    n_samples = 50
    n_features = 20  # Small fingerprint size for test speed
    
    np.random.seed(42)
    
    # Generate random fingerprints
    reactants_fp = np.random.randint(0, 2, (n_samples, n_features // 2)).tolist()
    reagents_fp = np.random.randint(0, 2, (n_samples, n_features // 2)).tolist()
    
    # Generate synthetic yields (0-100)
    yields = np.random.uniform(0, 100, n_samples).tolist()
    
    df = pd.DataFrame({
        'reactants_fp': reactants_fp,
        'reagents_fp': reagents_fp,
        'yield_pct': yields,
        'reaction_class': ['A'] * n_samples,
        'id': range(n_samples)
    })
    
    # Create split indices
    split_data = []
    for i in range(n_samples):
        if i < 30:
            split = 'train'
        elif i < 40:
            split = 'val'
        else:
            split = 'test'
        split_data.append({'id': i, 'split': split})
    
    split_df = pd.DataFrame(split_data)
    
    # Save to tmp_path
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    save_parquet(df, data_dir / "cleaned_reactions.parquet")
    save_parquet(split_df, data_dir / "split_indices.parquet")
    
    return tmp_path

def test_train_pipeline_execution(sample_data):
    """
    Test that the main training function runs without error and produces outputs.
    """
    # Mock the paths in the main function by temporarily changing the working directory
    # or by patching the paths. Since main() uses hardcoded paths relative to root,
    # we will run it in the context of the temp directory.
    
    original_cwd = Path.cwd()
    try:
        # Change to the temp directory root (which contains 'data' folder)
        os.chdir(sample_data)
        
        # Run the main function
        # We expect it to run on the tiny dataset created by the fixture
        main()
        
        # Check that output files were created
        output_dir = Path("data/results/best_models")
        
        assert output_dir.exists(), "Output directory was not created."
        assert (output_dir / "rf_best_model.pkl").exists(), "Model file not found."
        assert (output_dir / "rf_metrics.json").exists(), "Metrics file not found."
        
        # Verify metrics content
        with open(output_dir / "rf_metrics.json", 'r') as f:
            metrics = json.load(f)
        
        assert 'r2' in metrics, "R2 metric missing."
        assert 'rmse' in metrics, "RMSE metric missing."
        assert 'mae' in metrics, "MAE metric missing."
        assert 'best_params' in metrics, "Best params missing."
        
        # Verify best_params structure
        assert 'n_estimators' in metrics['best_params']
        assert 'max_depth' in metrics['best_params']
        
    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
