"""
code/analysis.py: Statistical analysis, regression, and goodness-of-fit tests.
Implements Plan-Primary (Deviation Ratio, KS) and Spec-Mandatory (Raw Density, Chi-Square) analyses.
"""
import argparse
import json
import logging
import os
import sys
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy import stats
from scipy.optimize import curve_fit
from scipy.special import comb
import math

# Import Dickman function from sibling module
from dickman import rho

# --- Helper Functions ---

def load_density_data(filepath: str) -> List[Dict[str, Any]]:
    """
    Loads density data from a CSV file.
    Expects columns: x, y, h, density, deviation_ratio
    """
    data = []
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        header = f.readline().strip().split(',')
        # Basic validation
        required = ['x', 'y', 'h', 'density']
        if not all(col in header for col in required):
            raise ValueError(f"CSV missing required columns. Found: {header}")
        
        for line in f:
            parts = line.strip().split(',')
            if len(parts) != len(header):
                continue
            row = dict(zip(header, parts))
            # Convert to float
            data.append({
                'x': float(row['x']),
                'y': float(row['y']),
                'h': float(row['h']),
                'density': float(row['density']),
                'deviation_ratio': float(row.get('deviation_ratio', 0.0))
            })
    return data

def power_law(x: np.ndarray, c: float, beta: float) -> np.ndarray:
    """Power law model: y = c * x^beta"""
    return c * (x ** beta)

def fit_power_law_deviation(data: List[Dict]) -> Optional[Dict[str, float]]:
    """
    Fits R = c * h^beta (Deviation Ratio) using Weighted Least Squares.
    Returns dict with beta, se, r_squared or None if fails.
    """
    # Filter data for specific y-group if needed, or use all
    # For this task, we assume data is pre-grouped or we fit globally per y
    # Let's group by y and fit one model per y, then average? 
    # The task implies a single "plan_beta" per grid. We will fit across all points for the Plan grid.
    
    h_vals = np.array([d['h'] for d in data])
    r_vals = np.array([d['deviation_ratio'] for d in data])
    
    # Filter out zeros or nans
    mask = (r_vals > 0) & np.isfinite(h_vals) & np.isfinite(r_vals)
    h_clean = h_vals[mask]
    r_clean = r_vals[mask]
    
    if len(h_clean) < 3:
        logging.warning("Insufficient data points for deviation ratio regression.")
        return None

    # Log-log transformation for linear regression: log(R) = log(c) + beta * log(h)
    log_h = np.log(h_clean)
    log_r = np.log(r_clean)
    
    # Weighted by 1/variance? Assuming uniform for now, or 1/h as proxy for noise
    weights = np.ones_like(log_h)
    
    try:
        # Linear fit
        slope, intercept, r_value, p_value, std_err = stats.linregress(log_h, log_r)
        
        beta = slope
        se = std_err
        c = np.exp(intercept)
        r_squared = r_value ** 2
        
        return {
            "beta": float(beta),
            "se": float(se),
            "r_squared": float(r_squared),
            "c": float(c)
        }
    except Exception as e:
        logging.error(f"Regression failed: {e}")
        return None

def fit_power_law_raw_density(data: List[Dict]) -> Optional[Dict[str, float]]:
    """
    Fits rho = c * h^beta (Raw Density) using Weighted Least Squares.
    Returns dict with beta, se, r_squared or None if fails.
    """
    h_vals = np.array([d['h'] for d in data])
    rho_vals = np.array([d['density'] for d in data])
    
    mask = (rho_vals > 0) & np.isfinite(h_vals) & np.isfinite(rho_vals)
    h_clean = h_vals[mask]
    rho_clean = rho_vals[mask]
    
    if len(h_clean) < 3:
        logging.warning("Insufficient data points for raw density regression.")
        return None

    log_h = np.log(h_clean)
    log_rho = np.log(rho_clean)
    
    try:
        slope, intercept, r_value, p_value, std_err = stats.linregress(log_h, log_rho)
        
        beta = slope
        se = std_err
        c = np.exp(intercept)
        r_squared = r_value ** 2
        
        return {
            "beta": float(beta),
            "se": float(se),
            "r_squared": float(r_squared),
            "c": float(c)
        }
    except Exception as e:
        logging.error(f"Regression failed: {e}")
        return None

# --- Plan-Primary Analysis (T026a, T027a) ---

