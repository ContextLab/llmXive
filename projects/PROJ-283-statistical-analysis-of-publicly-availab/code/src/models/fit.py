import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, Any, List
from pathlib import Path
import logging
import json
import statsmodels.api as sm
from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_val_score
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
ECO_FAMILIES = {
    'A': 'King\'s Pawn',
    'B': 'Sicilian',
    'C': 'French',
    'D': 'Queen\'s Gambit',
    'E': 'Indian Defense'
}

def load_eco_mapping(data_path: Path) -> Dict[str, str]:
    """Load ECO code mapping from data or generate dynamically."""
    logger.info(f"Loading ECO mapping from data at {data_path}")
    if not data_path.exists():
        logger.warning(f"Data file not found at {data_path}, returning empty mapping")
        return {}
    
    df = pd.read_parquet(data_path)
    unique_ecos = df['eco_code'].unique()
    mapping = {}
    for eco in unique_ecos:
        if pd.isna(eco) or eco == "Unknown":
            mapping[eco] = 'Unknown'
        else:
            first_char = str(eco)[0].upper()
            mapping[eco] = ECO_FAMILIES.get(first_char, 'Unknown')
    
    return mapping

def map_eco_to_family(eco_code: str) -> str:
    """Map a specific ECO code to its family."""
    if pd.isna(eco_code) or eco_code == "Unknown":
        return 'Unknown'
    first_char = str(eco_code)[0].upper()
    return ECO_FAMILIES.get(first_char, 'Unknown')

def collapse_eco_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse ECO codes to families."""
    df = df.copy()
    df['eco_family'] = df['eco_code'].apply(map_eco_to_family)
    return df

def prepare_features_for_modeling(df: pd.DataFrame, use_move_5: bool = False) -> Tuple[pd.DataFrame, pd.Series]:
    """Prepare features and target for modeling."""
    logger.info("Preparing features for modeling")
    
    # Collapse ECO codes
    df_collapsed = collapse_eco_codes(df)
    
    # Select primary feature based on config
    feature_col = 'material_imbalance_move5' if use_move_5 else 'material_imbalance_move10'
    
    # Prepare features
    features = pd.get_dummies(df_collapsed['eco_family'], prefix='eco')
    features['material_imbalance'] = df_collapsed[feature_col]
    
    # Target variable
    target = df_collapsed['outcome_deviation']
    
    return features, target

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load YAML schema."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate data against schema."""
    required_columns = schema.get('columns', [])
    for col in required_columns:
        if col not in data:
            logger.error(f"Missing required column: {col}")
            return False
    return True

def fit_gaussian_glm(features: pd.DataFrame, target: pd.Series) -> Dict[str, Any]:
    """Fit Gaussian GLM with identity link."""
    logger.info("Fitting Gaussian GLM")
    X = sm.add_constant(features)
    model = sm.GLM(target, X, family=sm.families.Gaussian())
    result = model.fit()
    
    return {
        'coefficients': result.params.tolist(),
        'p_values': result.pvalues.tolist(),
        'r_squared': result.rsquared,
        'aic': result.aic,
        'model_type': 'Gaussian GLM'
    }

