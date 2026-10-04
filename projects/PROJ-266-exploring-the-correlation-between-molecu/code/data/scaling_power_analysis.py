import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from statsmodels.stats.power import tt_solve_power, FTestPower
from scipy.stats import t
import statsmodels.api as sm

# Import project utilities
from utils.logging import get_logger, setup_logging_for_script
from utils.config import get_project_root

# Import existing analysis functions from sibling module
from data.analysis import load_analysis_data

logger = get_logger(__name__)

def calculate_effect_size_for_exponent(
    observed_exponent: float,
    null_exponent: float,
    sample_size: int,
    predictor_std: float,
    residual_std: float
) -> float:
    """
    Calculate Cohen's d (effect size) for a power law exponent test.
    
    In a log-log regression: log(Y) = beta * log(X) + intercept
    We test H0: beta = null_exponent vs H1: beta = observed_exponent.
    
    Effect size (Cohen's d for regression coefficients) is approximated as:
    d = |beta_observed - beta_null| / (SE_beta)
    where SE_beta = residual_std / (predictor_std * sqrt(n-1))
    
    Args:
        observed_exponent: The fitted scaling exponent from the power law model
        null_exponent: The null hypothesis value for the exponent
        sample_size: Number of observations (n)
        predictor_std: Standard deviation of log(X) (the predictor)
        residual_std: Standard deviation of residuals from the fitted model
        
    Returns:
        Cohen's d effect size
    """
    if sample_size < 2:
        raise ValueError("Sample size must be at least 2")
        
    # Standard error of the slope coefficient
    se_beta = residual_std / (predictor_std * np.sqrt(sample_size - 1))
    
    if se_beta == 0:
        # Avoid division by zero; if residuals are 0, effect is infinite
        return float('inf')
        
    effect_size = abs(observed_exponent - null_exponent) / se_beta
    return effect_size

