import os
import json
import logging
import csv
import pickle
import random
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import StratifiedKFold, cross_validate
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant
import matplotlib.pyplot as plt

# Constants
RESULTS_DIR = Path("results")
DATA_PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("models")
LOG_FILE = RESULTS_DIR / "power_analysis.log"
METRICS_CSV = DATA_PROCESSED_DIR / "metrics.csv"
FILTERED_FEATURES_CSV = DATA_PROCESSED_DIR / "filtered_features.csv"
MODEL_PATH = MODELS_DIR / "thermal_predictor.pkl"
PERFORMANCE_JSON = RESULTS_DIR / "model_performance.json"

def setup_analysis_logger() -> logging.Logger:
    """Setup the analysis logger."""
    logger = logging.getLogger("analysis")
    logger.setLevel(logging.DEBUG)
    
    # File handler
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

def load_metrics_csv() -> pd.DataFrame:
    """Load the metrics CSV file."""
    if not METRICS_CSV.exists():
        raise FileNotFoundError(f"Metrics file not found: {METRICS_CSV}")
    return pd.read_csv(METRICS_CSV)

def get_network_metrics(df: pd.DataFrame) -> List[str]:
    """Get the list of network metric columns."""
    # Based on T013: average degree, average shortest path length, clustering coefficient
    # Also includes density as diagnostic but we filter based on VIF
    possible_metrics = ['avg_degree', 'avg_shortest_path', 'clustering_coeff', 'density']
    return [col for col in possible_metrics if col in df.columns]

def get_thermal_conductivity_col(df: pd.DataFrame) -> str:
    """Get the thermal conductivity column name."""
    cols = [c for c in df.columns if 'thermal' in c.lower() and 'conductivity' in c.lower()]
    if not cols:
        # Fallback based on T015 naming convention
        cols = [c for c in df.columns if 'mean_thermal' in c.lower()]
    if not cols:
        raise ValueError("Thermal conductivity column not found in metrics CSV")
    return cols[0]

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """Calculate VIF for each feature."""
    if len(features) == 0:
        return {}
    
    X = df[features].dropna()
    if X.empty:
        return {f: float('inf') for f in features}
    
    # Add constant for OLS
    X_const = add_constant(X)
    
    vif_data = {}
    for i, col in enumerate(X_const.columns):
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X_const.values, i)
            vif_data[col] = vif
        except Exception as e:
            logging.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data[col] = float('inf')
    
    return vif_data

def log_vif_results(vif_data: Dict[str, float], logger: logging.Logger):
    """Log VIF results."""
    logger.info("VIF Analysis Results:")
    for feature, vif in vif_data.items():
        status = "EXCLUDED" if vif >= 5.0 else "KEPT"
        logger.info(f"  {feature}: VIF = {vif:.4f} [{status}]")

def generate_filtered_features_csv(df: pd.DataFrame, vif_data: Dict[str, float], target_col: str, logger: logging.Logger):
    """Generate filtered features CSV with only VIF < 5 features."""
    kept_features = [f for f, v in vif_data.items() if v < 5.0]
    
    # Create new dataframe with only kept features and target
    # Note: Target is NOT a feature, but we keep it for reference in the CSV
    # However, the requirement says "ONLY the columns for features with VIF < 5"
    # So we exclude the target from the feature set used for modeling
    filtered_df = df[kept_features].copy()
    
    # Save to CSV
    FILTERED_FEATURES_CSV.parent.mkdir(parents=True, exist_ok=True)
    filtered_df.to_csv(FILTERED_FEATURES_CSV, index=False)
    logger.info(f"Generated {FILTERED_FEATURES_CSV} with {len(kept_features)} features: {kept_features}")
    
    return kept_features

def train_linear_model(X: np.ndarray, y: np.ndarray, logger: logging.Logger) -> LinearRegression:
    """Train a linear regression model."""
    model = LinearRegression()
    model.fit(X, y)
    logger.info("Linear Regression model trained successfully.")
    return model

