import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

from . import logger

module_logger = logging.getLogger(__name__)

def load_processed_data(path: str = "data/processed/step_final_cleaned.csv") -> pd.DataFrame:
    """Load processed data."""
    return pd.read_csv(path)

def load_best_model(path: str = "data/models/best_model.pkl"):
    """Load the best model."""
    if not Path(path).exists():
        raise FileNotFoundError(f"Best model not found: {path}")
    return joblib.load(path)

def load_model_metrics(path: str = "data/results/model_metrics.json") -> Dict[str, Any]:
    """Load model metrics."""
    with open(path, 'r') as f:
        return json.load(f)

def load_baseline_metrics(path: str = "data/results/baseline_metrics.json") -> Dict[str, float]:
    """Load baseline metrics."""
    with open(path, 'r') as f:
        return json.load(f)

def train_leakage_check_model(df: pd.DataFrame, target: str = 'weibull_modulus') -> Any:
    """Train a model excluding 'primary_anion_cation_group' feature."""
    feature_cols = [c for c in df.columns if c not in [target, 'primary_anion_cation_group']]
    X = df[feature_cols]
    y = df[target]
    
    model = RandomForestRegressor(random_state=42, n_jobs=-1)
    model.fit(X, y)
    
    return model, X, y, feature_cols

def check_leakage(df: pd.DataFrame, target: str = 'weibull_modulus') -> Dict[str, Any]:
    """Check for data leakage by comparing performance with and without group feature."""
    # Load full model (with group feature)
    full_model = load_best_model()
    full_metrics = load_model_metrics()
    full_mae = full_metrics.get('rf', {}).get('mae', 0) if 'rf' in full_metrics else full_metrics.get('best_rf_mae', 0)
    
    # Train leakage check model (without group feature)
    leakage_model, X_leak, y_leak, feature_cols = train_leakage_check_model(df, target)
    y_pred_leak = leakage_model.predict(X_leak)
    leak_mae = mean_absolute_error(y_leak, y_pred_leak)
    
    # Compare
    mae_diff = leak_mae - full_mae
    mae_diff_pct = (mae_diff / full_mae * 100) if full_mae != 0 else 0
    
    # Flag if performance drop is small (< 10% increase in MAE)
    potential_leakage = mae_diff_pct < 10
    
    report = {
        "full_model_mae": float(full_mae),
        "leakage_check_model_mae": float(leak_mae),
        "mae_difference": float(mae_diff),
        "mae_difference_pct": float(mae_diff_pct),
        "potential_leakage": potential_leakage,
        "warning": "Potential Leakage detected" if potential_leakage else "No significant leakage detected",
        "features_used": feature_cols
    }
    
    # Save report
    output_path = Path("data/results/leakage_check.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Also save the leakage check model
    model_path = Path("data/models/leakage_check_model.pkl")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(leakage_model, model_path)
    
    module_logger.info(f"Leakage check completed: {report['warning']}")
    return report

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """Compute VIF for all predictors."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    vif_data = {}
    X = df[features]
    
    for i, feature in enumerate(features):
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data[feature] = float(vif)
        except Exception:
            vif_data[feature] = float('inf')
    
    return vif_data

def group_correlated_features(df: pd.DataFrame, threshold: float = 0.8) -> List[List[str]]:
    """Cluster highly correlated features."""
    corr_matrix = df.corr().abs()
    clusters = []
    used = set()
    
    for i, col1 in enumerate(corr_matrix.columns):
        if col1 in used:
            continue
        cluster = [col1]
        for j, col2 in enumerate(corr_matrix.columns):
            if i != j and col2 not in used:
                if corr_matrix.loc[col1, col2] > threshold:
                    cluster.append(col2)
                    used.add(col2)
        clusters.append(cluster)
        used.add(col1)
    
    return clusters

def main():
    """Main entry point for diagnostics."""
    module_logger.info("Diagnostics module loaded")

if __name__ == "__main__":
    main()