def run_power_analysis(
    observed_exponent: float,
    null_exponents: List[float],
    sample_size: int,
    predictor_std: float,
    residual_std: float,
    alpha: float = 0.05,
    power_target: float = 0.80
) -> Dict[str, Any]:
    """
    Perform statistical power analysis and hypothesis testing for scaling exponents.
    
    This function:
    1. Calculates the detectable effect size for a range of null exponents
    2. Tests if the observed exponent is statistically distinguishable from each null
    3. Computes statistical power for detecting the observed effect
    4. Applies FDR correction to p-values
    
    Args:
        observed_exponent: The fitted scaling exponent from the power law model
        null_exponents: List of null hypothesis values to test against
        sample_size: Number of observations
        predictor_std: Standard deviation of the predictor (log(Flexibility))
        residual_std: Standard deviation of model residuals
        alpha: Significance level for hypothesis tests (default 0.05)
        power_target: Target statistical power (default 0.80)
        
    Returns:
        Dictionary containing power analysis results and hypothesis test outcomes
    """
    results = {
        "observed_exponent": observed_exponent,
        "sample_size": sample_size,
        "predictor_std": predictor_std,
        "residual_std": residual_std,
        "alpha": alpha,
        "power_target": power_target,
        "hypothesis_tests": []
    }
    
    # Collect p-values for FDR correction
    p_values = []
    
    for null_exp in null_exponents:
        # Calculate effect size
        effect_size = calculate_effect_size_for_exponent(
            observed_exponent, null_exp, sample_size, predictor_std, residual_std
        )
        
        # Calculate t-statistic for the test
        # t = (beta_obs - beta_null) / SE_beta
        se_beta = residual_std / (predictor_std * np.sqrt(sample_size - 1))
        if se_beta == 0:
            t_stat = float('inf') if observed_exponent != null_exp else 0.0
        else:
            t_stat = (observed_exponent - null_exp) / se_beta
        
        # Calculate two-tailed p-value using t-distribution
        df = sample_size - 2  # degrees of freedom for simple linear regression
        if df <= 0:
            p_value = 1.0
        else:
            p_value = 2 * (1 - t.cdf(abs(t_stat), df))
        
        p_values.append(p_value)
        
        # Calculate statistical power for this effect size
        # Using t-test power calculation
        # For regression, we can approximate using the non-centrality parameter
        ncp = abs(t_stat)
        if df > 0:
            # Power = P(|t| > t_crit | H1 is true)
            # We use the non-central t-distribution
            from scipy.stats import nct
            t_crit = t.ppf(1 - alpha/2, df)
            power = 1 - nct.cdf(t_crit, df, ncp) + nct.cdf(-t_crit, df, ncp)
        else:
            power = 0.0
        
        test_result = {
            "null_exponent": null_exp,
            "observed_exponent": observed_exponent,
            "effect_size": effect_size,
            "t_statistic": t_stat,
            "degrees_of_freedom": df,
            "p_value": p_value,
            "power": power,
            "significant_at_alpha": p_value < alpha
        }
        results["hypothesis_tests"].append(test_result)
    
    # Apply Benjamini-Hochberg FDR correction to p-values
    if len(p_values) > 0:
        sorted_indices = np.argsort(p_values)
        sorted_p_values = np.array(p_values)[sorted_indices]
        n_tests = len(sorted_p_values)
        
        # BH critical values
        bh_thresholds = np.arange(1, n_tests + 1) * (alpha / n_tests)
        
        # Find the largest k where p_(k) <= threshold_k
        fdr_corrected = np.ones(n_tests) * 1.0
        for i in range(n_tests - 1, -1, -1):
            if sorted_p_values[i] <= bh_thresholds[i]:
                # All tests up to i are significant
                fdr_corrected[:i+1] = sorted_p_values[i] * n_tests / (i + 1)
                break
        
        # Ensure monotonicity (corrected p-values should be non-decreasing)
        for i in range(1, n_tests):
            fdr_corrected[i] = min(fdr_corrected[i], fdr_corrected[i-1])
        
        # Map back to original order
        fdr_p_values = np.zeros(n_tests)
        fdr_p_values[sorted_indices] = fdr_corrected
        
        # Update results with FDR-corrected p-values
        for i, test_result in enumerate(results["hypothesis_tests"]):
            test_result["fdr_p_value"] = float(fdr_p_values[i])
            test_result["significant_after_fdr"] = fdr_p_values[i] < alpha
    else:
        for test_result in results["hypothesis_tests"]:
            test_result["fdr_p_value"] = 1.0
            test_result["significant_after_fdr"] = False
    
    # Summary statistics
    significant_count = sum(1 for t in results["hypothesis_tests"] if t["significant_after_fdr"])
    results["summary"] = {
        "total_tests": len(null_exponents),
        "significant_after_fdr": significant_count,
        "rejection_rate": significant_count / len(null_exponents) if len(null_exponents) > 0 else 0.0
    }
    
    return results

