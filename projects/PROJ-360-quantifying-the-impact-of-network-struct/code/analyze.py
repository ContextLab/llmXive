import os
import json
import logging
import csv
import pickle
import random
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import r2_score, mean_squared_error

# Configuration
METRICS_CSV_PATH = "data/processed/metrics.csv"
FILTERED_FEATURES_CSV_PATH = "data/processed/filtered_features.csv"
POWER_ANALYSIS_LOG_PATH = "results/power_analysis.log"
MODEL_PATH = "models/thermal_predictor.pkl"
MODEL_PERFORMANCE_PATH = "results/model_performance.json"

def setup_analysis_logger(name: str, log_file: str) -> logging.Logger:
    """Setup a logger for the analysis module."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def load_metrics_csv() -> pd.DataFrame:
    """Load the metrics CSV file."""
    if not os.path.exists(METRICS_CSV_PATH):
        raise FileNotFoundError(f"Metrics file not found: {METRICS_CSV_PATH}")
    
    df = pd.read_csv(METRICS_CSV_PATH)
    
    # Handle comment lines in CSV if present
    if df.empty or df.columns[0].startswith('#'):
        # Re-read skipping comments if necessary
        df = pd.read_csv(METRICS_CSV_PATH, comment='#')
    
    return df

def get_network_metrics(df: pd.DataFrame) -> List[str]:
    """Extract network metric columns from the DataFrame."""
    # Based on T013, these are the network metrics
    network_metrics = ['avg_degree', 'avg_shortest_path', 'clustering_coefficient']
    return [col for col in network_metrics if col in df.columns]

def get_thermal_conductivity_col(df: pd.DataFrame) -> Optional[str]:
    """Identify the thermal conductivity column."""
    possible_cols = ['thermal_conductivity', 'mean_thermal_conductivity', 'k_avg']
    for col in possible_cols:
        if col in df.columns:
            return col
    # Fallback: look for any column with 'thermal' or 'k_' in name
    for col in df.columns:
        if 'thermal' in col.lower() or (col.startswith('k_') and col != 'k_x'):
            return col
    return None

def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for each feature."""
    if len(feature_cols) == 0:
        return {}
    
    # Extract features
    X = df[feature_cols].copy()
    
    # Handle constant features (VIF undefined)
    X = X.loc[:, (X != X.iloc[0]).any()]
    
    if X.empty:
        return {col: float('inf') for col in feature_cols}
    
    # Add constant for OLS
    X_const = add_constant(X)
    
    vif_values = {}
    for i, col in enumerate(X.columns):
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X_const.values, i)
            vif_values[col] = vif
        except Exception:
            vif_values[col] = float('inf')
    
    return vif_values

def log_vif_results(vif_values: Dict[str, float], logger: logging.Logger, log_file: str):
    """Log VIF results to the power analysis log file."""
    with open(log_file, 'a') as f:
        f.write("\n=== VIF Analysis Results ===\n")
        for feature, vif in vif_values.items():
            f.write(f"{feature}: {vif:.4f}\n")
        f.write("============================\n")
    
    logger.info("VIF analysis completed. Results logged to %s", log_file)

def generate_filtered_features_csv(df: pd.DataFrame, vif_values: Dict[str, float], 
                                 threshold: float = 5.0, logger: logging.Logger = None) -> pd.DataFrame:
    """
    Filter features based on VIF threshold.
    
    Args:
        df: DataFrame with all features
        vif_values: Dictionary mapping feature names to VIF values
        threshold: VIF threshold for filtering (default 5.0)
        logger: Logger instance
        
    Returns:
        DataFrame with only features having VIF < threshold
    """
    # Identify features to keep
    features_to_keep = []
    excluded_features = []
    
    for feature, vif in vif_values.items():
        if vif < threshold:
            features_to_keep.append(feature)
        else:
            excluded_features.append((feature, vif))
    
    # Log excluded features
    if logger:
        logger.info("Features excluded (VIF >= %.2f):", threshold)
        for feature, vif in excluded_features:
            logger.info("  - %s: VIF = %.4f", feature, vif)
    
    # Also log to power_analysis.log
    log_file = POWER_ANALYSIS_LOG_PATH
    with open(log_file, 'a') as f:
        f.write("\n=== VIF Filtering Results ===\n")
        f.write(f"Threshold: {threshold}\n")
        if excluded_features:
            f.write("Excluded features:\n")
            for feature, vif in excluded_features:
                f.write(f"  - {feature}: VIF = {vif:.4f}\n")
        else:
            f.write("No features excluded.\n")
        f.write(f"Kept features: {', '.join(features_to_keep)}\n")
        f.write("============================\n")
    
    # Create filtered DataFrame
    # Keep all original columns, but only include filtered feature columns
    # We need to preserve non-feature columns (like material_id, thermal_conductivity)
    filtered_cols = []
    
    # Add non-feature columns first
    for col in df.columns:
        if col not in vif_values:
            filtered_cols.append(col)
    
    # Add filtered feature columns
    filtered_cols.extend(features_to_keep)
    
    filtered_df = df[filtered_cols].copy()
    
    # Save to CSV
    filtered_df.to_csv(FILTERED_FEATURES_CSV_PATH, index=False)
    
    if logger:
        logger.info("Filtered features saved to %s", FILTERED_FEATURES_CSV_PATH)
        logger.info("Kept %d features: %s", len(features_to_keep), ', '.join(features_to_keep))
    
    return filtered_df

