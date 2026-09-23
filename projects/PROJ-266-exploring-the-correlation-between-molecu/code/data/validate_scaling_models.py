"""
T029: Validate scaling law model performance against linear model.

Requirement: Compare AIC/BIC of the power-law model vs. the linear model.
Dependency: T028 (Scaling analysis results must exist in data/processed/scaling_analysis_results.json)
Traceability: FR-029 (Model Validation)
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from scipy import stats

# Import from existing project utilities
from utils.config import get_project_root, get_data_path
from utils.logging import get_logger, setup_logging_for_script

# Ensure we can import from the project's code directory
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

def load_scaling_results() -> Optional[Dict[str, Any]]:
    """Load the scaling analysis results from T028."""
    results_path = get_data_path() / "processed" / "scaling_analysis_results.json"
    if not results_path.exists():
        logger.error(f"Scaling results file not found: {results_path}")
        logger.error("Please ensure T028 has been completed successfully.")
        return None
    
    with open(results_path, 'r') as f:
        return json.load(f)

def load_analysis_data() -> pd.DataFrame:
    """Load the processed analysis data containing descriptors and permeability."""
    data_path = get_data_path() / "processed" / "descriptors_raw.csv"
    if not data_path.exists():
        # Fallback to filtered data if descriptors are not yet computed
        # This should not happen in a normal flow after T014
        filtered_path = get_data_path() / "processed" / "filtered_data.csv"
        if filtered_path.exists():
            logger.warning(f"Using filtered data as fallback: {filtered_path}")
            df = pd.read_csv(filtered_path)
            # We need logPapp for correlation. If descriptors are missing, we can't do the full analysis.
            # For T029, we assume descriptors exist.
            if 'logPapp' not in df.columns:
                raise ValueError("logPapp not found in available data files.")
            return df
        else:
            raise FileNotFoundError("No analysis data found in data/processed/")
    
    df = pd.read_csv(data_path)
    if 'logPapp' not in df.columns:
        # Try to merge with filtered data if logPapp is missing in descriptors
        filtered_path = get_data_path() / "processed" / "filtered_data.csv"
        if filtered_path.exists():
            filtered_df = pd.read_csv(filtered_path)
            # Merge on smiles if possible, or assume order is preserved
            # Assuming order is preserved for simplicity as per pipeline design
            if len(df) == len(filtered_df):
                df['logPapp'] = filtered_df['logPapp']
            else:
                raise ValueError("Data length mismatch and no merge key found.")
        else:
            raise ValueError("logPapp column missing in descriptors data and no fallback found.")
    
    return df

def fit_linear_model(dihedral_variance: np.ndarray, logPapp: np.ndarray) -> Tuple[float, float, float, float]:
    """
    Fit a simple linear model: logPapp ~ dihedral_variance
    Returns: (slope, intercept, aic, bic)
    """
    # Filter out NaNs
    mask = ~(np.isnan(dihedral_variance) | np.isnan(logPapp))
    x = dihedral_variance[mask]
    y = logPapp[mask]
    
    if len(x) < 2:
        raise ValueError("Insufficient data points for linear regression.")
    
    # Fit linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    # Calculate residuals
    y_pred = slope * x + intercept
    residuals = y - y_pred
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    
    # Calculate AIC and BIC
    n = len(y)
    k = 2  # slope and intercept
    
    # AIC = 2k - 2ln(L)
    # For linear regression with normal errors: L ~ -n/2 * ln(2*pi*sigma^2) - SS_res/(2*sigma^2)
    # We use the simplified AIC formula for linear regression: AIC = n * ln(SS_res/n) + 2k
    # Or more precisely: AIC = n * ln(2*pi) + n * ln(SS_res/n) + n + 2k
    # We'll use the standard form: AIC = 2k + n * ln(SS_res/n)
    sigma_sq = ss_res / n
    if sigma_sq <= 0:
        sigma_sq = 1e-10  # Avoid log(0)
    
    aic = 2 * k + n * np.log(sigma_sq) + n * (1 + np.log(2 * np.pi))
    bic = k * np.log(n) + n * np.log(sigma_sq) + n * (1 + np.log(2 * np.pi))
    
    return slope, intercept, aic, bic

def fit_power_law_model(dihedral_variance: np.ndarray, logPapp: np.ndarray) -> Tuple[float, float, float, float]:
    """
    Fit a power-law model: log(Permeability) ~ log(Flexibility) + log(Complexity)
    For T029, we focus on the core relationship: logPapp ~ log(dihedral_variance)
    Returns: (exponent, intercept, aic, bic)
    """
    # Filter out NaNs and non-positive values for log
    mask = ~(np.isnan(dihedral_variance) | np.isnan(logPapp))
    x = dihedral_variance[mask]
    y = logPapp[mask]
    
    # Filter for positive values to take log
    valid_mask = (x > 0) & (y > 0)
    if not np.any(valid_mask):
        raise ValueError("No valid positive data points for power-law fitting.")
    
    x = x[valid_mask]
    y = y[valid_mask]
    
    if len(x) < 2:
        raise ValueError("Insufficient data points for power-law regression.")
    
    # Transform to log-log space
    log_x = np.log(x)
    log_y = np.log(y)
    
    # Fit linear regression in log-log space
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_x, log_y)
    
    # Calculate residuals in log space
    log_y_pred = slope * log_x + intercept
    residuals = log_y - log_y_pred
    ss_res = np.sum(residuals ** 2)
    
    # Calculate AIC and BIC
    n = len(log_y)
    k = 2  # exponent and intercept
    
    sigma_sq = ss_res / n
    if sigma_sq <= 0:
        sigma_sq = 1e-10
    
    aic = 2 * k + n * np.log(sigma_sq) + n * (1 + np.log(2 * np.pi))
    bic = k * np.log(n) + n * np.log(sigma_sq) + n * (1 + np.log(2 * np.pi))
    
    return slope, intercept, aic, bic

def compare_models(linear_metrics: Dict[str, float], power_metrics: Dict[str, float]) -> Dict[str, Any]:
    """Compare AIC and BIC between linear and power-law models."""
    comparison = {
        "linear_model": linear_metrics,
        "power_law_model": power_metrics,
        "aic_difference": linear_metrics["aic"] - power_metrics["aic"],
        "bic_difference": linear_metrics["bic"] - power_metrics["bic"],
        "preferred_model": None,
        "interpretation": ""
    }
    
    # Lower AIC/BIC is better
    if comparison["aic_difference"] > 0:
        comparison["preferred_model"] = "power_law"
        comparison["interpretation"] = "Power-law model has lower AIC (better fit)"
    elif comparison["aic_difference"] < 0:
        comparison["preferred_model"] = "linear"
        comparison["interpretation"] = "Linear model has lower AIC (better fit)"
    else:
        comparison["preferred_model"] = "tie"
        comparison["interpretation"] = "AIC values are equal"
    
    # Also check BIC
    if comparison["bic_difference"] > 0:
        if comparison["preferred_model"] == "linear":
            comparison["interpretation"] += " but BIC favors power-law"
        elif comparison["preferred_model"] == "power_law":
            comparison["interpretation"] += " and BIC also favors power-law"
        else:
            comparison["interpretation"] = "BIC favors power-law"
    elif comparison["bic_difference"] < 0:
        if comparison["preferred_model"] == "power_law":
            comparison["interpretation"] += " but BIC favors linear"
        elif comparison["preferred_model"] == "linear":
            comparison["interpretation"] += " and BIC also favors linear"
        else:
            comparison["interpretation"] = "BIC favors linear"
    
    return comparison

def write_validation_results(comparison: Dict[str, Any], output_path: Path):
    """Write the model comparison results to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(comparison, f, indent=2)
    logger.info(f"Validation results written to {output_path}")

