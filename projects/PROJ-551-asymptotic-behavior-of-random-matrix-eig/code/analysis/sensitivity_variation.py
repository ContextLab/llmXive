"""
Task T029a: Compute variation in critical threshold theta_c across density sweep.

Reads the sensitivity density sweep results produced by T028:
`data/processed/sensitivity_density_sweep.csv`

For each sparsity density, it calculates the fitted critical threshold theta_c
(by aggregating results across seeds and fitting a logistic curve or identifying
the transition point). It then computes the standard deviation of these theta_c
values across the density sweep to quantify the stability of the threshold.

Output: `data/processed/sensitivity_variation.csv`
Schema: {"density": float, "theta_c": float, "std_dev": float}
"""

import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy.optimize import curve_fit

# Project relative imports
# Ensure the code directory is in the path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import get_project_paths

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def sigmoid_function(x, a, b, c):
    """
    Logistic function for fitting the transition probability.
    P(outlier) = 1 / (1 + exp(-a * (x - c)))
    Where c is the critical threshold theta_c.
    a controls the steepness.
    """
    return 1.0 / (1.0 + np.exp(-a * (x - c)))

def load_sensitivity_results(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load the sensitivity density sweep results CSV.
    Expected columns: density, theta, outlier_count, total_count, ...
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    results = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'density': float(row['density']),
                'theta': float(row['theta']),
                'outlier_count': int(row['outlier_count']),
                'total_count': int(row['total_count']),
                'sparsity_type': row.get('sparsity_type', 'diagonal') # Default if missing
            })
    return results

def aggregate_by_density(results: List[Dict[str, Any]]) -> Dict[float, Dict[str, List]]:
    """
    Group results by density and theta.
    Returns: { density: { theta: {'outliers': [...], 'total': [...]} } }
    """
    aggregated = {}
    for res in results:
        d = res['density']
        t = res['theta']
        if d not in aggregated:
            aggregated[d] = {}
        if t not in aggregated[d]:
            aggregated[d][t] = {'outliers': [], 'total': []}
        aggregated[d][t]['outliers'].append(res['outlier_count'])
        aggregated[d][t]['total'].append(res['total_count'])
    return aggregated

def fit_theta_c_for_density(density_data: Dict[float, List], density: float) -> Tuple[Optional[float], Optional[float]]:
    """
    Fit the logistic curve for a specific density to find theta_c.
    Returns (theta_c, std_dev_estimate) or (None, None) if fit fails.
    """
    thetas = sorted(density_data.keys())
    if len(thetas) < 3:
        logger.warning(f"Not enough theta points for density {density} to fit curve.")
        return None, None

    # Aggregate counts
    probs = []
    x_vals = []
    for t in thetas:
        total = sum(density_data[t]['total'])
        outliers = sum(density_data[t]['outliers'])
        if total > 0:
            probs.append(outliers / total)
            x_vals.append(t)
        else:
            # Skip if no data
            pass

    if len(x_vals) < 3:
        logger.warning(f"Not enough valid data points for density {density}.")
        return None, None

    x_vals = np.array(x_vals)
    y_vals = np.array(probs)

    # Clamp y_vals to avoid log(0) in some fits, though sigmoid handles 0/1
    # Ensure y is strictly between 0 and 1 for robust fitting if using logit,
    # but sigmoid least squares is okay with 0/1 if initialized well.
    # Add small epsilon to avoid exact 0/1 if curve_fit struggles
    epsilon = 1e-6
    y_vals = np.clip(y_vals, epsilon, 1 - epsilon)

    # Initial guess: a=10 (steep), c=2.0 (expected threshold)
    try:
        popt, pcov = curve_fit(
            sigmoid_function,
            x_vals,
            y_vals,
            p0=[10.0, 0.0, 2.0],
            bounds=([0, -np.inf, 0], [np.inf, np.inf, 4.0]),
            maxfev=5000
        )
        # c is the third parameter (index 2)
        theta_c = popt[2]
        # Estimate std dev from covariance matrix (diagonal element for c)
        if pcov is not None:
            std_dev = np.sqrt(pcov[2, 2])
        else:
            std_dev = 0.0
        return theta_c, std_dev
    except RuntimeError as e:
        logger.warning(f"Curve fit failed for density {density}: {e}")
        return None, None