def fit_ridge_regression(features: pd.DataFrame, target: pd.Series) -> Dict[str, Any]:
    """Fit Ridge Regression."""
    logger.info("Fitting Ridge Regression")
    model = Ridge(alpha=1.0)
    model.fit(features, target)
    
    # Calculate R² on training data
    predictions = model.predict(features)
    ss_res = np.sum((target - predictions) ** 2)
    ss_tot = np.sum((target - np.mean(target)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    
    return {
        'coefficients': model.coef_.tolist(),
        'p_values': [np.nan] * len(model.coef_),  # Ridge doesn't provide p-values
        'r_squared': r_squared,
        'aic': np.nan,  # AIC not directly available for Ridge
        'model_type': 'Ridge'
    }

def fit_beta_regression(features: pd.DataFrame, target: pd.Series) -> Dict[str, Any]:
    """Fit Beta Regression with zero-inflation handling."""
    logger.info("Fitting Beta Regression")
    
    # Transform target to (0, 1) range
    N = len(target)
    y_norm = (target + 1) / 2
    y_transformed = (y_norm * (N - 1) + 0.5) / N
    
    X = sm.add_constant(features)
    model = sm.GLM(y_transformed, X, family=sm.families.Beta())
    result = model.fit()
    
    return {
        'coefficients': result.params.tolist(),
        'p_values': result.pvalues.tolist(),
        'r_squared': result.rsquared,
        'aic': result.aic,
        'model_type': 'Beta Regression'
    }

def save_model_metrics(
    beta_metrics: Dict[str, Any],
    gaussian_metrics: Dict[str, Any],
    ridge_metrics: Dict[str, Any],
    corrected_p_values: Dict[str, List[float]],
    cv_scores: Dict[str, List[float]],
    output_path: Path
) -> None:
    """Save consolidated model metrics to JSON."""
    logger.info(f"Saving model metrics to {output_path}")
    
    # Calculate significant predictors (corrected p-value < 0.01)
    significant_predictors = []
    if corrected_p_values and 'material_imbalance' in corrected_p_values:
        p_values = corrected_p_values['material_imbalance']
        for i, p_val in enumerate(p_values):
            if p_val < 0.01:
                significant_predictors.append(f"material_imbalance_{i}")
    
    # Also check ECO family p-values if available
    for key, p_vals in corrected_p_values.items():
        if key != 'material_imbalance':
            for i, p_val in enumerate(p_vals):
                if p_val < 0.01:
                    significant_predictors.append(f"{key}_{i}")
    
    # Remove duplicates
    significant_predictors = list(set(significant_predictors))
    
    # Build output structure
    output = {
        'models': [
            {
                'model_type': beta_metrics['model_type'],
                'coefficients': beta_metrics['coefficients'],
                'p_values': beta_metrics['p_values'],
                'r_squared': beta_metrics['r_squared'],
                'aic': beta_metrics['aic'],
                'cross_validation_scores': cv_scores.get('Beta Regression', [])
            },
            {
                'model_type': gaussian_metrics['model_type'],
                'coefficients': gaussian_metrics['coefficients'],
                'p_values': gaussian_metrics['p_values'],
                'r_squared': gaussian_metrics['r_squared'],
                'aic': gaussian_metrics['aic'],
                'cross_validation_scores': cv_scores.get('Gaussian GLM', [])
            },
            {
                'model_type': ridge_metrics['model_type'],
                'coefficients': ridge_metrics['coefficients'],
                'p_values': ridge_metrics['p_values'],
                'r_squared': ridge_metrics['r_squared'],
                'aic': ridge_metrics['aic'],
                'cross_validation_scores': cv_scores.get('Ridge', [])
            }
        ],
        'significant_predictors': significant_predictors
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Model metrics saved to {output_path}")

def main():
    """Main entry point for T027."""
    logger.info("Starting T027: Model Metrics Consolidation")
    
    # Paths
    processed_data_path = Path("data/processed/games.parquet")
    output_path = Path("data/results/model_metrics.json")
    schema_path = Path("specs/contracts/model_output.schema.yaml")
    
    # Load data
    if not processed_data_path.exists():
        logger.error(f"Processed data not found at {processed_data_path}")
        return
    
    df = pd.read_parquet(processed_data_path)
    logger.info(f"Loaded {len(df)} records")
    
    # Prepare features
    features, target = prepare_features_for_modeling(df)
    logger.info(f"Prepared {features.shape[1]} features")
    
    # Fit models
    beta_metrics = fit_beta_regression(features, target)
    gaussian_metrics = fit_gaussian_glm(features, target)
    ridge_metrics = fit_ridge_regression(features, target)
    
    # Load corrected p-values (from T024)
    corrected_p_values = {}
    fdr_path = Path("data/results/fdr_corrected_pvalues.json")
    if fdr_path.exists():
        with open(fdr_path, 'r') as f:
            fdr_data = json.load(f)
            corrected_p_values = fdr_data.get('corrected_p_values', {})
    
    # Load CV scores (from T029/T030)
    cv_scores = {}
    cv_path = Path("data/results/cv_scores.json")
    if cv_path.exists():
        with open(cv_path, 'r') as f:
            cv_data = json.load(f)
            cv_scores = cv_data.get('cv_scores', {})
    
    # Save consolidated metrics
    save_model_metrics(
        beta_metrics,
        gaussian_metrics,
        ridge_metrics,
        corrected_p_values,
        cv_scores,
        output_path
    )
    
    # Validate against schema
    if schema_path.exists():
        schema = load_schema(schema_path)
        with open(output_path, 'r') as f:
            output_data = json.load(f)
        if validate_against_schema(output_data, schema):
            logger.info("Output validated against schema")
        else:
            logger.warning("Output validation failed")
    
    logger.info("T027 completed successfully")

if __name__ == "__main__":
    main()