def main():
    """Main entry point for T029."""
    logger.info("Starting T029: Validate scaling law model performance against linear model")
    
    # Load scaling results (from T028)
    scaling_results = load_scaling_results()
    if scaling_results is None:
        logger.error("Failed to load scaling results. Exiting.")
        return 1
    
    # Load analysis data
    try:
        df = load_analysis_data()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load analysis data: {e}")
        return 1
    
    # Extract necessary columns
    if 'dihedral_variance' not in df.columns:
        logger.error("dihedral_variance column not found in data.")
        return 1
    
    if 'logPapp' not in df.columns:
        logger.error("logPapp column not found in data.")
        return 1
    
    dihedral_variance = df['dihedral_variance'].values
    logPapp = df['logPapp'].values
    
    # Fit linear model
    try:
        linear_slope, linear_intercept, linear_aic, linear_bic = fit_linear_model(dihedral_variance, logPapp)
        linear_metrics = {
            "slope": float(linear_slope),
            "intercept": float(linear_intercept),
            "aic": float(linear_aic),
            "bic": float(linear_bic)
        }
        logger.info(f"Linear model fitted: AIC={linear_aic:.4f}, BIC={linear_bic:.4f}")
    except Exception as e:
        logger.error(f"Failed to fit linear model: {e}")
        return 1
    
    # Fit power-law model
    try:
        power_exponent, power_intercept, power_aic, power_bic = fit_power_law_model(dihedral_variance, logPapp)
        power_metrics = {
            "exponent": float(power_exponent),
            "intercept": float(power_intercept),
            "aic": float(power_aic),
            "bic": float(power_bic)
        }
        logger.info(f"Power-law model fitted: AIC={power_aic:.4f}, BIC={power_bic:.4f}")
    except Exception as e:
        logger.error(f"Failed to fit power-law model: {e}")
        return 1
    
    # Compare models
    comparison = compare_models(linear_metrics, power_metrics)
    
    # Write results
    output_path = get_data_path() / "processed" / "scaling_model_validation.json"
    write_validation_results(comparison, output_path)
    
    # Update scaling_analysis_results.json with validation info
    scaling_results['model_validation'] = comparison
    scaling_results_path = get_data_path() / "processed" / "scaling_analysis_results.json"
    with open(scaling_results_path, 'w') as f:
        json.dump(scaling_results, f, indent=2)
    
    logger.info("T029 completed successfully.")
    logger.info(f"Preferred model: {comparison['preferred_model']}")
    logger.info(f"Interpretation: {comparison['interpretation']}")
    
    return 0

if __name__ == "__main__":
    # Setup logging
    log_path = get_data_path().parent / "logs" / "t029_validation.log"
    setup_logging_for_script(log_path)
    
    exit_code = main()
    sys.exit(exit_code)