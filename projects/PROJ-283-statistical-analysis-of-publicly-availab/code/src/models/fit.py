"""
Model fitting module for Chess Elo Analysis.
Implements ECO collapsing, feature preparation, and regression fitting.
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, Any, List
from pathlib import Path
import logging
import re
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Corrected ECO mapping per T021a specification:
# 'A' -> King's Pawn
# 'B'-'C' -> Queen's Pawn
# 'D' -> Sicilian
# 'E' -> King's Indian
# 'F' -> English
# 'G' -> Réti
# 'H' -> Other
ECO_FAMILIES = {
    'A': "King's Pawn",
    'B': "Queen's Pawn",
    'C': "Queen's Pawn",
    'D': "Sicilian",
    'E': "King's Indian",
    'F': "English",
    'G': "Réti",
    'H': "Other"
}

def map_eco_to_family(eco_code: str) -> str:
    """
    Maps a specific ECO code (e.g., 'B20') to its family based on the first character.
    
    Args:
        eco_code: The ECO code string (e.g., 'A00', 'B12').
        
    Returns:
        The family name string.
        
    Raises:
        ValueError: If the ECO code is invalid or empty.
    """
    if not eco_code or not isinstance(eco_code, str):
        raise ValueError(f"Invalid ECO code: {eco_code}")
    
    # Extract the first character
    first_char = eco_code[0].upper()
    
    if first_char not in ECO_FAMILIES:
        # Fallback for unexpected characters, though spec implies A-H coverage
        logger.warning(f"Unexpected ECO prefix '{first_char}' in code '{eco_code}'. Defaulting to 'Other'.")
        return "Other"
        
    return ECO_FAMILIES[first_char]

def prepare_features_for_modeling(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepares features and target for regression modeling.
    - Collapses ECO codes to families.
    - Selects relevant features.
    - Handles missing values.
    
    Args:
        df: Input DataFrame with game records.
        
    Returns:
        Tuple of (feature_matrix, target_series).
    """
    logger.info("Preparing features for modeling...")
    
    # Create a copy to avoid SettingWithCopyWarning
    data = df.copy()
    
    # Apply ECO collapsing
    data['eco_family'] = data['eco_code'].apply(map_eco_to_family)
    
    # Define features for modeling
    # Based on typical chess analysis: ratings, time, imbalance, and the new ECO family
    feature_cols = [
        'white_rating', 'black_rating', 
        'avg_move_time_white', 'avg_move_time_black',
        'material_imbalance_move10'
    ]
    
    # Check for required columns
    missing_cols = [col for col in feature_cols if col not in data.columns]
    if missing_cols:
        raise ValueError(f"Missing required feature columns: {missing_cols}")
    
    # One-hot encode ECO families
    eco_dummies = pd.get_dummies(data['eco_family'], prefix='eco')
    
    # Combine features
    features = pd.concat([data[feature_cols], eco_dummies], axis=1)
    
    # Handle missing values in features (simple imputation with mean for now)
    # In a full pipeline, this might be more sophisticated
    features = features.fillna(features.mean())
    
    # Target: outcome_deviation
    if 'outcome_deviation' not in data.columns:
        raise ValueError("Target column 'outcome_deviation' not found in DataFrame")
    
    target = data['outcome_deviation'].fillna(0.0) # Simple imputation for target if needed
    
    logger.info(f"Feature matrix shape: {features.shape}")
    return features, target

def fit_ridge_regression(X: pd.DataFrame, y: pd.Series, alpha: float = 1.0) -> Dict[str, Any]:
    """
    Fits a Ridge Regression model.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        alpha: Regularization strength.
        
    Returns:
        Dictionary containing model results (coefficients, intercept, score).
    """
    from sklearn.linear_model import Ridge
    
    logger.info("Fitting Ridge Regression...")
    model = Ridge(alpha=alpha)
    model.fit(X, y)
    
    return {
        'model_type': 'Ridge',
        'alpha': alpha,
        'coefficients': model.coef_,
        'intercept': model.intercept_,
        'r_squared': model.score(X, y),
        'feature_names': X.columns.tolist()
    }