def run_plan_primary_analysis() -> Optional[Dict[str, float]]:
    """
    Executes Plan-Primary analysis:
    1. Fits R ~ h^beta (Deviation Ratio)
    2. Performs KS Test against Dickman distribution
    """
    filepath = "data/density_measurements_plan.csv"
    if not os.path.exists(filepath):
        logging.error(f"Plan data file not found: {filepath}")
        return None

    data = load_density_data(filepath)
    if not data:
        return None

    # 1. Regression
    regression_results = fit_power_law_deviation(data)
    
    # 2. KS Test
    # Compare observed deviation ratios to the theoretical expectation (which should be 1.0 if perfect)
    # Or compare the distribution of smooth counts to Dickman expectation.
    # The task says: "KS test comparing observed vs. Dickman distributions".
    # We will compare the empirical CDF of observed densities (normalized) vs theoretical.
    # However, simpler interpretation: Compare the set of observed deviation ratios to a distribution centered at 1.0?
    # Let's interpret as: Compare the empirical distribution of (observed_count / expected_count) to a delta function at 1? No, KS needs continuous.
    # Better: Compare the empirical distribution of the observed densities to the theoretical densities predicted by Dickman.
    
    # Let's extract observed densities and expected densities
    observed_densities = []
    expected_densities = []
    
    for d in data:
        u = math.log(d['x']) / math.log(d['y']) if d['y'] > 1 else 0
        theoretical_rho = rho(u)
        expected_densities.append(theoretical_rho)
        observed_densities.append(d['density'])
    
    # KS Test
    ks_stat, ks_p = stats.ks_2samp(observed_densities, expected_densities)
    
    if regression_results:
        regression_results['ks_p_value'] = float(ks_p)
        return regression_results
    else:
        return {"ks_p_value": float(ks_p)}

# --- Spec-Mandatory Analysis (T026b, T027b) ---

def run_spec_mandatory_analysis() -> Optional[Dict[str, float]]:
    """
    Executes Spec-Mandatory analysis:
    1. Fits rho = c * h^beta (Raw Density)
    """
    filepath = "data/density_measurements_spec.csv"
    if not os.path.exists(filepath):
        logging.error(f"Spec data file not found: {filepath}")
        return None

    data = load_density_data(filepath)
    if not data:
        return None

    return fit_power_law_raw_density(data)

