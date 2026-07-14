import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, Any, List
from pathlib import Path
import logging
import re
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import joblib

from src.config import ensure_directories

logger = logging.getLogger(__name__)

def map_eco_to_family(eco_code: str) -> str:
    """
    Map a specific ECO code to a broader opening family.
    
    Args:
        eco_code: The ECO code string (e.g., 'B00', 'C50').
        
    Returns:
        A string representing the opening family.
    """
    if pd.isna(eco_code) or not isinstance(eco_code, str) or len(eco_code) < 1:
        return "Unknown"
    
    first_char = eco_code[0].upper()
    families = {
        'A': 'Flank Openings',
        'B': 'Semi-Open Games',
        'C': 'Open Games',
        'D': 'Closed Games',
        'E': 'Indian Defenses'
    }
    return families.get(first_char, "Unclassified")

def prepare_features_for_modeling(
    df: pd.DataFrame, 
    target_col: str = 'outcome',
    drop_cols: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepare features for modeling by one-hot encoding ECO families and 
    selecting numerical predictors.
    
    Args:
        df: The input DataFrame containing game records.
        target_col: The name of the target column.
        drop_cols: List of columns to drop before modeling.
        
    Returns:
        A tuple of (feature_matrix, target_series).
    """
    if drop_cols is None:
        drop_cols = ['game_id', 'eco_code']
        
    # Create a copy to avoid SettingWithCopyWarning
    data = df.copy()
    
    # Map ECO codes to families if 'eco_code' exists
    if 'eco_code' in data.columns:
        data['eco_family'] = data['eco_code'].apply(map_eco_to_family)
        if 'eco_code' not in drop_cols:
            drop_cols.append('eco_code')
        
        # One-hot encode the family
        dummies = pd.get_dummies(data['eco_family'], prefix='eco_family')
        data = pd.concat([data.drop('eco_family', axis=1), dummies], axis=1)
    
    # Ensure target is numeric
    if target_col in data.columns:
        # Map chess outcomes (1-0, 0-1, 1/2-1/2) to numeric (1, 0, 0.5)
        if data[target_col].dtype == 'object':
            mapping = {'1-0': 1.0, '0-1': 0.0, '1/2-1/2': 0.5, '*': np.nan}
            data[target_col] = data[target_col].map(mapping)
    
    # Separate features and target
    if target_col in data.columns:
        y = data[target_col]
        X = data.drop(columns=[c for c in [target_col] + drop_cols if c in data.columns])
    else:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame")
    
    # Select only numerical columns for Ridge regression
    numerical_cols = X.select_dtypes(include=[np.number]).columns
    X = X[numerical_cols]
    
    # Handle missing values by dropping rows with NaN in features or target
    mask = ~X.isna().any(axis=1) & ~y.isna()
    X = X[mask]
    y = y[mask]
    
    return X, y

def fit_ridge_regression(X: pd.DataFrame, y: pd.Series, alpha: float = 1.0) -> Dict[str, Any]:
    """
    Fit a Ridge Regression model as a linear baseline.
    
    Args:
        X: Feature matrix (pandas DataFrame).
        y: Target series (pandas Series).
        alpha: Regularization strength.
        
    Returns:
        A dictionary containing the fitted model, scaler, coefficients, and metrics.
    """
    if X.empty or y.empty:
        raise ValueError("Feature matrix or target series is empty.")
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Fit model
    model = Ridge(alpha=alpha)
    model.fit(X_scaled, y)
    
    # Calculate R-squared
    y_pred = model.predict(X_scaled)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    # Calculate MSE
    mse = np.mean((y - y_pred) ** 2)
    
    # Map coefficients back to feature names
    coefficients = dict(zip(X.columns, model.coef_))
    
    return {
        'model': model,
        'scaler': scaler,
        'coefficients': coefficients,
        'r_squared': r_squared,
        'mse': mse,
        'alpha': alpha
    }

def main():
    """
    Main entry point to load data, fit Ridge Regression, and save results.
    """
    # Ensure output directories exist
    ensure_directories()
    
    # Load processed game data
    input_path = Path("data/processed/games.parquet")
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Please run the data ingestion pipeline first.")
        return
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_parquet(input_path)
    
    logger.info(f"Loaded {len(df)} games. Columns: {list(df.columns)}")
    
    # Prepare features
    try:
        X, y = prepare_features_for_modeling(df, target_col='outcome')
        logger.info(f"Prepared features: {X.shape[1]} features, {len(X)} samples.")
    except Exception as e:
        logger.error(f"Error preparing features: {e}")
        return
    
    # Fit Ridge Regression
    try:
        results = fit_ridge_regression(X, y, alpha=1.0)
        logger.info(f"Ridge Regression fitted. R²: {results['r_squared']:.4f}, MSE: {results['mse']:.4f}")
    except Exception as e:
        logger.error(f"Error fitting Ridge Regression: {e}")
        return
    
    # Save results
    output_path = Path("data/results/ridge_model_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert numpy types to native Python for JSON serialization
    serializable_results = {
        'coefficients': {k: float(v) for k, v in results['coefficients'].items()},
        'r_squared': float(results['r_squared']),
        'mse': float(results['mse']),
        'alpha': float(results['alpha'])
    }
    
    import json
    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    logger.info(f"Model results saved to {output_path}")
    
    # Also save the model artifact for later use
    model_artifact_path = Path("data/results/ridge_model.pkl")
    joblib.dump({
        'model': results['model'],
        'scaler': results['scaler'],
        'coefficients': results['coefficients']
    }, model_artifact_path)
    logger.info(f"Model artifact saved to {model_artifact_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()