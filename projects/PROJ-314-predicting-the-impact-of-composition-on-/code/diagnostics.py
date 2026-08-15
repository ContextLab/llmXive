import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.linear_model import LinearRegression
import joblib

logger = logging.getLogger(__name__)

def load_processed_data(filepath: str = 'data/processed/step_final_cleaned.csv') -> pd.DataFrame:
    """Load processed data."""
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Processed data file not found: {filepath}")
    return pd.read_csv(filepath)

def load_best_model(filepath: str = 'data/models/best_model.pkl'):
    """Load the best model."""
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Best model file not found: {filepath}")
    return joblib.load(filepath)

def load_model_metrics(filepath: str = 'data/results/model_metrics.json') -> Dict[str, Any]:
    """Load model metrics."""
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Model metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def load_baseline_metrics(filepath: str = 'data/results/baseline_metrics.json') -> Dict[str, Any]:
    """Load baseline metrics."""
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Baseline metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def train_leakage_check_model(df: pd.DataFrame, feature_cols: List[str], target_col: str = 'weibull_modulus', exclude_feature: str = 'primary_anion_cation_group'):
    """
    Train a model excluding the 'primary_anion_cation_group' feature to check for leakage.
    """
    logger.info("Training leakage check model...")
    
    if exclude_feature in feature_cols:
        feature_cols_leakage = [f for f in feature_cols if f != exclude_feature]
    else:
        feature_cols_leakage = feature_cols
    
    if not feature_cols_leakage:
        logger.warning("No features left after excluding leakage feature.")
        return None
    
    X = df[feature_cols_leakage]
    y = df[target_col]
    
    model = RandomForestRegressor(random_state=42)
    model.fit(X, y)
    
    # Evaluate
    predictions = model.predict(X)
    mae = mean_absolute_error(y, predictions)
    
    metrics = {
        "mae": mae,
        "features_used": feature_cols_leakage,
        "excluded_feature": exclude_feature
    }
    
    output_path = 'data/models/leakage_check_model.pkl'
    joblib.dump(model, output_path)
    logger.info(f"Leakage check model saved to {output_path}")
    
    return model, metrics

def check_leakage(original_mae: float, leakage_mae: float) -> Dict[str, Any]:
    """
    Check for descriptor sufficiency by comparing MAE with and without the proxy feature.
    """
    logger.info("Checking descriptor sufficiency...")
    
    if original_mae is None or leakage_mae is None:
        logger.error("Missing MAE values for leakage check.")
        return {"status": "error", "message": "Missing MAE values"}
    
    mae_increase = ((leakage_mae - original_mae) / original_mae) * 100
    
    if mae_increase >= 10:
        status = "POTENTIAL LEAKAGE"
    else:
        status = "DESCRIPTORS SUFFICIENT"
    
    report = {
        "original_mae": original_mae,
        "leakage_mae": leakage_mae,
        "mae_increase_percent": mae_increase,
        "status": status
    }
    
    output_path = 'data/results/descriptor_sufficiency.json'
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Descriptor sufficiency report saved to {output_path}")
    
    return report

def load_leakage_check_model(filepath: str = 'data/models/leakage_check_model.pkl'):
    """Load leakage check model."""
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Leakage check model file not found: {filepath}")
    return joblib.load(filepath)

def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for all predictors.
    """
    logger.info("Calculating VIF...")
    vif_data = {}
    
    for i, feature in enumerate(feature_cols):
        X = df[feature_cols[:i] + feature_cols[i+1:]]
        y = df[feature]
        
        if X.shape[1] == 0:
            vif_data[feature] = 1.0
            continue
        
        model = LinearRegression()
        model.fit(X, y)
        r_squared = model.score(X, y)
        
        if r_squared >= 1:
            vif_data[feature] = float('inf')
        else:
            vif_data[feature] = 1 / (1 - r_squared)
    
    output_path = 'data/results/vif_scores.json'
    with open(output_path, 'w') as f:
        json.dump(vif_data, f, indent=2)
    logger.info(f"VIF scores saved to {output_path}")
    
    return vif_data

def group_correlated_features(vif_scores: Dict[str, float], threshold: float = 5.0) -> List[List[str]]:
    """
    Cluster highly correlated features (VIF > threshold).
    """
    logger.info("Grouping correlated features...")
    high_vif_features = [f for f, v in vif_scores.items() if v > threshold]
    
    # Simple grouping: all high VIF features in one group for now
    # In a real scenario, we would use clustering algorithms
    if high_vif_features:
        return [high_vif_features]
    return []

def main():
    """Main entry point for diagnostics."""
    try:
        # Load data
        df = load_processed_data()
        
        # Define feature columns
        exclude_cols = ['composition', 'weibull_modulus', 'sample_count', 'is_range_flag', 'range_original', 'primary_anion_cation_group', 'sintering_temp', 'is_imputed']
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        # Load model metrics
        metrics = load_model_metrics()
        original_mae = metrics.get('mae')
        
        # Train leakage check model
        leakage_model, leakage_metrics = train_leakage_check_model(df, feature_cols)
        if leakage_model is None:
            logger.error("Failed to train leakage check model.")
            sys.exit(1)
        
        leakage_mae = leakage_metrics.get('mae')
        
        # Check leakage
        check_leakage(original_mae, leakage_mae)
        
        # Calculate VIF
        vif_scores = calculate_vif(df, feature_cols)
        
        # Group correlated features
        groups = group_correlated_features(vif_scores)
        
        logger.info("Diagnostics completed successfully.")
        
    except Exception as e:
        logger.error(f"Diagnostics failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
