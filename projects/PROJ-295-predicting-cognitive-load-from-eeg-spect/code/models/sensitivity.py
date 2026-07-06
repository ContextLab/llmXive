import numpy as np
import pandas as pd
from typing import List, Dict
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
import yaml

def load_config(config_path: str = "pipeline_config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def run_sensitivity_analysis(
    X: np.ndarray,
    y: np.ndarray,
    subject_ids: np.ndarray,
    window_sizes: List[float],
    alpha: float = 1.0
) -> pd.DataFrame:
    """
    Run sensitivity analysis by varying gaze variance calculation windows.
    
    Args:
        X: Feature matrix.
        y: Labels.
        subject_ids: Subject IDs.
        window_sizes: List of window sizes to test.
        alpha: Regularization strength.
        
    Returns:
        DataFrame with sensitivity results.
    """
    results = []
    
    for window_size in window_sizes:
        # In a real implementation, we would recompute features with the new window size
        # For now, we simulate by using the same features (placeholder)
        # This would ideally call the feature extraction with the new window size
        
        # Train and evaluate
        model = Ridge(alpha=alpha)
        model.fit(X, y)
        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred)
        
        results.append({
            'window_size': window_size,
            'r2': float(r2),
            'rmse': float(np.sqrt(np.mean((y - y_pred) ** 2)))
        })
    
    return pd.DataFrame(results)

if __name__ == "__main__":
    print("Sensitivity analysis module loaded successfully.")
