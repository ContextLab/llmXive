import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, Any, List
from pathlib import Path
import logging
import re

from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod import families

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mapping of ECO codes to families (simplified for demonstration)
ECO_FAMILIES = {
    'A': 'Flank Openings',
    'B': 'Semi-Open Games',
    'C': 'Open Games',
    'D': 'Closed Games',
    'E': 'Indian Defenses'
}

def map_eco_to_family(eco_code: str) -> str:
    """
    Map an ECO code (e.g., 'B20') to its opening family based on the first letter.
    
    Args:
        eco_code: The ECO code string (e.g., 'B20', 'C44')
        
    Returns:
        The family name (e.g., 'Semi-Open Games') or 'Unknown' if not found
    """
    if not eco_code or len(eco_code) == 0:
        return 'Unknown'
    
    first_char = eco_code[0].upper()
    return ECO_FAMILIES.get(first_char, 'Unknown')

def prepare_features_for_modeling(df: pd.DataFrame, target_col: str = 'outcome') -> Tuple[pd.DataFrame, pd.Series, Dict[str, Any]]:
    """
    Prepare features for modeling by one-hot encoding ECO families and scaling numeric features.
    
    Args:
        df: Input DataFrame with columns including 'eco_family' and numeric features
        target_col: Name of the target column (default: 'outcome')
        
    Returns:
        Tuple of (feature_matrix, target_series, info_dict)
    """
    logger.info(f"Preparing features for modeling. Target column: {target_col}")
    
    # Ensure we have the required columns
    required_cols = ['eco_family', 'avg_move_time_white', 'avg_move_time_black', 'material_imbalance_move5']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for modeling: {missing_cols}")
    
    # Create a copy to avoid modifying the original
    df_prep = df.copy()
    
    # One-hot encode ECO families
    eco_dummies = pd.get_dummies(df_prep['eco_family'], prefix='eco', drop_first=False)
    
    # Select numeric features
    numeric_features = ['avg_move_time_white', 'avg_move_time_black', 'material_imbalance_move5']
    
    # Combine numeric features and one-hot encoded ECO families
    X = pd.concat([df_prep[numeric_features], eco_dummies], axis=1)
    
    # Extract target
    y = df_prep[target_col]
    
    # Scale numeric features (not the one-hot encoded ones)
    scaler = StandardScaler()
    X_numeric = X[numeric_features]
    X_scaled = pd.DataFrame(scaler.fit_transform(X_numeric), columns=numeric_features, index=X.index)
    
    # Combine scaled numeric and one-hot encoded features
    X_final = pd.concat([X_scaled, X.drop(columns=numeric_features)], axis=1)
    
    info = {
        'scaler': scaler,
        'feature_names': list(X_final.columns),
        'numeric_features': numeric_features,
        'eco_columns': list(eco_dummies.columns)
    }
    
    logger.info(f"Prepared {X_final.shape[1]} features from {df.shape[0]} samples")
    return X_final, y, info

def fit_gaussian_glm(X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """
    Fit a Gaussian GLM model using statsmodels.
    
    Args:
        X: Feature DataFrame
        y: Target Series
        
    Returns:
        Dictionary containing model results and metadata
    """
    logger.info("Fitting Gaussian GLM...")
    
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    
    # Fit the model
    model = GLM(y, X_with_const, family=families.Gaussian())
    results = model.fit()
    
    # Extract coefficients and p-values
    coefficients = results.params.to_dict()
    p_values = results.pvalues.to_dict()
    r_squared = results.rsquared
    aic = results.aic
    
    logger.info(f"Gaussian GLM fitted. R²: {r_squared:.4f}, AIC: {aic:.2f}")
    
    return {
        'model_type': 'Gaussian GLM',
        'results': results,
        'coefficients': coefficients,
        'p_values': p_values,
        'r_squared': r_squared,
        'aic': aic,
        'feature_names': list(X_with_const.columns)
    }

def fit_ridge_regression(X: pd.DataFrame, y: pd.Series, alpha: float = 1.0) -> Dict[str, Any]:
    """
    Fit a Ridge Regression model using scikit-learn.
    
    Args:
        X: Feature DataFrame
        y: Target Series
        alpha: Ridge regularization strength (default: 1.0)
        
    Returns:
        Dictionary containing model results and metadata
    """
    logger.info(f"Fitting Ridge Regression with alpha={alpha}...")
    
    # Fit the model
    model = Ridge(alpha=alpha)
    model.fit(X, y)
    
    # Extract coefficients (intercept is separate)
    coefficients = {f'coef_{i}': coef for i, coef in enumerate(model.coef_)}
    coefficients['intercept'] = model.intercept_
    
    # Calculate R²
    y_pred = model.predict(X)
    r_squared = model.score(X, y)
    
    # AIC approximation for Ridge (using log-likelihood approximation)
    n = len(y)
    k = len(model.coef_) + 1  # +1 for intercept
    mse = np.mean((y - y_pred) ** 2)
    aic = n * np.log(mse) + 2 * k
    
    logger.info(f"Ridge Regression fitted. R²: {r_squared:.4f}, AIC (approx): {aic:.2f}")
    
    return {
        'model_type': 'Ridge Regression',
        'model': model,
        'coefficients': coefficients,
        'r_squared': r_squared,
        'aic': aic,
        'alpha': alpha,
        'feature_names': list(X.columns)
    }

def main():
    """
    Main function to demonstrate the fitting of Gaussian GLM and Ridge Regression.
    This function loads processed data, prepares features, fits both models, and saves results.
    """
    logger.info("Starting model fitting pipeline...")
    
    # Load processed data (assuming it exists from previous steps)
    data_path = Path("data/processed/games.parquet")
    if not data_path.exists():
        logger.error(f"Processed data not found at {data_path}. Please run data processing first.")
        return
    
    df = pd.read_parquet(data_path)
    logger.info(f"Loaded {len(df)} game records")
    
    # Prepare features
    X, y, info = prepare_features_for_modeling(df)
    
    # Fit Gaussian GLM
    glm_results = fit_gaussian_glm(X, y)
    
    # Fit Ridge Regression
    ridge_results = fit_ridge_regression(X, y)
    
    # Save results
    results_dir = Path("data/results")
    results_dir.mkdir(exist_ok=True)
    
    # Save model metrics
    metrics = {
        'Gaussian GLM': {
            'r_squared': glm_results['r_squared'],
            'aic': glm_results['aic'],
            'coefficients': glm_results['coefficients'],
            'p_values': glm_results['p_values']
        },
        'Ridge Regression': {
            'r_squared': ridge_results['r_squared'],
            'aic': ridge_results['aic'],
            'coefficients': ridge_results['coefficients'],
            'alpha': ridge_results['alpha']
        }
    }
    
    metrics_path = results_dir / "model_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    
    logger.info(f"Model metrics saved to {metrics_path}")
    logger.info("Model fitting pipeline completed successfully.")

if __name__ == "__main__":
    main()
