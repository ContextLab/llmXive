import pandas as pd
import numpy as np
import pytest
import math
from pathlib import Path
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analyser import compute_regression_residuals, aggregate_log_variance
from code.config import RESULTS_DIR, RAW_EVALUATIONS_FILE

def create_test_data():
    """Create synthetic test data for residuals calculation."""
    # Create a mock dataset_properties.csv
    props_data = {
        'dataset_id': [1, 2, 3, 4, 5],
        'n_samples': [1000, 2000, 5000, 10000, 20000],
        'n_features': [10, 20, 30, 40, 50]
    }
    props_df = pd.DataFrame(props_data)
    props_path = Path("data/raw/dataset_properties.csv")
    props_path.parent.mkdir(parents=True, exist_ok=True)
    props_df.to_csv(props_path, index=False)

    # Create mock raw evaluations
    # We need multiple repeats for each dataset/model to calculate std
    raw_data = []
    for d_id in [1, 2, 3, 4, 5]:
        for m_name in ["LogisticRegression", "RandomForest"]:
            for repeat in range(10):
                # Generate some random accuracy and f1 scores
                # Introduce variance based on sample size to test regression
                base_acc = 0.8
                noise = np.random.normal(0, 0.05)
                raw_data.append({
                    'dataset_id': d_id,
                    'model_name': m_name,
                    'fold_id': 1,
                    'repeat_id': repeat,
                    'accuracy': base_acc + noise,
                    'f1_score': base_acc + noise
                })
    
    raw_df = pd.DataFrame(raw_data)
    raw_path = RESULTS_DIR / RAW_EVALUATIONS_FILE
    raw_df.to_csv(raw_path, index=False)
    return raw_df, props_df

def test_compute_regression_residuals():
    """Test that residuals are computed correctly."""
    # Setup
    create_test_data()
    
    # Run
    result = compute_regression_residuals()
    
    # Assert
    assert not result.empty, "Residuals dataframe should not be empty"
    assert 'residual' in result.columns, "Result should contain 'residual' column"
    assert 'dataset_id' in result.columns, "Result should contain 'dataset_id' column"
    assert 'model_name' in result.columns, "Result should contain 'model_name' column"
    
    # Check that residuals are calculated (observed - predicted)
    # We can't check exact values without knowing the exact regression, 
    # but we can check they are numeric
    assert result['residual'].dtype in [np.float64, np.float32], "Residuals should be numeric"
    
    # Check file was written
    output_path = RESULTS_DIR / "regression_residuals.csv"
    assert output_path.exists(), "Residuals file should be written to disk"

def test_aggregate_log_variance_zero_std():
    """Test that log-variance handles zero standard deviation."""
    data = pd.DataFrame({
        'dataset_id': [1, 1],
        'model_name': ['LR', 'LR'],
        'accuracy': [0.9, 0.9], # Zero variance
        'f1_score': [0.9, 0.9]
    })
    result = aggregate_log_variance(data)
    assert result['log_variance_accuracy'].iloc[0] == -999.0, "Zero variance should result in -999"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])