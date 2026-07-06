import os
import sys
import argparse
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from simulation.engine import calculate_vif
from models.bayesian import fit_bayesian_and_get_intervals
from models.ols import fit_ols_and_get_intervals
from models.bootstrap import fit_bootstrap_and_get_intervals

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fetch_uci_concrete_dataset(output_path: str) -> pd.DataFrame:
    """
    Fetches the UCI Concrete Compressive Strength dataset.
    Tries the official CSV URL first, then falls back to a known mirror.
    """
    # Primary URL from UCI Machine Learning Repository
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00240/UCI%20Concrete%20Compressive%20Strength%20Dataset.csv"
    
    try:
        logger.info(f"Attempting to fetch dataset from: {url}")
        df = pd.read_csv(url)
        logger.info(f"Successfully loaded dataset with shape: {df.shape}")
        return df
    except Exception as e:
        logger.warning(f"Primary URL failed: {e}. Trying fallback...")
        # Fallback: known working direct link to the CSV content
        fallback_url = "https://raw.githubusercontent.com/UCI-ML/Concrete-Compressive-Strength/master/Concrete_Data.csv"
        try:
            df = pd.read_csv(fallback_url)
            logger.info(f"Successfully loaded dataset from fallback: {df.shape}")
            return df
        except Exception as e2:
            logger.error(f"Both URLs failed: {e2}")
            raise RuntimeError("Could not fetch UCI Concrete dataset from any known source.")

def subsample_stratified(df: pd.DataFrame, target_n: int, seed: int = 42) -> pd.DataFrame:
    """
    Subsamples the dataframe to target_n using stratified sampling on the target variable.
    Ensures N > p (sample size > number of predictors).
    """
    rng = np.random.default_rng(seed)
    
    # Identify target column (usually 'Concrete compressive strength (MPa)')
    target_col = None
    for col in df.columns:
        if 'strength' in col.lower() or 'compressive' in col.lower():
            target_col = col
            break
    
    if target_col is None:
        # Fallback: assume last column is target if not found by name
        target_col = df.columns[-1]
        logger.warning(f"Target column not found by name, using '{target_col}'")

    predictors = [c for c in df.columns if c != target_col]
    p = len(predictors)

    if target_n <= p:
        raise ValueError(f"Target N ({target_n}) must be greater than number of predictors ({p}).")

    # Create bins for stratification if target is continuous
    # We'll use quantile-based binning to ensure representation
    try:
        df['stratum'] = pd.qcut(df[target_col], q=min(10, target_n), duplicates='drop')
    except ValueError:
        # If too few unique values, just use the values directly or a simpler binning
        df['stratum'] = pd.cut(df[target_col], bins=min(5, target_n), duplicates='drop')

    # Stratified sample
    sample = df.groupby('stratum', group_keys=False).apply(
        lambda x: x.sample(n=min(int((len(x) / len(df)) * target_n), len(x)), replace=False, random_state=rng)
    )
    
    # If we didn't get enough, fill the rest randomly
    while len(sample) < target_n:
        missing = target_n - len(sample)
        pool = df.drop(sample.index)
        if len(pool) == 0:
            break
        extra = pool.sample(n=min(missing, len(pool)), replace=False, random_state=rng)
        sample = pd.concat([sample, extra])
    
    sample = sample.drop(columns=['stratum'])
    logger.info(f"Subsampled to N={len(sample)} with {p} predictors.")
    return sample

def load_best_method_config(config_path: str) -> Dict[str, Any]:
    """Loads the best method configuration."""
    if not os.path.exists(config_path):
        logger.warning(f"Best method config not found at {config_path}. Defaulting to 'bayesian'.")
        return {"method": "bayesian", "params": {}}
    
    with open(config_path, 'r') as f:
        return json.load(f)