def compute_sensitivity_variation(input_path: Path, output_path: Path) -> List[Dict[str, float]]:
    """
    Main logic to compute variation.
    1. Load data.
    2. Aggregate by density.
    3. Fit theta_c for each density.
    4. Compute standard deviation of theta_c values across densities.
    """
    logger.info(f"Loading sensitivity results from {input_path}")
    results = load_sensitivity_results(input_path)

    logger.info("Aggregating by density...")
    aggregated = aggregate_by_density(results)

    density_results = []
    theta_c_values = []

    for density in sorted(aggregated.keys()):
        logger.info(f"Processing density {density}...")
        theta_c, std_err = fit_theta_c_for_density(aggregated[density], density)

        if theta_c is not None:
            density_results.append({
                'density': density,
                'theta_c': theta_c,
                'std_err': std_err if std_err else 0.0
            })
            theta_c_values.append(theta_c)
        else:
            logger.warning(f"Skipping density {density} due to fit failure.")

    if not theta_c_values:
        raise RuntimeError("No valid theta_c values computed for any density.")

    # Calculate the global standard deviation of the theta_c values
    global_std_dev = float(np.std(theta_c_values))
    logger.info(f"Global standard deviation of theta_c across densities: {global_std_dev:.6f}")

    # Prepare output rows.
    # The task asks for: {"density": float, "theta_c": float, "std_dev": float}
    # Interpretation: For each density, report its theta_c.
    # The 'std_dev' column likely refers to the uncertainty of that specific fit,
    # OR the global std_dev of the set.
    # Given the schema "Calculate the standard deviation of the critical threshold theta_c values across the density sweep",
    # and the output file name "sensitivity_variation.csv", it implies a summary or a per-row metric.
    # If it's per-row, the 'std_dev' might be the fit error.
    # However, the task says "Calculate the standard deviation ... across the density sweep" as the metric.
    # This suggests the final output might be a single row summary, OR each row includes the global variation.
    # Let's include the global std_dev in every row to show the variation context,
    # and also the per-fit std_err if available.
    # Re-reading: "Output `data/processed/sensitivity_variation.csv` with schema: {"density": float, "theta_c": float, "std_dev": float}"
    # This looks like a row per density. The 'std_dev' column is ambiguous.
    # Option A: std_dev of the fit (uncertainty).
    # Option B: The global std_dev of all theta_c's (the variation metric).
    # Given the task is "Compute variation ... across the density sweep", the global std_dev is the primary result.
    # But the schema implies a table.
    # Let's output the global std_dev in the 'std_dev' column for every row,
    # as that represents the "variation across the sweep" for that point's context.
    # Alternatively, if the task implies a single summary row, the schema would be different.
    # Let's assume the user wants to see the variation metric repeated or the per-fit error.
    # Let's use the global_std_dev as the 'std_dev' column to highlight the sweep variation.

    output_rows = []
    for row in density_results:
        output_rows.append({
            'density': row['density'],
            'theta_c': row['theta_c'],
            'std_dev': global_std_dev
        })

    # Write output
    logger.info(f"Writing results to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['density', 'theta_c', 'std_dev']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    return output_rows

def write_variation_csv(results: List[Dict[str, float]], output_path: Path):
    """
    Helper to write the CSV if needed separately, though compute_sensitivity_variation does it.
    """
    pass

def main():
    args = argparse.ArgumentParser(description="Task T029a: Compute sensitivity variation of theta_c")
    args.add_argument('--input', type=str, default='data/processed/sensitivity_density_sweep.csv',
                      help='Path to sensitivity density sweep results CSV')
    args.add_argument('--output', type=str, default='data/processed/sensitivity_variation.csv',
                      help='Path to output variation CSV')
    args = args.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        compute_sensitivity_variation(input_path, output_path)
        logger.info("Task T029a completed successfully.")
    except Exception as e:
        logger.error(f"Task T029a failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()