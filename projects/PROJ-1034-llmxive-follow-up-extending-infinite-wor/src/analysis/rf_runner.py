"""
Random Forest Feature Importance Analyzer.
"""
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import logging

logger = logging.getLogger(__name__)

def run_rf_analysis(data: pd.DataFrame, target: str = "coherence_score") -> dict:
    """
    Run Random Forest to determine feature importance.
    """
    if target not in data.columns:
        raise ValueError(f"Target column '{target}' not found in data")
    
    features = [col for col in data.columns if col != target and col != "step"]
    if not features:
        return {"error": "No features found"}
    
    X = data[features]
    y = data[target]
    
    rf = RandomForestRegressor(n_estimators=10, random_state=42)
    rf.fit(X, y)
    
    importance = dict(zip(features, rf.feature_importances_.tolist()))
    return {"feature_importance": importance}