def run_validation_on_dataset(
    df: pd.DataFrame, 
    method_name: str, 
    seed: int = 42
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Runs the specified method on the dataset and returns results.
    Returns: (results_dict, diagnostics_dict)
    """
    # Prepare data
    # Identify target column
    target_col = None
    for col in df.columns:
        if 'strength' in col.lower() or 'compressive' in col.lower():
            target_col = col
            break
    if target_col is None:
        target_col = df.columns[-1]
    
    X = df.drop(columns=[target_col]).values
    y = df[target_col].values
    p = X.shape[1]

    # Calculate VIF
    vif_max = calculate_vif(X)
    logger.info(f"VIF Max: {vif_max}")

    results = {
        "method": method_name,
        "N": len(y),
        "p": p,
        "vif_max": vif_max,
        "seed": seed
    }
    
    diagnostics = {
        "converged": True,
        "warnings": []
    }

    try:
        if method_name == "bayesian":
            # Run Bayesian
            model = fit_bayesian_and_get_intervals(X, y, seed=seed)
            results["intervals"] = model["intervals"]
            results["coefficients"] = model["coefficients"]
            if not model.get("converged", True):
                diagnostics["converged"] = False
                diagnostics["warnings"].append("Bayesian model did not converge")
        
        elif method_name == "ols":
            # Run OLS
            model = fit_ols_and_get_intervals(X, y)
            results["intervals"] = model["intervals"]
            results["coefficients"] = model["coefficients"]
        
        elif method_name == "bootstrap":
            # Run Bootstrap
            model = fit_bootstrap_and_get_intervals(X, y, seed=seed)
            results["intervals"] = model["intervals"]
            results["coefficients"] = model["coefficients"]
        
        else:
            raise ValueError(f"Unknown method: {method_name}")

    except Exception as e:
        logger.error(f"Error running {method_name}: {e}")
        diagnostics["warnings"].append(str(e))
        diagnostics["converged"] = False
        raise

    return results, diagnostics

def generate_interval_stability_metrics(
    results: Dict[str, Any], 
    output_path: str
) -> None:
    """Generates metrics on interval stability and saves them."""
    # This is a placeholder for more complex stability metrics
    # For now, we just save the results summary
    metrics = {
        "mean_interval_width": np.mean([r[1] - r[0] for r in results["intervals"]]),
        "interval_count": len(results["intervals"]),
        "method": results["method"]
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved interval stability metrics to {output_path}")

def generate_diagnostic_plots(
    results: Dict[str, Any], 
    diagnostics: Dict[str, Any],
    output_dir: str
) -> None:
    """
    Generates diagnostic plots:
    1. Posterior distributions (for Bayesian) or Coefficient estimates with intervals
    2. Interval widths comparison
    """
    os.makedirs(output_dir, exist_ok=True)
    
    method = results["method"]
    coefficients = results["coefficients"]
    intervals = results["intervals"]
    n_coeffs = len(coefficients)
    coeff_names = [f"β{i}" for i in range(n_coeffs)]

    # Plot 1: Coefficient Estimates with Intervals
    plt.figure(figsize=(10, 6))
    x_pos = np.arange(n_coeffs)
    widths = [intervals[i][1] - intervals[i][0] for i in range(n_coeffs)]
    centers = [intervals[i][0] + widths[i]/2 for i in range(n_coeffs)]
    lower = [intervals[i][0] for i in range(n_coeffs)]
    upper = [intervals[i][1] for i in range(n_coeffs)]

    plt.errorbar(
        x_pos, 
        centers, 
        yerr=[np.array(centers) - np.array(lower), np.array(upper) - np.array(centers)],
        fmt='o', 
        capsize=5, 
        label='95% Interval'
    )
    plt.axhline(0, color='black', linewidth=0.8, linestyle='--')
    plt.xticks(x_pos, coeff_names)
    plt.xlabel('Coefficient')
    plt.ylabel('Value')
    plt.title(f'{method.capitalize()} Coefficient Estimates and Intervals')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'coefficient_intervals.png'))
    plt.close()
    logger.info(f"Saved coefficient intervals plot to {output_dir}/coefficient_intervals.png")

    # Plot 2: Interval Widths
    plt.figure(figsize=(8, 5))
    plt.bar(x_pos, widths)
    plt.xticks(x_pos, coeff_names)
    plt.xlabel('Coefficient')
    plt.ylabel('Interval Width')
    plt.title(f'{method.capitalize()} Interval Widths')
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'interval_widths.png'))
    plt.close()
    logger.info(f"Saved interval widths plot to {output_dir}/interval_widths.png")

    # Plot 3: Posterior Distributions (if Bayesian)
    if method == "bayesian":
        # Assuming results might contain posterior samples or we approximate with normal
        # If we have full posterior samples, we would plot histograms.
        # Since the API returns intervals, we will plot a schematic of the posterior 
        # centered at the coefficient with width based on the interval (assuming normal approx)
        plt.figure(figsize=(10, 6))
        
        # We need to retrieve posterior samples if available. 
        # If the model object in results had 'samples', we would use them.
        # For this implementation, we will generate a synthetic plot based on the interval
        # to visualize the shape, assuming a normal distribution centered at the estimate.
        # In a real scenario, we would pass the StanFit object or samples.
        
        # Let's assume we have access to the model object if it was stored, 
        # but here we only have the summary. We will skip the full posterior plot 
        # unless we modify run_validation_on_dataset to return samples.
        # Instead, we will plot the "Estimated Posterior Density" using the interval width as sigma.
        
        for i in range(n_coeffs):
            mu = centers[i]
            sigma = widths[i] / (2 * 1.96) # Approx sigma from 95% CI
            x = np.linspace(mu - 4*sigma, mu + 4*sigma, 100)
            y = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma)**2)
            plt.plot(x, y, label=f'{coeff_names[i]}')
        
        plt.title('Approximate Posterior Distributions (Normal Approx)')
        plt.xlabel('Coefficient Value')
        plt.ylabel('Density')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'posterior_distributions.png'))
        plt.close()
        logger.info(f"Saved posterior distributions plot to {output_dir}/posterior_distributions.png")

def main():
    parser = argparse.ArgumentParser(description="Run validation on UCI Concrete dataset and generate plots.")
    parser.add_argument('--data', type=str, default='data/raw/uci_concrete.csv', help='Path to UCI dataset')
    parser.add_argument('--output', type=str, default='data/results', help='Output directory for plots and metrics')
    parser.add_argument('--method', type=str, default='bayesian', help='Method to use (bayesian, ols, bootstrap)')
    parser.add_argument('--n', type=int, default=40, help='Target sample size')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()

    # Ensure directories exist
    os.makedirs(args.output, exist_ok=True)
    os.makedirs(os.path.dirname(args.data), exist_ok=True)

    # 1. Fetch and subsample
    logger.info("Fetching UCI Concrete dataset...")
    try:
        full_df = fetch_uci_concrete_dataset(args.data)
    except RuntimeError as e:
        logger.error(f"Failed to fetch data: {e}")
        sys.exit(1)

    logger.info("Subsampling dataset...")
    subsampled_df = subsample_stratified(full_df, target_n=args.n, seed=args.seed)

    # 2. Load best method config (optional, but good practice)
    best_method_config_path = 'data/results/best_method_config.json'
    config = load_best_method_config(best_method_config_path)
    method_to_use = args.method if args.method != 'bayesian' else config.get('method', 'bayesian')
    
    logger.info(f"Running validation with method: {method_to_use}")

    # 3. Run validation
    try:
        results, diagnostics = run_validation_on_dataset(subsampled_df, method_to_use, seed=args.seed)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

    # 4. Generate stability metrics
    metrics_path = os.path.join(args.output, 'validation_metrics.json')
    generate_interval_stability_metrics(results, metrics_path)

    # 5. Generate diagnostic plots
    plots_dir = os.path.join(args.output, 'plots')
    generate_diagnostic_plots(results, diagnostics, plots_dir)

    # Save raw results for reference
    results_path = os.path.join(args.output, 'validation_results.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("Validation complete. Plots and metrics saved.")

if __name__ == "__main__":
    main()