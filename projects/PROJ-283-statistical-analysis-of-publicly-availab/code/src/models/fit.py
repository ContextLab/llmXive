"""
Model fitting module.
Implements T021-1, T021-2, T022a-2, T022b, T027: Fit models and save metrics.
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, Any, List
from pathlib import Path
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ECO_FAMILIES = {
    'A': 'King\'s Pawn',
    'B': 'Sicilian',
    'C': 'French',
    'D': 'Queen\'s Gambit',
    'E': 'Indian Defense'
}

def load_eco_mapping(df: pd.DataFrame) -> Dict[str, str]:
    """
    Scan dataset for unique ECO codes and map to families.
    Implements T021-1.
    """
    unique_codes = df['eco_code'].unique()
    mapping = {}
    
    for code in unique_codes:
        if pd.isna(code) or code == 'Unknown':
            mapping[code] = 'Unknown'
            continue
        
        first_char = str(code)[0].upper()
        mapping[code] = ECO_FAMILIES.get(first_char, 'Unknown')
    
    return mapping

def map_eco_to_family(eco_code: str, mapping: Dict[str, str]) -> str:
    """Map a single ECO code to family."""
    return mapping.get(eco_code, 'Unknown')

def collapse_eco_codes(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Collapse ECO codes to families.
    Implements T021-2.
    """
    df = df.copy()
    df['eco_family'] = df['eco_code'].apply(lambda x: map_eco_to_family(x, mapping))
    return df

def prepare_features_for_modeling(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepare features and target for modeling.
    Implements T021-2.
    """
    # Use material_imbalance_move10 as primary feature
    features = ['material_imbalance_move10', 'white_rating', 'black_rating']
    
    # Encode eco_family as dummy variables
    eco_dummies = pd.get_dummies(df['eco_family'], prefix='eco')
    
    X = pd.concat([df[features], eco_dummies], axis=1)
    y = df['outcome_deviation']
    
    return X, y

def transform_for_beta(y: pd.Series) -> pd.Series:
    """
    Transform outcome deviation for Beta regression.
    Implements T022a-1.
    """
    # Normalize to [0, 1]
    y_norm = (y + 1) / 2
    
    # Apply zero-inflation transformation
    N = len(y)
    y_transformed = (y_norm * (N - 1) + 0.5) / N
    
    return y_transformed

def inverse_transform_beta(y_transformed: pd.Series, N: int) -> pd.Series:
    """Inverse transform Beta regression predictions."""
    y_norm = (y_transformed * N - 0.5) / (N - 1)
    y = y_norm * 2 - 1
    return y

def fit_beta_regression(X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """
    Fit Beta regression model.
    Implements T022a-2.
    """
    try:
        import statsmodels.api as sm
        from statsmodels.genmod.generalized_linear_model import GLM
        from statsmodels.genmod import families
        
        X_with_const = sm.add_constant(X)
        model = GLM(y, X_with_const, family=families.Beta())
        results = model.fit()
        
        return {
            'coefficients': dict(zip(X_with_const.columns, results.params)),
            'p_values': list(results.pvalues),
            'r_squared': results.prsquared,
            'aic': results.aic,
            'model': results
        }
    except Exception as e:
        logger.warning(f"Beta regression failed: {e}")
        return {'coefficients': {}, 'p_values': [], 'r_squared': 0, 'aic': 0}

def fit_gaussian_glm(X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """
    Fit Gaussian GLM.
    Implements T022b.
    """
    try:
        import statsmodels.api as sm
        from statsmodels.genmod.generalized_linear_model import GLM
        from statsmodels.genmod import families
        
        X_with_const = sm.add_constant(X)
        model = GLM(y, X_with_const, family=families.Gaussian())
        results = model.fit()
        
        return {
            'coefficients': dict(zip(X_with_const.columns, results.params)),
            'p_values': list(results.pvalues),
            'r_squared': results.prsquared,
            'aic': results.aic,
            'model': results
        }
    except Exception as e:
        logger.warning(f"Gaussian GLM failed: {e}")
        return {'coefficients': {}, 'p_values': [], 'r_squared': 0, 'aic': 0}

def fit_ridge_regression(X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """
    Fit Ridge regression.
    Implements T022b.
    """
    try:
        from sklearn.linear_model import Ridge
        from sklearn.preprocessing import StandardScaler
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = Ridge(alpha=1.0)
        model.fit(X_scaled, y)
        
        return {
            'coefficients': dict(zip(X.columns, model.coef_)),
            'p_values': [],  # Ridge doesn't provide p-values
            'r_squared': model.score(X_scaled, y),
            'aic': 0,  # AIC not directly available for Ridge
            'model': model
        }
    except Exception as e:
        logger.warning(f"Ridge regression failed: {e}")
        return {'coefficients': {}, 'p_values': [], 'r_squared': 0, 'aic': 0}

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load schema from YAML file."""
    import yaml
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate data against schema."""
    # Simple validation
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in data:
            return False
    return True

def save_model_metrics(metrics: Dict[str, Any], output_path: Path) -> None:
    """
    Save model metrics to JSON.
    Implements T027.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    logger.info(f"Saved model metrics to {output_path}")

def main():
    """Main entry point for testing."""
    pass
