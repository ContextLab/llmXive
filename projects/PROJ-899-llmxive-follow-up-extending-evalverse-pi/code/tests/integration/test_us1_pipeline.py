import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path

# Add code to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.models.train import load_processed_features, prepare_data, train_ridge
from src.models.evaluate import run_baseline_comparisons, calculate_metrics

def test_us1_pipeline_sample():
    """
    Integration test: Run a simplified version of US1 pipeline on a small sample.
    """
    # 1. Create sample data
    sample_data = pd.DataFrame({
        'clip_id': [f'c{i}' for i in range(10)],
        'human_score': np.random.rand(10),
        'optical_flow_mean': np.random.rand(10) * 100,
        'optical_flow_var': np.random.rand(10),
        'audio_spectral': np.random.rand(10) * 100,
        'audio_zcr': np.random.rand(10)
    })

    # 2. Mock loading data (since we don't have real files)
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "features.csv")
        sample_data.to_csv(csv_path, index=False)
        
        # Patch the load function to use our temp file
        import src.models.train as train_module
        original_load = train_module.load_processed_features
        train_module.load_processed_features = lambda file_path=None: pd.read_csv(csv_path)

        try:
            # 3. Run pipeline steps
            df = load_processed_features()
            X, y, cols = prepare_data(df)
            model = train_ridge(X, y)
            
            # 4. Verify model trained
            assert hasattr(model, 'coef_')
            
            # 5. Run baseline comparisons
            baseline_results = run_baseline_comparisons(df)
            assert len(baseline_results) == 2
            assert 'mean_predictor' in baseline_results['baseline_type'].values
        finally:
            train_module.load_processed_features = original_load