def main():
    """
    Main entry point for statistical power analysis of scaling exponents.
    
    This function:
    1. Loads the scaling analysis results from T027
    2. Extracts the observed exponent and model statistics
    3. Runs power analysis against a range of null hypotheses
    4. Saves results to data/processed/scaling_analysis_results.json
    """
    # Setup logging
    log_path = setup_logging_for_script(__file__)
    logger.info("Starting statistical power analysis for scaling exponents (T028)")
    
    project_root = get_project_root()
    processed_dir = project_root / "data" / "processed"
    output_path = processed_dir / "scaling_analysis_results.json"
    
    # Ensure output directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Load scaling analysis results from T027
    scaling_results_path = processed_dir / "scaling_analysis_results.json"
    
    if not scaling_results_path.exists():
        logger.error(f"Scaling analysis results not found at {scaling_results_path}")
        logger.error("T027 must be completed before running T028")
        sys.exit(1)
    
    try:
        with open(scaling_results_path, 'r') as f:
            scaling_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load scaling analysis results: {e}")
        sys.exit(1)
    
    # Check if scaling analysis was skipped
    if scaling_data.get("status") == "SKIPPED":
        logger.info("Scaling law analysis was skipped (R² >= 0.3). Skipping power analysis.")
        # Still create output with skipped status
        output_data = {
            "status": "SKIPPED",
            "reason": "Scaling law analysis was skipped in T026 (R² >= 0.3)",
            "power_analysis": None
        }
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Saved skipped power analysis results to {output_path}")
        return
    
    # Extract required parameters from scaling results
    if "power_law_model" not in scaling_data:
        logger.error("Power law model results not found in scaling analysis")
        sys.exit(1)
    
    model_results = scaling_data["power_law_model"]
    
    if "exponent" not in model_results:
        logger.error("Scaling exponent not found in model results")
        sys.exit(1)
    
    observed_exponent = model_results["exponent"]
    sample_size = scaling_data.get("sample_size", 0)
    
    if sample_size < 2:
        logger.error(f"Insufficient sample size for power analysis: {sample_size}")
        sys.exit(1)
    
    # Load analysis data to get predictor statistics
    try:
        analysis_data = load_analysis_data()
        logger.info(f"Loaded {len(analysis_data)} records for power analysis")
    except Exception as e:
        logger.error(f"Failed to load analysis data: {e}")
        sys.exit(1)
    
    # Calculate predictor statistics (log(Flexibility))
    # Assuming the power law model used dihedral_variance as the flexibility metric
    if "dihedral_variance" not in analysis_data.columns:
        logger.error("dihedral_variance column not found in analysis data")
        sys.exit(1)
    
    if "logPapp" not in analysis_data.columns:
        logger.error("logPapp column not found in analysis data")
        sys.exit(1)
    
    # Filter for valid data
    valid_data = analysis_data.dropna(subset=["dihedral_variance", "logPapp"])
    valid_data = valid_data[valid_data["dihedral_variance"] > 0]  # log requires positive values
    
    if len(valid_data) < 2:
        logger.error("Insufficient valid data points for power analysis")
        sys.exit(1)
    
    # Compute log-transformed variables
    log_flexibility = np.log(valid_data["dihedral_variance"])
    log_permeability = np.log10(valid_data["logPapp"])
    
    # Fit the power law model to get residuals
    # log(P) = exponent * log(F) + intercept
    X = sm.add_constant(log_flexibility)
    y = log_permeability
    
    model = sm.OLS(y, X).fit()
    residuals = model.resid
    
    predictor_std = np.std(log_flexibility, ddof=1)
    residual_std = np.std(residuals, ddof=1)
    
    logger.info(f"Predictor std: {predictor_std:.4f}")
    logger.info(f"Residual std: {residual_std:.4f}")
    logger.info(f"Observed exponent: {observed_exponent:.4f}")
    
    # Define range of null exponents to test
    # Test from -2 to 2 in increments of 0.25
    null_exponents = [round(x, 2) for x in np.arange(-2.0, 2.25, 0.25)]
    
    logger.info(f"Testing {len(null_exponents)} null hypotheses: {null_exponents}")
    
    # Run power analysis
    power_results = run_power_analysis(
        observed_exponent=observed_exponent,
        null_exponents=null_exponents,
        sample_size=len(valid_data),
        predictor_std=predictor_std,
        residual_std=residual_std,
        alpha=0.05,
        power_target=0.80
    )
    
    # Prepare output
    output_data = {
        "status": "COMPLETED",
        "scaling_analysis_status": scaling_data.get("status", "UNKNOWN"),
        "observed_exponent": observed_exponent,
        "sample_size": len(valid_data),
        "power_analysis": power_results,
        "metadata": {
            "task_id": "T028",
            "description": "Statistical power analysis and hypothesis testing for scaling exponents",
            "methodology": "Cohen's d effect size calculation with Benjamini-Hochberg FDR correction"
        }
    }
    
    # Save results
    try:
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Successfully saved power analysis results to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save power analysis results: {e}")
        sys.exit(1)
    
    # Log summary
    summary = power_results["summary"]
    logger.info(f"Power analysis complete: {summary['significant_after_fdr']}/{summary['total_tests']} null hypotheses rejected after FDR correction")
    
    # Print significant results
    significant_tests = [t for t in power_results["hypothesis_tests"] if t["significant_after_fdr"]]
    if significant_tests:
        logger.info("Significant null hypotheses (after FDR correction):")
        for test in significant_tests:
            logger.info(f"  H0: beta = {test['null_exponent']:.2f} (p={test['fdr_p_value']:.4f})")
    else:
        logger.info("No null hypotheses rejected after FDR correction")

if __name__ == "__main__":
    main()