import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, Any, List
from pathlib import Path
import logging
import re
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from statsmodels.stats.outliers_influence import OLSInfluence
import statsmodels.api as sm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mapping of ECO codes to opening families based on standard chess opening theory
ECO_FAMILIES = {
    'A': 'Sicilian Defense',
    'B': 'Sicilian Defense',
    'C': 'King\'s Pawn Openings',
    'D': 'Queen\'s Pawn Openings',
    'E': 'Indian Defenses',
}

def map_eco_to_family(eco_code: str) -> str:
    """
    Map a specific ECO code to its opening family.
    
    Args:
        eco_code: A string representing an ECO code (e.g., 'B20', 'C50')
        
    Returns:
        The opening family name as a string
    """
    if not isinstance(eco_code, str) or len(eco_code) < 1:
        return 'Unknown Opening'
    
    first_char = eco_code[0].upper()
    return ECO_FAMILIES.get(first_char, 'Other Openings')

def prepare_features_for_modeling(df: pd.DataFrame, target_col: str = 'outcome_deviation') -> Tuple[pd.DataFrame, pd.Series, ColumnTransformer]:
    """
    Prepare features for modeling by one-hot encoding ECO codes and collapsing them into families.
    
    Args:
        df: Input DataFrame with game records
        target_col: Name of the target variable column
        
    Returns:
        Tuple of (processed_features, target_series, preprocessor)
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame")
    
    # Map ECO codes to families
    df = df.copy()
    df['eco_family'] = df['eco_code'].apply(map_eco_to_family)
    
    # Define feature columns
    feature_cols = [
        'white_rating',
        'black_rating', 
        'avg_move_time_white',
        'avg_move_time_black',
        'material_imbalance_move5',
        'eco_family'
    ]
    
    # Filter to available columns
    available_cols = [col for col in feature_cols if col in df.columns]
    
    if len(available_cols) == 0:
        raise ValueError("No feature columns available for modeling")
    
    # Separate numeric and categorical features
    numeric_features = [col for col in available_cols if col != 'eco_family']
    categorical_features = ['eco_family'] if 'eco_family' in available_cols else []
    
    # Create preprocessor
    transformers = []
    if numeric_features:
        transformers.append(('num', 'passthrough', numeric_features))
    if categorical_features:
        transformers.append(('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features))
    
    preprocessor = ColumnTransformer(transformers=transformers)
    
    # Prepare features and target
    X = df[available_cols]
    y = df[target_col]
    
    # Drop rows with missing target or features
    mask = ~(X.isnull().any(axis=1) | y.isnull())
    X_clean = X[mask]
    y_clean = y[mask]
    
    logger.info(f"Prepared {len(X_clean)} samples with {len(available_cols)} features for modeling")
    
    return X_clean, y_clean, preprocessor

def fit_ridge_regression(X: pd.DataFrame, y: pd.Series, alpha: float = 1.0) -> Tuple[Ridge, ColumnTransformer, Dict[str, Any]]:
    """
    Fit a Ridge Regression model as a linear baseline.
    
    Args:
        X: Feature DataFrame
        y: Target Series
        alpha: Regularization strength (must be >= 0)
        
    Returns:
        Tuple of (fitted_model, preprocessor, metrics_dict)
    """
    logger.info(f"Fitting Ridge Regression with alpha={alpha}")
    
    # Prepare features
    X_clean, y_clean, preprocessor = prepare_features_for_modeling(
        pd.concat([X.reset_index(drop=True), y.reset_index(drop=True)], axis=1)
    )
    
    # Create pipeline
    model = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', Ridge(alpha=alpha))
    ])
    
    # Fit the model
    model.fit(X_clean, y_clean)
    
    # Calculate metrics
    y_pred = model.predict(X_clean)
    mse = np.mean((y_clean - y_pred) ** 2)
    r_squared = 1 - (np.sum((y_clean - y_pred) ** 2) / np.sum((y_clean - y_clean.mean()) ** 2))
    
    # Extract coefficients for the first stage (preprocessor)
    ridge_model = model.named_steps['regressor']
    preprocessor_model = model.named_steps['preprocessor']
    
    # Get feature names after preprocessing
    feature_names = []
    if 'num' in preprocessor_model.named_transformers_:
        feature_names.extend(preprocessor_model.named_transformers_['num'][2])
    if 'cat' in preprocessor_model.named_transformers_:
        cat_encoder = preprocessor_model.named_transformers_['cat'][0]
        cat_features = preprocessor_model.named_transformers_['cat'][2]
        for i, feat in enumerate(cat_features):
            for j, category in enumerate(cat_encoder.categories_[i]):
                feature_names.append(f"{feat}_{category}")
    
    # Create coefficients dictionary
    coefficients = dict(zip(feature_names, ridge_model.coef_))
    coefficients['intercept'] = float(ridge_model.intercept_)
    
    metrics = {
        'model_type': 'Ridge',
        'alpha': alpha,
        'r_squared': float(r_squared),
        'mse': float(mse),
        'coefficients': coefficients,
        'n_samples': len(X_clean),
        'n_features': len(feature_names)
    }
    
    logger.info(f"Ridge Regression complete - R²: {r_squared:.4f}, MSE: {mse:.4f}")
    
    return model, preprocessor, metrics

def main():
    """
    Main function to demonstrate Ridge Regression fitting.
    This is intended to be called from a pipeline or main entry point.
    """
    logger.info("Starting Ridge Regression fitting demonstration")
    
    # Create sample data for demonstration
    # In production, this would load from data/processed/games.parquet
    np.random.seed(42)
    n_samples = 1000
    
    sample_data = pd.DataFrame({
        'white_rating': np.random.normal(1500, 200, n_samples),
        'black_rating': np.random.normal(1500, 200, n_samples),
        'avg_move_time_white': np.random.exponential(10, n_samples),
        'avg_move_time_black': np.random.exponential(10, n_samples),
        'material_imbalance_move5': np.random.normal(0, 0.5, n_samples),
        'eco_code': np.random.choice(['A', 'B', 'C', 'D', 'E'], n_samples),
        'outcome_deviation': np.random.normal(0, 0.3, n_samples)
    })
    
    # Fit Ridge Regression
    model, preprocessor, metrics = fit_ridge_regression(
        sample_data[['white_rating', 'black_rating', 'avg_move_time_white', 
                    'avg_move_time_black', 'material_imbalance_move5', 'eco_code']],
        sample_data['outcome_deviation']
    )
    
    logger.info(f"Model metrics: {metrics}")
    return model, metrics

if __name__ == "__main__":
    main()