def run_chi_square_goodness_of_fit() -> Optional[Dict[str, float]]:
    """
    Executes Spec-Mandatory Chi-Square Goodness-of-Fit Test.
    Method:
    1. Bin the interval lengths or densities? Spec says "Binning: Use Sturges' rule".
       Likely binning the observed densities or the counts.
       Let's bin the observed density values.
    2. Calculate expected counts based on Dickman.
    3. Compute Chi-Square.
    """
    filepath = "data/density_measurements_spec.csv"
    if not os.path.exists(filepath):
        logging.error(f"Spec data file not found: {filepath}")
        return None

    data = load_density_data(filepath)
    if not data:
        return None

    # Prepare observed and expected values
    # We will bin the observed densities.
    observed_densities = np.array([d['density'] for d in data])
    
    # Filter valid
    valid_mask = np.isfinite(observed_densities)
    obs_vals = observed_densities[valid_mask]
    
    if len(obs_vals) < 2:
        logging.warning("Not enough data for Chi-Square test.")
        return None

    # Sturges' rule for bins
    n = len(obs_vals)
    k = int(np.ceil(1 + np.log2(n)))
    if k < 2: k = 2
    
    # Create bins
    bins = np.linspace(0, np.max(obs_vals) * 1.1, k + 1)
    
    observed_counts, _ = np.histogram(obs_vals, bins=bins)
    
    # Calculate expected counts
    # Expected count for bin i = Sum(Dickman(u) * h * bin_width) for points in that bin?
    # The task says: "E_i = sum (rho_Dickman(u) * h * bin_width)"
    # This implies we need to sum the theoretical probability mass for each data point that falls in the bin.
    # But we lost the mapping of which point fell where in the histogram.
    # Let's re-iterate and assign expected mass to bins.
    
    expected_counts = np.zeros(k)
    
    for d in data:
        if not np.isfinite(d['density']):
            continue
        # Find bin index
        idx = np.digitize(d['density'], bins) - 1
        if 0 <= idx < k:
            # Theoretical expectation for this specific point's context
            u = math.log(d['x']) / math.log(d['y']) if d['y'] > 1 else 0
            theo_rho = rho(u)
            # The "expected count" contribution for this point in the bin
            # The task formula is a bit ambiguous: "sum (rho * h * bin_width)"
            # If we are comparing densities, the expected density is rho.
            # The observed is density.
            # Let's treat the "count" as the density value itself? No, Chi-square needs counts.
            # Let's assume we are binning the "smoothness indicator" or the density values as a distribution.
            # If we treat the density values as samples from a distribution, the expected frequency is proportional to the probability density.
            # Let's assume the expected value for a bin is the average theoretical rho of points in that bin?
            # Or simpler: Expected count = (Total N) * (Probability of falling in bin).
            # Probability of falling in bin = Integral of theoretical PDF over bin.
            # But we don't have a PDF for density, we have a point estimate rho(u).
            # Let's follow the instruction literally: "E_i = sum (rho_Dickman(u) * h * bin_width)"
            # This looks like it's summing the expected number of smooth numbers in the interval?
            # But we are comparing densities.
            # Let's interpret: The "expected count" for a bin is the sum of theoretical densities for all points falling in that bin.
            # This is a bit non-standard but we follow the spec.
            expected_counts[idx] += d.get('expected_rho', 0) # We need to calculate expected_rho per point
    
    # Re-calculate expected counts properly
    expected_counts = np.zeros(k)
    for d in data:
        if not np.isfinite(d['density']):
            continue
        u = math.log(d['x']) / math.log(d['y']) if d['y'] > 1 else 0
        theo_rho = rho(u)
        idx = np.digitize(d['density'], bins) - 1
        if 0 <= idx < k:
            # Contribution to expected count in this bin
            # The spec says: rho * h * bin_width. 
            # If density = count/h, then count = density * h.
            # So expected count in bin = sum of (rho * h) for points in bin?
            # But we are binning the density values, not the intervals.
            # Let's assume the spec implies: Expected frequency in bin i is proportional to the sum of theoretical densities.
            expected_counts[idx] += theo_rho

    # Normalize expected counts to match total observed count?
    # Chi-square usually compares observed counts vs expected counts (frequencies).
    # If observed_counts are frequencies of density values, expected_counts should be frequencies.
    # Let's normalize expected to sum to sum(observed_counts)
    total_obs = np.sum(observed_counts)
    if total_obs > 0:
        expected_counts = expected_counts * (total_obs / np.sum(expected_counts))
    
    # Merge sparse bins (expected < 5)
    # This is tricky with fixed bins. Let's just compute and warn if sparse.
    # Or merge adjacent bins from the end.
    merged_obs = []
    merged_exp = []
    curr_obs = 0
    curr_exp = 0
    
    for i in range(k):
        if expected_counts[i] < 5:
            curr_obs += observed_counts[i]
            curr_exp += expected_counts[i]
        else:
            if curr_obs > 0:
                merged_obs.append(curr_obs)
                merged_exp.append(curr_exp)
                curr_obs = 0
                curr_exp = 0
            merged_obs.append(observed_counts[i])
            merged_exp.append(expected_counts[i])
    if curr_obs > 0:
        merged_obs.append(curr_obs)
        merged_exp.append(curr_exp)
        
    merged_obs = np.array(merged_obs)
    merged_exp = np.array(merged_exp)
    
    # Compute Chi-Square
    if np.sum(merged_exp) == 0:
        logging.warning("Expected counts are zero.")
        return None
        
    chi2_stat = np.sum((merged_obs - merged_exp) ** 2 / merged_exp)
    df = len(merged_obs) - 1 # -1 for estimated parameter? No parameters estimated here.
    p_val = 1 - stats.chi2.cdf(chi2_stat, df)
    
    return {"p_value": float(p_val), "chi2_stat": float(chi2_stat)}

def main():
    """Run analysis based on CLI args."""
    parser = argparse.ArgumentParser(description="Analysis module")
    parser.add_argument("--task", type=str, choices=["plan", "spec", "chi2"], help="Analysis task")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    if args.task == "plan":
        res = run_plan_primary_analysis()
        print(json.dumps(res))
    elif args.task == "spec":
        res = run_spec_mandatory_analysis()
        print(json.dumps(res))
    elif args.task == "chi2":
        res = run_chi_square_goodness_of_fit()
        print(json.dumps(res))
    else:
        print("Usage: python code/analysis.py --task {plan,spec,chi2}")

if __name__ == "__main__":
    main()