def fit_beta_regression(X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """
    Fits a Beta Regression model using statsmodels GLM.
    Note: Beta regression requires y in (0, 1). Since outcome_deviation can be outside this,
    we may need to scale or use a different link if strictly following Beta distribution assumptions.
    However, for this task, we attempt to fit it. If y is not in valid range, we might need to transform.
    For the purpose of this implementation, we assume the data is suitable or we apply a safe transform.
    Actually, outcome_deviation = actual (0,1) - expected (0,1) -> range [-1, 1].
    Beta regression is for (0,1). We will shift/scale y to (0,1) for the model fit.
    """
    import statsmodels.api as sm
    from statsmodels.genmod.families import Beta
    
    logger.info("Fitting Beta Regression...")
    
    # Ensure y is strictly between 0 and 1 for Beta family
    # Shift and scale to (0.01, 0.99) to avoid log(0) issues
    y_min, y_max = y.min(), y.max()
    if y_min < 0 or y_max > 1:
        logger.warning("Target 'outcome_deviation' is outside [0,1]. Rescaling to (0.01, 0.99) for Beta regression.")
        # Simple linear transformation to (0.01, 0.99)
        y_scaled = 0.01 + (y - y_min) / (y_max - y_min + 1e-9) * 0.98
    else:
        y_scaled = y.copy()
    
    # Add constant for intercept
    X_sm = sm.add_constant(X)
    
    try:
        model = sm.GLM(y_scaled, X_sm, family=Beta())
        results = model.fit()
        
        return {
            'model_type': 'Beta',
            'coefficients': results.params.values,
            'p_values': results.pvalues.values,
            'r_squared': results.prsquared, # Pseudo R-squared
            'aic': results.aic,
            'feature_names': X_sm.columns.tolist()
        }
    except Exception as e:
        logger.error(f"Failed to fit Beta Regression: {e}")
        # Fallback to Gaussian if Beta fails, but log it
        logger.warning("Falling back to Gaussian GLM due to Beta fit failure.")
        model = sm.GLM(y_scaled, X_sm, family=sm.families.Gaussian())
        results = model.fit()
        return {
            'model_type': 'Beta_Fallback_Gaussian',
            'coefficients': results.params.values,
            'p_values': results.pvalues.values,
            'r_squared': results.prsquared,
            'aic': results.aic,
            'feature_names': X_sm.columns.tolist()
        }

def save_model_metrics(models_results: List[Dict[str, Any]], output_path: str):
    """
    Saves model metrics to a JSON file.
    
    Args:
        models_results: List of dictionaries containing model results.
        output_path: Path to save the JSON file.
    """
    logger.info(f"Saving model metrics to {output_path}")
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Convert numpy types to Python native types for JSON serialization
    def convert_numpy_types(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(i) for i in obj]
        return obj
    
    clean_results = convert_numpy_types(models_results)
    
    with open(output_path, 'w') as f:
        json.dump(clean_results, f, indent=2)
    
    logger.info("Model metrics saved successfully.")

def save_eco_mapping(output_path: str):
    """
    Saves the ECO mapping dictionary to a JSON file.
    
    Args:
        output_path: Path to save the JSON file.
    """
    logger.info(f"Saving ECO mapping to {output_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(ECO_FAMILIES, f, indent=2)
    
    logger.info("ECO mapping saved successfully.")

def main():
    """
    Main function to execute ECO collapsing and model fitting.
    This is a placeholder for the full pipeline integration.
    In a real scenario, this would load data, prepare features, fit models, and save results.
    """
    logger.info("Starting ECO mapping and model fitting process.")
    
    # Save the ECO mapping as per T021a requirement
    mapping_path = "data/processed/eco_mapping.json"
    save_eco_mapping(mapping_path)
    
    # Note: Actual data loading and model fitting would happen here
    # if this script were run as part of the full pipeline with data available.
    # For now, we ensure the mapping artifact is created.
    
    logger.info("ECO mapping process completed.")

if __name__ == "__main__":
    main()
