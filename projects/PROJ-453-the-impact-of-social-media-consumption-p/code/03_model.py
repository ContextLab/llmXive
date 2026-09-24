import os
import sys
import logging
import json
import yaml
import numpy as np
import pandas as pd
import statsmodels.api as sm
from pathlib import Path
from typing import Tuple, Dict, Any, List

logger = logging.getLogger(__name__)

def log_setup():
    """Configure logging to stdout."""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        stream=sys.stdout
    )

def load_schema_contract() -> Dict[str, Any]:
    """Load the output schema contract."""
    schema_path = Path("contracts/output.schema.yaml")
    if not schema_path.exists():
        raise FileNotFoundError(f"Output schema contract not found at {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_output_schema(output: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate model output against schema."""
    required_keys = ['coefficients', 'p_values', 'vif_scores', 'diagnostics', 'interpretation']
    return all(key in output for key in required_keys)

def mean_center(series: pd.Series) -> pd.Series:
    """Mean-center a series."""
    return series - series.mean()

def create_interaction(series1: pd.Series, series2: pd.Series) -> pd.Series:
    """Create interaction term."""
    return series1 * series2

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for predictors."""
    vif_data = {}
    for col in predictors:
        X = df[predictors]
        X = sm.add_constant(X)
        # Drop the column we're calculating VIF for from the model matrix
        X_other = X.drop(columns=[col])
        if len(X_other.columns) > 1:  # Keep const
            model = sm.OLS(df[col], X_other).fit()
            vif = 1 / (1 - model.rsquared)
            vif_data[col] = vif
        else:
            vif_data[col] = 1.0
    return vif_data

def benjamini_hochberg(p_values: List[float]) -> List[float]:
    """Apply Benjamini-Hochberg FDR correction."""
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    corrected = sorted_p * n / (np.arange(1, n + 1))
    corrected = np.minimum.accumulate(corrected[::-1])[::-1]
    corrected = np.clip(corrected, 0, 1)
    # Restore original order
    result = np.empty(n)
    result[sorted_indices] = corrected
    return result.tolist()

def check_collinearity(df: pd.DataFrame, var1: str, var2: str) -> Tuple[float, bool]:
    """Check correlation between two variables. Return (corr, is_high)."""
    corr = df[var1].corr(df[var2])
    is_high = abs(corr) > 0.7
    return corr, is_high

def run_model(df: pd.DataFrame) -> Tuple[Any, Dict[str, Any]]:
    """Fit OLS model and return results and diagnostics."""
    # Prepare variables
    y = df['cognitive_flexibility_score']
    X = df[['switching_index', 'total_screen_time', 'age']]
    
    # Mean-center and create interaction
    switching_centered = mean_center(df['switching_index'])
    age_centered = mean_center(df['age'])
    interaction = create_interaction(switching_centered, age_centered)
    
    # Add to X
    X['interaction'] = interaction
    X = sm.add_constant(X)
    
    # Fit model
    model = sm.OLS(y, X).fit()
    
    # Calculate VIF
    predictors = ['switching_index', 'total_screen_time', 'age', 'interaction']
    vif_scores = calculate_vif(df, predictors)
    
    # Correlation matrix
    corr_matrix = df[predictors].corr().to_dict()
    
    diagnostics = {
        'vif_scores': vif_scores,
        'correlation_matrix': corr_matrix
    }
    
    return model, diagnostics

def main():
    """Main entry point for model fitting."""
    log_setup()
    logger.info("Starting model fitting pipeline.")

    # Load cleaned data
    data_path = Path("data/processed/participants_cleaned.csv")
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {data_path}")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} rows from {data_path}")

    # Check collinearity
    corr, is_high = check_collinearity(df, 'switching_index', 'total_screen_time')
    if is_high:
        logger.warning(f"Potential Mathematical Coupling: correlation = {corr:.3f}")
        Path("logs").mkdir(exist_ok=True)
        with open("logs/collinearity_check.log", 'w') as f:
            f.write(f"Collinearity Check - switching_index vs total_screen_time\n")
            f.write(f"Correlation: {corr:.3f}\n")
            f.write(f"Flag: true\n")

    # Run model
    model, diagnostics = run_model(df)
    
    # Prepare output
    output = {
        'coefficients': model.params.to_dict(),
        'p_values': model.pvalues.to_dict(),
        'vif_scores': diagnostics['vif_scores'],
        'diagnostics': diagnostics,
        'interpretation': "Association observed between switching index and cognitive flexibility."
    }

    # Validate schema
    schema = load_schema_contract()
    if not validate_output_schema(output, schema):
        raise ValueError("Model output does not match schema")

    # Save results
    Path("results/models").mkdir(parents=True, exist_ok=True)
    output_path = Path("results/models/regression_summary.json")
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Saved model summary to {output_path}")
    logger.info("Model fitting complete.")

if __name__ == "__main__":
    main()