def train_linear_model(X: pd.DataFrame, y: pd.Series, logger: logging.Logger = None) -> LinearRegression:
    """Train a linear regression model."""
    model = LinearRegression()
    model.fit(X, y)
    
    if logger:
        logger.info("Linear regression model trained.")
        logger.info("Model R² score on training data: %.4f", model.score(X, y))
    
    return model

def run_stratified_cross_validation(df: pd.DataFrame, feature_cols: List[str], 
                                  target_col: str, n_splits: int = 5, 
                                  logger: logging.Logger = None) -> Dict[str, Any]:
    """
    Run stratified cross-validation for the linear regression model.
    
    Args:
        df: DataFrame with features and target
        feature_cols: List of feature column names
        target_col: Target column name
        n_splits: Number of CV folds
        logger: Logger instance
        
    Returns:
        Dictionary with CV results
    """
    X = df[feature_cols].copy()
    y = df[target_col].copy()
    
    # Create bins for stratification
    y_binned = pd.qcut(y, q=n_splits, labels=False, duplicates='drop')
    
    # Handle case where qcut fails (too few unique values)
    if len(np.unique(y_binned)) < 2:
        # Fallback to simple KFold if stratification not possible
        skf = StratifiedKFold(n_splits=min(n_splits, len(y)), shuffle=True, random_state=42)
        cv_results = cross_validate(
            LinearRegression(), X, y_binned, cv=skf,
            scoring=['r2', 'neg_mean_squared_error'],
            return_train_score=True
        )
    else:
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        cv_results = cross_validate(
            LinearRegression(), X, y_binned, cv=skf,
            scoring=['r2', 'neg_mean_squared_error'],
            return_train_score=True
        )
    
    # Extract results
    r2_scores = cv_results['test_r2']
    rmse_scores = np.sqrt(-cv_results['test_neg_mean_squared_error'])
    
    result = {
        'r2_scores': r2_scores.tolist(),
        'rmse_scores': rmse_scores.tolist(),
        'mean_r2': float(np.mean(r2_scores)),
        'std_r2': float(np.std(r2_scores)),
        'mean_rmse': float(np.mean(rmse_scores)),
        'std_rmse': float(np.std(rmse_scores)),
        'n_splits': n_splits,
        'r2_interpretation': None
    }
    
    # Add interpretation if mean R² < 0.30
    if result['mean_r2'] < 0.30:
        result['r2_interpretation'] = "Weak predictive power (R² < 0.30), consistent with null hypothesis."
    
    if logger:
        logger.info("Cross-validation completed.")
        logger.info("Mean R²: %.4f (±%.4f)", result['mean_r2'], result['std_r2'])
        logger.info("Mean RMSE: %.4f (±%.4f)", result['mean_rmse'], result['std_rmse'])
        if result['r2_interpretation']:
            logger.warning(result['r2_interpretation'])
    
    return result

def save_model_performance(results: Dict[str, Any], logger: logging.Logger = None):
    """Save model performance metrics to JSON."""
    with open(MODEL_PERFORMANCE_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    
    if logger:
        logger.info("Model performance saved to %s", MODEL_PERFORMANCE_PATH)

def main():
    """Main entry point for the analysis module."""
    # Setup logger
    logger = setup_analysis_logger("analysis", "results/analysis.log")
    logger.info("Starting analysis...")
    
    # Load metrics
    try:
        df = load_metrics_csv()
        logger.info("Loaded metrics from %s", METRICS_CSV_PATH)
        logger.info("DataFrame shape: %s", df.shape)
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    
    # Get network metrics
    network_metrics = get_network_metrics(df)
    if not network_metrics:
        logger.error("No network metrics found in the DataFrame.")
        logger.error("Available columns: %s", list(df.columns))
        return 1
    
    logger.info("Network metrics identified: %s", network_metrics)
    
    # Get thermal conductivity column
    target_col = get_thermal_conductivity_col(df)
    if not target_col:
        logger.error("Thermal conductivity column not found.")
        logger.error("Available columns: %s", list(df.columns))
        return 1
    
    logger.info("Target column: %s", target_col)
    
    # Calculate VIF
    logger.info("Calculating VIF for network metrics...")
    vif_values = calculate_vif(df, network_metrics)
    
    # Log VIF results
    log_vif_results(vif_values, logger, POWER_ANALYSIS_LOG_PATH)
    
    # Filter features based on VIF
    logger.info("Filtering features with VIF threshold = 5.0...")
    filtered_df = generate_filtered_features_csv(df, vif_values, threshold=5.0, logger=logger)
    
    # Check if we have any features left
    filtered_features = [col for col in filtered_df.columns if col in network_metrics]
    if not filtered_features:
        logger.warning("No features passed the VIF filter. Cannot proceed with model training.")
        logger.warning("This may indicate high multicollinearity in the network metrics.")
        # Still save empty results or handle appropriately
        return 0
    
    # Prepare data for model training
    X = filtered_df[filtered_features]
    y = filtered_df[target_col]
    
    # Train model
    logger.info("Training linear regression model...")
    model = train_linear_model(X, y, logger)
    
    # Save model
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    logger.info("Model saved to %s", MODEL_PATH)
    
    # Run cross-validation
    logger.info("Running stratified cross-validation...")
    cv_results = run_stratified_cross_validation(
        filtered_df, filtered_features, target_col, n_splits=5, logger=logger
    )
    
    # Save model performance
    save_model_performance(cv_results, logger)
    
    logger.info("Analysis completed successfully.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())