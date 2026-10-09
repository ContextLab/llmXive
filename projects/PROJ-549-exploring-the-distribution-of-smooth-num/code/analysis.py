"""
code/analysis.py: Statistical analysis, regression, and goodness-of-fit tests.
Implements Plan-Primary (Deviation Ratio, KS) and Spec-Mandatory (Raw Density, Chi-Square) analyses.
"""
import argparse
import json
import logging
import os
import sys
from typing import Dict, List, Optional, Any
import numpy as np
from scipy import stats
from scipy.optimize import curve_fit
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
        required = ['x', 'y', 'h', 'density']
        if not all(col in header for col in required):
            raise ValueError(f"CSV missing required columns. Found: {header}")

        for line in f:
            parts = line.strip().split(',')
            if len(parts) != len(header):
                continue
            row = dict(zip(header, parts))
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
    Fits R = c * h^beta (Deviation Ratio) using linear regression on log‑log scale.
    Returns a dict with beta, standard error, R² and the fitted coefficient c.
    """
    h_vals = np.array([d['h'] for d in data])
    r_vals = np.array([d['deviation_ratio'] for d in data])

    mask = (r_vals > 0) & np.isfinite(h_vals) & np.isfinite(r_vals)
    h_clean = h_vals[mask]
    r_clean = r_vals[mask]

    if len(h_clean) < 3:
        logging.warning("Insufficient data points for deviation ratio regression.")
        return None

    log_h = np.log(h_clean)
    log_r = np.log(r_clean)

    try:
        slope, intercept, r_value, _, std_err = stats.linregress(log_h, log_r)
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
    Fits rho = c * h^beta (Raw Density) using linear regression on log‑log scale.
    Returns a dict with beta, standard error, R² and the fitted coefficient c.
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
        slope, intercept, r_value, _, std_err = stats.linregress(log_h, log_rho)
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

# --- Core Analysis Functions ---

def run_plan_primary_analysis(
    density_path: Optional[str] = None
) -> Optional[Dict[str, float]]:
    """
    Executes Plan‑Primary analysis:
    1. Fits R ∝ h^beta (Deviation Ratio) on the Plan grid.
    2. Performs a two‑sample Kolmogorov‑Smirnov test comparing observed densities
       against the Dickman‑predicted densities.
    Returns a dictionary containing regression results and the KS p‑value.
    """
    filepath = density_path or "data/density_measurements_plan.csv"
    if not os.path.exists(filepath):
        logging.error(f"Plan data file not found: {filepath}")
        return None

    data = load_density_data(filepath)
    if not data:
        return None

    # Regression on deviation ratio
    regression_results = fit_power_law_deviation(data)

    # KS test: compare observed densities to Dickman expectations
    observed = []
    expected = []
    for d in data:
        u = math.log(d['x']) / math.log(d['y']) if d['y'] > 1 else 0.0
        expected.append(rho(u))
        observed.append(d['density'])

    ks_stat, ks_p = stats.ks_2samp(observed, expected)

    if regression_results is None:
        regression_results = {}
    regression_results["ks_p_value"] = float(ks_p)
    return regression_results

def run_spec_mandatory_analysis(
    density_path: Optional[str] = None
) -> Optional[Dict[str, float]]:
    """
    Executes Spec‑Mandatory analysis:
    Fits raw density ρ ∝ h^beta on the Spec grid.
    """
    filepath = density_path or "data/density_measurements_spec.csv"
    if not os.path.exists(filepath):
        logging.error(f"Spec data file not found: {filepath}")
        return None

    data = load_density_data(filepath)
    if not data:
        return None

    return fit_power_law_raw_density(data)

def run_chi_square_goodness_of_fit(
    density_path: Optional[str] = None
) -> Optional[Dict[str, float]]:
    """
    Executes the Spec‑Mandatory Chi‑Square Goodness‑of‑Fit test.
    Implements Sturges' rule for binning and merges bins with expected count < 5.
    """
    filepath = density_path or "data/density_measurements_spec.csv"
    if not os.path.exists(filepath):
        logging.error(f"Spec data file not found: {filepath}")
        return None

    data = load_density_data(filepath)
    if not data:
        return None

    observed_densities = np.array([d['density'] for d in data if np.isfinite(d['density'])])
    if len(observed_densities) < 2:
        logging.warning("Not enough data for Chi‑Square test.")
        return None

    # Sturges' rule
    n = len(observed_densities)
    k = int(np.ceil(1 + np.log2(n)))
    k = max(k, 2)

    # Bin edges
    bins = np.linspace(0, observed_densities.max() * 1.1, k + 1)

    observed_counts, _ = np.histogram(observed_densities, bins=bins)

    # Expected counts per bin based on Dickman predictions
    expected_counts = np.zeros(k)
    for d in data:
        if not np.isfinite(d['density']):
            continue
        u = math.log(d['x']) / math.log(d['y']) if d['y'] > 1 else 0.0
        theo_rho = rho(u)
        idx = np.digitize(d['density'], bins) - 1
        if 0 <= idx < k:
            expected_counts[idx] += theo_rho

    # Scale expected to total observed count
    total_obs = observed_counts.sum()
    if expected_counts.sum() > 0:
        expected_counts = expected_counts * (total_obs / expected_counts.sum())

    # Merge bins with expected < 5
    merged_obs = []
    merged_exp = []
    cur_obs = 0.0
    cur_exp = 0.0
    for obs, exp in zip(observed_counts, expected_counts):
        if exp < 5:
            cur_obs += obs
            cur_exp += exp
        else:
            if cur_exp > 0:
                merged_obs.append(cur_obs)
                merged_exp.append(cur_exp)
                cur_obs = 0.0
                cur_exp = 0.0
            merged_obs.append(obs)
            merged_exp.append(exp)
    if cur_exp > 0:
        merged_obs.append(cur_obs)
        merged_exp.append(cur_exp)

    merged_obs = np.array(merged_obs)
    merged_exp = np.array(merged_exp)

    if merged_exp.sum() == 0:
        logging.warning("All expected counts are zero after merging.")
        return None

    chi2_stat = np.sum((merged_obs - merged_exp) ** 2 / merged_exp)
    df = len(merged_obs) - 1
    p_val = 1 - stats.chi2.cdf(chi2_stat, df)

    return {"p_value": float(p_val), "chi2_stat": float(chi2_stat)}

# --- CLI Interface ---

def main():
    """
    Command‑line interface.
    Supports three tasks:
    * plan  – deviation‑ratio regression + KS test
    * spec  – raw‑density regression
    * chi2  – chi‑square goodness‑of‑fit test
    Optional arguments allow overriding input and output file locations.
    """
    parser = argparse.ArgumentParser(description="Statistical analysis for smooth‑number study")
    parser.add_argument(
        "--task",
        type=str,
        choices=["plan", "spec", "chi2"],
        required=True,
        help="Analysis task to perform"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to density CSV file (overrides default for the selected task)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to write JSON result (if omitted, result is printed only)"
    )
    parser.add_argument(
        "--plot-dir",
        type=str,
        default=None,
        help="Directory for plots (currently unused by this script)"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    if args.task == "plan":
        result = run_plan_primary_analysis(density_path=args.input)
    elif args.task == "spec":
        result = run_spec_mandatory_analysis(density_path=args.input)
    elif args.task == "chi2":
        result = run_chi_square_goodness_of_fit(density_path=args.input)
    else:
        parser.error("Invalid task selected")

    if result is None:
        logging.error("Analysis failed; no results to output.")
        sys.exit(1)

    if args.output:
        try:
            os.makedirs(os.path.dirname(args.output), exist_ok=True)
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
            logging.info(f"Results written to {args.output}")
        except Exception as e:
            logging.error(f"Failed to write results: {e}")
            sys.exit(1)
    else:
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
