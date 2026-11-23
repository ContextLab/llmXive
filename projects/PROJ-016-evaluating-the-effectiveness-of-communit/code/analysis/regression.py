import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant

# Ensure logging is configured
try:
    from logging_config import get_logger
    logger = get_logger()
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {file_path}")
        return None

def save_json_file(file_path: Path, data: Dict[str, Any]) -> bool:
    """Save data to a JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Failed to save JSON file {file_path}: {e}")
        return False

def load_regression_results(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load regression results from a JSON file."""
    return load_json_file(file_path)

def save_regression_results_primary(file_path: Path, results: Dict[str, Any]) -> bool:
    """Save primary regression results to a JSON file."""
    return save_json_file(file_path, results)

def generate_associational_flag(file_path: Path) -> bool:
    """Generate and save the associational flag."""
    data = {"is_associational": True}
    return save_json_file(file_path, data)

def run_sensitivity_analysis_no_gdp(data: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """Run regression without GDP controls."""
    try:
        # Prepare data
        y = data['land_use_change']
        X = data[['regime_type', 'population_density']]
        X = add_constant(X)

        model = OLS(y, X).fit()

        return {
            "model_type": "No GDP Model",
            "coefficients": model.params.to_dict(),
            "p_values": model.pvalues.to_dict(),
            "r_squared": model.rsquared,
            "adj_r_squared": model.rsquared_adj
        }
    except Exception as e:
        logger.error(f"Sensitivity analysis (No GDP) failed: {e}")
        return None

def calculate_sensitivity_change(full_model: Dict, no_gdp_model: Dict) -> float:
    """Calculate percentage change in CBNRM coefficient."""
    try:
        full_coef = full_model['coefficients'].get('regime_type', 0)
        no_gdp_coef = no_gdp_model['coefficients'].get('regime_type', 0)
        
        if full_coef == 0:
            return 0.0
        
        return ((no_gdp_coef - full_coef) / full_coef) * 100
    except Exception as e:
        logger.error(f"Failed to calculate sensitivity change: {e}")
        return 0.0

def run_nonlinearity_check(data: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Run non-linearity robustness check by adding a quadratic term for regime_type.
    Tests significance of the quadratic term and saves results.
    """
    try:
        # Prepare data
        y = data['land_use_change']
        
        # Create quadratic term
        data = data.copy()
        data['regime_type_sq'] = data['regime_type'] ** 2
        
        X = data[['regime_type', 'regime_type_sq', 'gdp_per_capita', 'population_density']]
        X = add_constant(X)

        # Check for multicollinearity or singular matrix issues
        if X.isna().any().any():
            logger.warning("NaN values detected in design matrix for non-linearity check.")
            return None

        model = OLS(y, X).fit()

        # Extract results for the quadratic term
        quad_coef = model.params.get('regime_type_sq', 0)
        quad_pvalue = model.pvalues.get('regime_type_sq', 1.0)
        quad_se = model.bse.get('regime_type_sq', 0.0)

        # Determine significance
        is_significant = quad_pvalue < 0.05

        results = {
            "model_type": "Non-Linearity Check (Quadratic)",
            "quadratic_term": {
                "coefficient": float(quad_coef),
                "standard_error": float(quad_se),
                "p_value": float(quad_pvalue),
                "is_significant": bool(is_significant)
            },
            "full_model_params": {k: float(v) for k, v in model.params.to_dict().items()},
            "full_model_pvalues": {k: float(v) for k, v in model.pvalues.to_dict().items()},
            "r_squared": float(model.rsquared),
            "adj_r_squared": float(model.rsquared_adj),
            "f_statistic": float(model.fvalue),
            "f_pvalue": float(model.f_pvalue)
        }

        return results

    except Exception as e:
        logger.error(f"Non-linearity check failed: {e}")
        return None

def main():
    """Main entry point for non-linearity robustness check."""
    logger.info("Starting Non-linearity Robustness Check (T025b)...")

    # Paths
    processed_dir = Path("data/processed")
    classified_panel_path = processed_dir / "classified_panel.csv"
    output_path = processed_dir / "regression_results_nonlinear.json"

    # Load classified panel data
    if not classified_panel_path.exists():
        logger.error(f"Input file not found: {classified_panel_path}")
        logger.error("Cannot proceed with non-linearity check without classified_panel.csv")
        # Create empty output to prevent downstream failure as per spec
        save_json_file(output_path, {"error": "Input data missing", "status": "failed"})
        return

    try:
        data = pd.read_csv(classified_panel_path)
        logger.info(f"Loaded {len(data)} rows from {classified_panel_path}")
    except Exception as e:
        logger.error(f"Failed to load classified_panel.csv: {e}")
        save_json_file(output_path, {"error": str(e), "status": "failed"})
        return

    # Check for required columns
    required_cols = ['land_use_change', 'regime_type', 'gdp_per_capita', 'population_density']
    missing_cols = [col for col in required_cols if col not in data.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        save_json_file(output_path, {"error": f"Missing columns: {missing_cols}", "status": "failed"})
        return

    # Run non-linearity check
    results = run_nonlinearity_check(data)

    if results is None:
        logger.error("Non-linearity check returned no results.")
        save_json_file(output_path, {"error": "Check failed to produce results", "status": "failed"})
        return

    # Save results
    if save_json_file(output_path, results):
        logger.info(f"Non-linearity results saved to {output_path}")
    else:
        logger.error("Failed to save non-linearity results.")

    logger.info("Non-linearity Robustness Check (T025b) completed.")

if __name__ == "__main__":
    main()