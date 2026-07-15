"""
Integration test for T022: Full training pipeline execution.

Verifies that the training script runs end-to-end and produces artifacts.
"""
import os
import sys
import json
import pickle
import tempfile
from pathlib import Path
import shutil
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.train import main

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def setup_test_data(temp_data_dir):
    """Set up minimal test data structure."""
    # Create necessary directories
    data_processed = temp_data_dir / "data" / "processed"
    data_processed.mkdir(parents=True, exist_ok=True)
    
    artifacts_models = temp_data_dir / "artifacts" / "models"
    artifacts_models.mkdir(parents=True, exist_ok=True)
    
    artifacts_metrics = temp_data_dir / "artifacts" / "metrics"
    artifacts_metrics.mkdir(parents=True, exist_ok=True)
    
    # Create a minimal cleaned dataset
    import pandas as pd
    import numpy as np
    
    np.random.seed(42)
    n_samples = 50
    n_families = 5
    
    data = {
        'alloy_id': [f'MG_{i}' for i in range(n_samples)],
        'composition': ['Fe40Ni40B20'] * n_samples,
        'Tg': np.random.rand(n_samples) * 100 + 300,
        'family': np.repeat([f'Family_{i}' for i in range(n_families)], n_samples // n_families),
        'radius_mismatch': np.random.rand(n_samples),
        'electronegativity_diff': np.random.rand(n_samples),
        'vec': np.random.rand(n_samples) * 2 + 7,
        'weighted_mean_radius': np.random.rand(n_samples) * 2 + 1
    }
    
    df = pd.DataFrame(data)
    csv_path = data_processed / "cleaned_mg.csv"
    df.to_csv(csv_path, index=False)
    
    # Create config file
    config_path = temp_data_dir / "code" / "config" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_content = """
    seed: 42
    max_runtime_hours: 6
    max_ram_gb: 7
    data:
      raw_dir: "data/raw"
      processed_dir: "data/processed"
      input_file: "cleaned_mg.csv"
    artifacts:
      models_dir: "artifacts/models"
      metrics_dir: "artifacts/metrics"
      reports_dir: "artifacts/reports"
    """
    config_path.write_text(config_content)
    
    return temp_data_dir

@pytest.mark.integration
def test_training_pipeline_execution(setup_test_data):
    """Test that the training pipeline runs and produces artifacts."""
    # Change to temp directory to simulate running from project root
    original_cwd = os.getcwd()
    os.chdir(setup_test_data)
    
    try:
        # Run main
        result = main()
        
        # Check exit code
        assert result == 0, "Training pipeline failed"
        
        # Check model artifact exists
        model_path = setup_test_data / "artifacts" / "models" / "best_model.pkl"
        assert model_path.exists(), "Model artifact not created"
        
        # Check metrics artifact exists
        metrics_path = setup_test_data / "artifacts" / "metrics" / "training_metrics.json"
        assert metrics_path.exists(), "Metrics artifact not created"
        
        # Validate model content
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        assert 'model' in model_data, "Model not saved in pickle"
        assert 'feature_cols' in model_data, "Feature columns not saved"
        assert 'params' in model_data, "Hyperparameters not saved"
        
        # Validate metrics content
        with open(metrics_path, 'r') as f:
            metrics_data = json.load(f)
        
        assert 'r2_mean' in metrics_data, "R2 metric missing"
        assert 'mae_mean' in metrics_data, "MAE metric missing"
        assert 'hyperparameters' in metrics_data, "Hyperparameters missing"
        assert 'feature_importances' in metrics_data, "Feature importances missing"
        
        # Validate R2 is reasonable (not -inf or nan)
        assert isinstance(metrics_data['r2_mean'], (int, float)), "R2 is not a number"
        assert not (metrics_data['r2_mean'] != metrics_data['r2_mean']), "R2 is NaN"
        
    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])