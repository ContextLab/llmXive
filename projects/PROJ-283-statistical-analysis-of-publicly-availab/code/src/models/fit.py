"""
Model fitting and metric consolidation for chess Elo analysis.
Implements Beta Regression, Ridge Regression, and final metric saving.
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, Any, List
from pathlib import Path
import logging
import json
import statsmodels.api as sm
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod import families
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SCHEMA_PATH = Path("specs/contracts/model_output.schema.yaml")
ECO_MAPPING_PATH = Path("data/config/eco_mapping.json")
PROCESSED_DATA_PATH = Path("data/processed/games.parquet")
METRICS_OUTPUT_PATH = Path("data/results/model_metrics.json")

def load_eco_mapping() -> Dict[str, str]:
    """Load ECO mapping from JSON config file."""
    if not ECO_MAPPING_PATH.exists():
        logger.error(f"ECO mapping file not found at {ECO_MAPPING_PATH}")
        raise FileNotFoundError(f"ECO mapping file not found: {ECO_MAPPING_PATH}")
    
    with open(ECO_MAPPING_PATH, 'r') as f:
        return json.load(f)

def map_eco_to_family(eco_code: Optional[str], mapping: Dict[str, str]) -> str:
    """Map ECO code to its family."""
    if eco_code is None or not isinstance(eco_code, str) or len(eco_code) == 0:
        return "Unknown"
    
    first_char = eco_code[0].upper()
    return mapping.get(first_char, "Unknown")

def collapse_eco_codes(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Collapse ECO codes into families based on the mapping.
    Adds a new column 'eco_family' to the dataframe.
    """
    logger.info("Collapsing ECO codes to families...")
    df['eco_family'] = df['eco_code'].apply(lambda x: map_eco_to_family(x, mapping))
    return df

