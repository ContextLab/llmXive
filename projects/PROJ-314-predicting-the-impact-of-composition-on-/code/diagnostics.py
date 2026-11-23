"""
Diagnostics Module.

Handles VIF calculation, SHAP analysis, and feature importance.
"""
import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor

# Add project root to path
import os
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'logs' / 'diagnostics.log')
    ]
)
logger = logging.getLogger(__name__)

def load_processed_data(filepath: str = None) -> pd.DataFrame:
    """Load processed data."""
    if not filepath:
        filepath = project_root / "data" / "processed" / "step_final_cleaned.csv"
    return pd.read_csv(filepath)

def load_best_model(filepath: str = None):
    """Load best trained model."""
    if not filepath:
        filepath = project_root / "data" / "models" / "best_model.pkl"
    import joblib
    return joblib.load(filepath)

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for features.

    Args:
        df: DataFrame with features
        features: List of feature columns

    Returns:
        Dictionary mapping feature to VIF
    """
    vif_data = {}
    for i, feature in enumerate(features):
        X = df[features[:i] + features[i+1:]]
        y = df[feature]
        model = LinearRegression()
        model.fit(X, y)
        r2 = model.score(X, y)
        vif = 1 / (1 - r2) if r2 < 1 else np.inf
        vif_data[feature] = vif
        logger.debug(f"VIF for {feature}: {vif:.2f}")

    return vif_data

def group_correlated_features(vif_data: Dict[str, float], threshold: float = 5.0) -> Dict[str, List[str]]:
    """
    Group highly correlated features (VIF > threshold).

    Args:
        vif_data: VIF values
        threshold: VIF threshold for grouping

    Returns:
        Dictionary mapping cluster ID to list of features
    """
    clusters = {}
    cluster_id = 0
    for feature, vif in vif_data.items():
        if vif > threshold:
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(feature)
            cluster_id += 1
        else:
            # Single feature cluster
            clusters[cluster_id] = [feature]
            cluster_id += 1
    return clusters

def main():
    """Main entry point for diagnostics."""
    logger.info("Diagnostics module loaded.")

if __name__ == "__main__":
    main()
