"""
Task T028: Statistical Power Analysis and Hypothesis Testing for Scaling Exponents.

This script performs statistical power analysis using statsmodels to determine
the detectable effect size for specific scaling exponents (0.25, 0.5, 1.0)
given the current sample size derived from the real data processed in previous steps.
It also tests if the estimated scaling exponent is statistically distinguishable
from these null hypotheses.

Output: data/processed/scaling_analysis_results.json
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.power import TTestPower, FTestPower, GofChisquarePower

# Import existing utilities from the project
# We assume the analysis module has the necessary data loading helpers
# If not, we will implement local loading logic based on the known file paths
try:
    from data.analysis import get_project_root, load_analysis_data
except ImportError:
    # Fallback if analysis.py doesn't export these directly or structure differs
    # We will implement local loading logic to ensure robustness
    get_project_root = None
    load_analysis_data = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root_fallback() -> Path:
    """Fallback to get project root if import fails."""
    return Path(__file__).resolve().parent.parent.parent

def load_analysis_data_fallback() -> pd.DataFrame:
    """
    Load the processed data required for analysis.
    We expect the data to be in data/processed/ directory.
    Specifically, we need the descriptors (dihedral_variance) and permeability (logPapp).
    Based on T010, filtered data is in data/processed/filtered_data.csv.
    Based on T014, descriptors are in data/processed/descriptors_raw.csv.
    We need to merge them.
    """
    root = get_project_root_fallback()
    filtered_path = root / "data" / "processed" / "filtered_data.csv"
    descriptors_path = root / "data" / "processed" / "descriptors_raw.csv"

    if not filtered_path.exists():
        raise FileNotFoundError(f"Required input file not found: {filtered_path}")
    if not descriptors_path.exists():
        raise FileNotFoundError(f"Required input file not found: {descriptors_path}")

    df_filtered = pd.read_csv(filtered_path)
    df_descriptors = pd.read_csv(descriptors_path)

    # Merge on 'smiles'
    if 'smiles' not in df_filtered.columns or 'smiles' not in df_descriptors.columns:
        raise ValueError("Merged data must contain 'smiles' column.")

    df = pd.merge(df_filtered, df_descriptors, on='smiles', how='inner')

    # Ensure we have the necessary columns
    required_cols = ['logPapp', 'dihedral_variance']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in merged data.")

    # Drop rows with NaN in key columns
    df = df.dropna(subset=required_cols)
    return df

def calculate_effect_size_for_exponent(
    df: pd.DataFrame,
    target_exponent: float,
    primary_col: str = 'dihedral_variance',
    target_col: str = 'logPapp'
) -> Tuple[float, float]:
    """
    Calculates the effect size (Cohen's d or similar) for a specific scaling exponent.
    In the context of power-law: log(y) = a + b * log(x).
    We test if the slope 'b' is distinguishable from 'target_exponent'.
    """
    x = df[primary_col]
    y = df[target_col]

    # Log transform for power law analysis
    # Avoid log(0) or negative values if any
    x_clean = x[x > 0]
    y_clean = y.loc[x_clean.index]

    if len(x_clean) < 10:
        return np.nan, np.nan

    log_x = np.log(x_clean)
    log_y = np.log(y_clean)

    # Fit linear model: log_y = intercept + slope * log_x
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_x, log_y)

    # The null hypothesis is slope == target_exponent
    # We calculate the t-statistic for this difference
    t_stat = (slope - target_exponent) / std_err
    n = len(x_clean)
    # Two-tailed p-value
    p_val = 2 * (1 - stats.t.cdf(np.abs(t_stat), n - 2))

    # Effect size: Cohen's d for regression slope?
    # Alternatively, we can use the non-centrality parameter for power analysis
    # For TTestPower, effect size is (mean1 - mean2) / std
    # Here, we treat the difference in slopes as the effect.
    # A standard approach for regression slope power:
    # f^2 = R^2 / (1 - R^2)
    # But we are testing a specific value.
    # Let's use the standardized difference: (slope - target) / SE(slope)
    # This is effectively the t-stat.
    # For statsmodels TTestPower, effect_size is Cohen's d.
    # d = (mu - mu0) / sigma.
    # Here, we can approximate the "sigma" of the slope distribution as std_err.
    # So effect_size = (slope - target_exponent) / std_err is the t-stat, not d.
    # However, for a single sample test of mean, d = (mean - mu0) / std_dev.
    # We don't have the std_dev of the slope directly in that form.
    # Let's use the non-centrality parameter logic directly or use FTestPower for regression.
    
    # Simpler approach for "detectable effect size":
    # Given N, alpha, power=0.8, what is the minimum detectable difference in slope?
    # We will calculate this in the main function.
    # Here we just return the observed t-stat and p-value for the specific exponent.
    return t_stat, p_val

def run_power_analysis(
    df: pd.DataFrame,
    exponents: List[float],
    alpha: float = 0.05,
    power_target: float = 0.8,
    primary_col: str = 'dihedral_variance',
    target_col: str = 'logPapp'
) -> Dict[str, Any]:
    """
    Runs power analysis for the given exponents.
    """
    x = df[primary_col]
    y = df[target_col]
    
    x_clean = x[x > 0]
    y_clean = y.loc[x_clean.index]
    n = len(x_clean)

    if n < 10:
        logger.warning(f"Sample size too small ({n}) for reliable power analysis.")
        return {"error": "Insufficient sample size"}

    log_x = np.log(x_clean)
    log_y = np.log(y_clean)

    # Fit model to get residuals and standard error
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_x, log_y)
    r_squared = r_value**2

    results = {
        "sample_size": int(n),
        "observed_slope": float(slope),
        "observed_r_squared": float(r_squared),
        "observed_p_value": float(p_value),
        "standard_error_slope": float(std_err),
        "exponents_tested": [],
        "power_analysis": []
    }

    # Use TTestPower for single sample mean test analogy (slope vs target)
    # Or FTestPower for regression.
    # statsmodels TTestPower.solve(n, alpha, effect_size) -> power
    # We want to find the effect size detectable at power_target.
    # effect_size = TTestPower.solve(n, alpha, power_target, alternative='two-sided')
    # This returns Cohen's d.
    # In our context, d = (slope - target) / std_err_of_slope? No, std_err is for the mean.
    # For regression slope, the standard error is std_err.
    # The "effect size" in terms of slope difference is d_slope = (slope - target) / std_err?
    # Actually, the t-stat is exactly that.
    # So the minimum detectable difference (MDD) in slope = d * std_err.
    
    power_analysis_tool = TTestPower()
    
    for exp in exponents:
        # 1. Calculate observed t-stat and p-value for this exponent
        t_stat, p_val = calculate_effect_size_for_exponent(df, exp, primary_col, target_col)
        
        # 2. Calculate the effect size (Cohen's d) corresponding to the observed difference
        # d_obs = t_stat / sqrt(n) is not quite right for regression slope.
        # Let's stick to the TTestPower logic:
        # We treat the slope estimate as a sample mean with standard error std_err.
        # The "population mean" under H0 is 'exp'.
        # The "sample mean" is 'slope'.
        # The standard deviation of the sampling distribution is std_err.
        # So Cohen's d = (slope - exp) / std_err.
        # Wait, Cohen's d is usually (mean - mu) / sigma (population std dev).
        # Here we have standard error of the mean (slope).
        # If we assume the "population" of slopes has std_dev = std_err * sqrt(n)? No.
        # Let's use the non-centrality parameter approach directly via statsmodels.
        # We want to know: given n, alpha, and a specific effect size (difference in slope),
        # what is the power?
        # Effect size for TTestPower is (mu1 - mu2) / sigma.
        # Here, sigma is the standard deviation of the data, not the standard error of the mean.
        # We need to estimate sigma from the residuals of the regression.
        residuals = log_y - (intercept + slope * log_x)
        sigma_est = np.std(residuals, ddof=2) # ddof=2 because 2 params (slope, intercept)
        
        # The standard error of the slope is sigma_est / (sqrt(n-1) * std(log_x))
        # Let's just use the TTestPower on the slope estimate directly if we treat it as a mean.
        # But the variance of the slope is not the variance of the data.
        # Correct approach:
        # The test statistic is t = (b - b0) / SE(b).
        # Under H0, t ~ t(n-2).
        # Power is P(|t| > t_crit | b != b0).
        # The non-centrality parameter (ncp) = (b - b0) / SE(b).
        # We can use GofChisquarePower or FTestPower?
        # Actually, TTestPower.solve can be used if we define effect_size correctly.
        # effect_size = (b - b0) / sigma_y? No.
        
        # Let's use a simpler approximation:
        # Minimum Detectable Effect (MDE) in terms of slope difference:
        # MDE = t_crit * SE(b) / sqrt(power_factor)?
        # statsmodels TTestPower.solve(n, alpha, power, effect_size) -> returns effect_size
        # But that effect_size is Cohen's d (difference in means / std_dev).
        # Here, difference in means = (slope - target).
        # std_dev = sigma_est (std dev of residuals? No, std dev of y).
        # Let's calculate Cohen's f^2 for the regression model?
        
        # Alternative: Calculate the detectable difference in slope directly.
        # We know SE(slope).
        # The critical t-value for alpha=0.05, df=n-2.
        t_crit = stats.t.ppf(1 - alpha/2, n - 2)
        # The margin of error for 80% power is roughly 2.8 * SE (for 0.5 power it's 1.96*SE)
        # For power=0.8, we need the non-centrality parameter to be ~2.8.
        # ncp = (slope - target) / SE(slope).
        # So detectable difference = 2.8 * SE(slope).
        
        # Let's use statsmodels TTestPower to be precise about the "effect size" definition.
        # We will assume the "effect size" is the standardized difference in slopes:
        # d = (slope - target) / SE(slope) ??? No, that's t.
        # Let's use the formula: Power = 1 - beta.
        # We want to find the 'delta' (difference in slope) such that Power = 0.8.
        # delta = (t_alpha + t_beta) * SE(slope).
        # t_alpha = 1.96 (approx for large n). t_beta = 0.84 (for 80% power).
        # So delta = 2.8 * SE(slope).
        
        detectable_diff = (t_crit + stats.norm.ppf(power_target)) * std_err
        
        results["exponents_tested"].append({
            "exponent": exp,
            "observed_t_stat": float(t_stat) if not np.isnan(t_stat) else None,
            "observed_p_value": float(p_val) if not np.isnan(p_val) else None,
            "is_significant": bool(p_val < alpha) if not np.isnan(p_val) else False,
            "min_detectable_difference": float(detectable_diff),
            "slope_difference_observed": float(abs(slope - exp))
        })

    return results

def main():
    logger.info("Starting T028: Statistical Power Analysis for Scaling Exponents")
    
    try:
        # Load data
        if load_analysis_data:
            df = load_analysis_data()
        else:
            df = load_analysis_data_fallback()
        
        logger.info(f"Loaded {len(df)} records for analysis.")
        
        # Define exponents to test
        exponents = [0.25, 0.5, 1.0]
        
        # Run analysis
        results = run_power_analysis(df, exponents)
        
        # Add metadata
        results["analysis_timestamp"] = str(pd.Timestamp.now())
        results["null_hypothesis"] = "Scaling exponent equals target value"
        results["alternative_hypothesis"] = "Scaling exponent differs from target value"
        results["correction_method"] = "None (individual tests per exponent)" # FDR applied if multiple tests, but here we test specific values.
        
        # Output
        root = get_project_root_fallback()
        output_path = root / "data" / "processed" / "scaling_analysis_results.json"
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Power analysis results saved to {output_path}")
        
        # Verify file exists
        if not output_path.exists():
            raise RuntimeError("Output file was not created.")
            
        logger.info("T028 completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during T028 execution: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