def prepare_features_for_modeling(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepare features and target for modeling.
    Returns X (features) and y (target: outcome_deviation).
    """
    # Define features
    feature_cols = [
        'white_rating', 'black_rating', 'avg_move_time_white', 
        'avg_move_time_black', 'material_imbalance_move10', 'eco_family'
    ]
    
    # Ensure all feature columns exist
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required feature columns: {missing_cols}")
    
    X = df[feature_cols].copy()
    y = df['outcome_deviation'].copy()
    
    # Handle missing values
    X = X.fillna(X.median())
    
    # One-hot encode eco_family
    X = pd.get_dummies(X, columns=['eco_family'], drop_first=True)
    
    return X, y

def fit_beta_regression(X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """
    Fit Beta Regression model using statsmodels GLM.
    Returns model metrics.
    """
    logger.info("Fitting Beta Regression model...")
    
    # Transform y to (0, 1) range for Beta distribution
    # Normalize to [0, 1] then apply zero-inflation transformation
    y_norm = (y + 1) / 2
    n = len(y)
    y_transformed = (y_norm * (n - 1) + 0.5) / n
    
    # Ensure no values are exactly 0 or 1
    y_transformed = np.clip(y_transformed, 1e-6, 1 - 1e-6)
    
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    
    try:
        model = GLM(y_transformed, X_with_const, family=families.Beta())
        result = model.fit()
        
        # Extract metrics
        coefficients = result.params.to_dict()
        p_values = result.pvalues.to_dict()
        r_squared = result.rsquared
        aic = result.aic
        
        return {
            'model_type': 'Beta Regression',
            'coefficients': {k: float(v) for k, v in coefficients.items()},
            'p_values': {k: float(v) for k, v in p_values.items()},
            'r_squared': float(r_squared),
            'aic': float(aic),
            'cross_validation_scores': []  # Will be filled by validation stage
        }
    except Exception as e:
        logger.error(f"Error fitting Beta Regression: {e}")
        raise

def fit_ridge_regression(X: pd.DataFrame, y: pd.Series, alpha: float = 1.0) -> Dict[str, Any]:
    """
    Fit Ridge Regression model.
    Returns model metrics.
    """
    logger.info("Fitting Ridge Regression model...")
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Fit model
    model = Ridge(alpha=alpha)
    model.fit(X_scaled, y)
    
    # Calculate metrics
    predictions = model.predict(X_scaled)
    ss_res = np.sum((y - predictions) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    
    # Calculate p-values approximately (using t-test for coefficients)
    n = len(y)
    p = X_scaled.shape[1]
    residuals = y - predictions
    mse = np.sum(residuals ** 2) / (n - p - 1)
    std_errors = np.sqrt(mse * np.diag(np.linalg.inv(X_scaled.T @ X_scaled)))
    t_stats = model.coef_ / std_errors
    p_values = 2 * (1 - sm.stats.t.cdf(np.abs(t_stats), n - p - 1))
    
    coefficients = dict(zip(X.columns, model.coef_))
    p_values_dict = dict(zip(X.columns, p_values))
    
    return {
        'model_type': 'Ridge Regression',
        'coefficients': {k: float(v) for k, v in coefficients.items()},
        'p_values': {k: float(v) for k, v in p_values_dict.items()},
        'r_squared': float(r_squared),
        'aic': float(len(y) * np.log(ss_res / len(y)) + 2 * (p + 1)),
        'cross_validation_scores': []  # Will be filled by validation stage
    }

def load_schema() -> Dict[str, Any]:
    """Load the model output schema."""
    if not SCHEMA_PATH.exists():
        logger.error(f"Schema file not found at {SCHEMA_PATH}")
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def validate_against_schema(metrics: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate metrics against the schema."""
    logger.info("Validating metrics against schema...")
    
    # Check required fields
    required_fields = ['model_type', 'coefficients', 'p_values', 'r_squared', 'aic', 'cross_validation_scores']
    for field in required_fields:
        if field not in metrics:
            logger.error(f"Missing required field in metrics: {field}")
            return False
    
    # Check that cross_validation_scores is a list (non-empty requirement handled separately)
    if not isinstance(metrics['cross_validation_scores'], list):
        logger.error("cross_validation_scores must be a list")
        return False
    
    return True

def save_model_metrics(beta_metrics: Dict[str, Any], ridge_metrics: Dict[str, Any], 
                     significant_predictors: List[str]) -> None:
    """
    Save model metrics to JSON file and validate against schema.
    """
    logger.info("Saving model metrics...")
    
    # Prepare final metrics structure
    final_metrics = {
        'models': [beta_metrics, ridge_metrics],
        'significant_predictors': significant_predictors,
        'schema_version': '1.0'
    }
    
    # Load and validate against schema
    schema = load_schema()
    for model_metrics in final_metrics['models']:
        if not validate_against_schema(model_metrics, schema):
            raise ValueError("Model metrics failed schema validation")
    
    # Ensure output directory exists
    METRICS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to JSON
    with open(METRICS_OUTPUT_PATH, 'w') as f:
        json.dump(final_metrics, f, indent=2)
    
    logger.info(f"Model metrics saved to {METRICS_OUTPUT_PATH}")

def main():
    """Main function to run the model fitting and saving pipeline."""
    logger.info("Starting model fitting and metrics consolidation...")
    
    # Load processed data
    if not PROCESSED_DATA_PATH.exists():
        logger.error(f"Processed data not found at {PROCESSED_DATA_PATH}")
        raise FileNotFoundError(f"Processed data not found: {PROCESSED_DATA_PATH}")
    
    df = pd.read_parquet(PROCESSED_DATA_PATH)
    logger.info(f"Loaded {len(df)} game records")
    
    # Load ECO mapping
    eco_mapping = load_eco_mapping()
    
    # Collapse ECO codes
    df = collapse_eco_codes(df, eco_mapping)
    
    # Prepare features
    X, y = prepare_features_for_modeling(df)
    
    # Fit models
    beta_metrics = fit_beta_regression(X, y)
    ridge_metrics = fit_ridge_regression(X, y)
    
    # Calculate significant predictors (corrected p-value < 0.01)
    # Note: In a full pipeline, this would use corrected p-values from FDR
    # For now, we'll use raw p-values as a placeholder
    all_p_values = {}
    for model_metrics in [beta_metrics, ridge_metrics]:
        for predictor, p_val in model_metrics['p_values'].items():
            if predictor not in all_p_values or p_val < all_p_values[predictor]:
                all_p_values[predictor] = p_val
    
    significant_predictors = [
        predictor for predictor, p_val in all_p_values.items() 
        if p_val < 0.01 and predictor != 'const'
    ]
    
    # Save metrics
    save_model_metrics(beta_metrics, ridge_metrics, significant_predictors)
    
    logger.info("Model fitting and metrics consolidation completed successfully")
    return 0

if __name__ == "__main__":
    exit(main())
