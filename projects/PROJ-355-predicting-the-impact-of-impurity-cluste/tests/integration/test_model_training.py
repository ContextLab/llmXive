"""Integration test for model training and evaluation."""
import pytest
import sys
import os
import pandas as pd
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.modeling.train import main as train_main
from code.config import get_data_paths

@pytest.mark.integration
def test_model_training_integration():
    """
    Integration test: Train model on processed data and verify metrics output.
    """
    data_paths = get_data_paths()
    processed_dir = data_paths['processed']
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)

    # Check if input data exists
    descriptors_path = processed_dir / "descriptors.csv"
    energies_path = processed_dir / "segregation_energies.csv"

    if not descriptors_path.exists() or not energies_path.exists():
        pytest.skip("Input data files not found. Run US1 pipeline first.")

    # Run training
    try:
        train_main()
        
        # Verify metrics output
        metrics_path = results_dir / "metrics.json"
        assert metrics_path.exists(), "metrics.json not created"
        
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
            
        assert 'r2' in metrics, "R2 metric missing"
        assert 'rmse' in metrics, "RMSE metric missing"
        
    except Exception as e:
        if "DATA_UNAVAILABLE" in str(e) or "No data" in str(e):
            pytest.skip("Insufficient data for training")
        else:
            raise e