def run_stratified_cross_validation(df: pd.DataFrame, feature_cols: List[str], target_col: str, logger: logging.Logger) -> Dict[str, Any]:
    """Run stratified k-fold cross-validation."""
    if len(feature_cols) == 0:
        raise ValueError("No features available for training after VIF filtering.")
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Remove rows with NaN in features or target
    mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    X = X[mask]
    y = y[mask]
    
    if len(X) == 0:
        raise ValueError("No valid data points after removing NaN values.")
    
    # Create strata based on quantiles of y
    n_splits = 5
    n_strata = min(n_splits, len(np.unique(y)))
    if n_strata < 2:
        # If not enough unique values, use simple KFold
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        # Create dummy strata if unique values are too few
        strata = np.zeros(len(y), dtype=int)
        if len(np.unique(y)) == 1:
            strata = np.zeros(len(y), dtype=int)
        else:
            # Bin into 5 quantiles
            strata = pd.qcut(y, q=min(5, len(np.unique(y))), labels=False)
    else:
        strata = pd.qcut(y, q=min(5, len(np.unique(y))), labels=False)
    
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    # Run cross-validation
    cv_results = cross_validate(
        LinearRegression(),
        X, y,
        cv=skf,
        scoring=['r2', 'neg_root_mean_squared_error'],
        return_train_score=False
    )
    
    # Extract results
    r2_scores = cv_results['test_r2']
    rmse_scores = -cv_results['test_neg_root_mean_squared_error']  # Negate to get positive RMSE
    
    mean_r2 = float(np.mean(r2_scores))
    std_r2 = float(np.std(r2_scores))
    mean_rmse = float(np.mean(rmse_scores))
    std_rmse = float(np.std(rmse_scores))
    
    logger.info(f"Cross-validation completed: {n_splits} folds")
    logger.info(f"R²: mean = {mean_r2:.4f}, std = {std_r2:.4f}")
    logger.info(f"RMSE: mean = {mean_rmse:.4f}, std = {std_rmse:.4f}")
    
    return {
        'n_splits': n_splits,
        'r2_scores': r2_scores.tolist(),
        'rmse_scores': rmse_scores.tolist(),
        'mean_r2': mean_r2,
        'std_r2': std_r2,
        'mean_rmse': mean_rmse,
        'std_rmse': std_rmse,
        'r2_interpretation': None  # Will be set by T023/T024 logic
    }

def save_model_performance(results: Dict[str, Any], logger: logging.Logger):
    """Save model performance results to JSON."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(PERFORMANCE_JSON, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Model performance saved to {PERFORMANCE_JSON}")

def main():
    """Main entry point for the analysis pipeline."""
    logger = setup_analysis_logger()
    logger.info("Starting analysis pipeline...")
    
    try:
        # Load data
        df = load_metrics_csv()
        logger.info(f"Loaded metrics: {len(df)} rows")
        
        # Get network metrics and target
        network_metrics = get_network_metrics(df)
        target_col = get_thermal_conductivity_col(df)
        logger.info(f"Network metrics: {network_metrics}")
        logger.info(f"Target column: {target_col}")
        
        # Calculate VIF
        vif_data = calculate_vif(df, network_metrics)
        log_vif_results(vif_data, logger)
        
        # Generate filtered features
        feature_cols = generate_filtered_features_csv(df, vif_data, target_col, logger)
        
        if len(feature_cols) == 0:
            logger.error("No features remained after VIF filtering. Cannot train model.")
            return
        
        # Run cross-validation
        cv_results = run_stratified_cross_validation(df, feature_cols, target_col, logger)
        
        # Determine interpretation
        if cv_results['mean_r2'] < 0.30:
            cv_results['r2_interpretation'] = "Weak predictive power (R² < 0.30), consistent with null hypothesis."
            logger.info(cv_results['r2_interpretation'])
        else:
            cv_results['r2_interpretation'] = "Predictive power is moderate to strong (R² >= 0.30)."
            logger.info(cv_results['r2_interpretation'])
        
        # Save results
        save_model_performance(cv_results, logger)
        
        # Train final model on all data
        X = df[feature_cols].values
        y = df[target_col].values
        mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X = X[mask]
        y = y[mask]
        
        final_model = train_linear_model(X, y, logger)
        
        # Save model
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(final_model, f)
        logger.info(f"Final model saved to {MODEL_PATH}")
        
        logger.info("Analysis pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
