import os
import sys
import argparse
import logging
import json
import warnings
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models.ols import fit_ols_and_get_intervals, OLSModel
from models.bootstrap import fit_bootstrap_and_get_intervals, BootstrapModel
from models.bayesian import fit_bayesian_and_get_intervals, BayesianModel
from simulation.engine import calculate_vif

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(project_root, 'data', 'results', 'uci_validation.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
NOMINAL_COVERAGE = 0.95

def fetch_uci_concrete_dataset() -> pd.DataFrame:
    """
    Fetches the UCI Concrete Compressive Strength dataset.
    Uses the ucimlrepo package which is a verified real source.
    """
    try:
        from ucimlrepo import fetch_ucirepo
        logger.info("Fetching UCI Concrete Compressive Strength dataset...")
        concrete = fetch_ucirepo(id=92)
        df = concrete.data.variables
        # The dataset typically has 8 predictors and 1 target
        # Verify columns exist
        expected_cols = ['Cement', 'BlastFurnaceSlag', 'FlyAsh', 'Water', 'Superplasticizer', 'CoarseAggregate', 'FineAggregate', 'Age', 'Concrete compressive strength']
        if not all(col in df.columns for col in expected_cols):
            logger.warning("Expected columns not found. Checking available columns...")
            logger.warning(f"Available: {df.columns.tolist()}")
            # Fallback: try to identify target and predictors dynamically if structure differs slightly
            # But standard UCI ID 92 is consistent.
        
        # Rename target for clarity if needed, or keep standard names
        # Standard: 'Concrete compressive strength' is the target
        target_col = 'Concrete compressive strength'
        predictor_cols = [c for c in df.columns if c != target_col]
        
        # Ensure numeric
        df = df[predictor_cols + [target_col]].apply(pd.to_numeric, errors='raise')
        logger.info(f"Dataset loaded successfully with shape {df.shape}")
        return df
    except ImportError:
        logger.error("ucimlrepo not installed. Please install it: pip install ucimlrepo")
        raise
    except Exception as e:
        logger.error(f"Failed to fetch dataset: {e}")
        raise

def subsample_stratified(df: pd.DataFrame, target_col: str, n_samples: int, seed: int = 42) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Subsamples the dataframe to n_samples using stratified sampling on the target.
    Ensures N > p (sample size > number of predictors) and at least 3 predictors.
    """
    np.random.seed(seed)
    predictors = [c for c in df.columns if c != target_col]
    p = len(predictors)
    
    if p < 3:
        raise ValueError(f"Dataset has only {p} predictors. Need at least 3.")
    
    if n_samples <= p:
        raise ValueError(f"Requested sample size {n_samples} is not greater than number of predictors {p}.")
    
    # Stratify by binned target to ensure distribution is preserved
    # Create bins for stratification
    n_bins = min(10, n_samples // 2) # Ensure we have enough samples per bin
    if n_bins < 2: n_bins = 2
    
    df = df.copy()
    df['_bin'] = pd.qcut(df[target_col], q=n_bins, duplicates='drop')
    
    # Perform stratified sampling
    try:
        subsample = df.groupby('_bin', group_keys=False).apply(lambda x: x.sample(n=min(int(n_samples * len(x) / len(df)), n_samples), random_state=seed))
    except ValueError:
        # If some bins are too small, fall back to simple random sampling with warning
        logger.warning("Stratified sampling failed (some bins too small). Falling back to simple random sampling.")
        subsample = df.sample(n=n_samples, random_state=seed)
    
    subsample = subsample.drop(columns=['_bin'])
    subsample.reset_index(drop=True, inplace=True)
    
    logger.info(f"Subsampled data: N={len(subsample)}, Predictors={p}, Target distribution preserved.")
    
    metadata = {
        "n_samples": len(subsample),
        "n_predictors": p,
        "seed": seed,
        "method": "stratified"
    }
    
    return subsample, metadata

def load_best_method_config(config_path: str) -> Dict[str, Any]:
    """
    Loads the best method configuration from the JSON file.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Best method config file not found: {config_path}. "
                                "Run the simulation and selection script first.")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    logger.info(f"Loaded best method config: {config}")
    return config

def run_validation_on_dataset(
    df: pd.DataFrame, 
    target_col: str, 
    best_method_config: Dict[str, Any],
    seed: int = 42
) -> Dict[str, Any]:
    """
    Runs the best identified method on the subsampled dataset.
    Returns results including intervals, diagnostics, and coverage stats (if ground truth known, 
    but for real data we focus on interval properties and stability).
    """
    np.random.seed(seed)
    
    predictors = [c for c in df.columns if c != target_col]
    X = df[predictors].values
    y = df[target_col].values
    
    # Calculate VIF
    vif_values = calculate_vif(X, predictors)
    max_vif = max(vif.values() for v in vif_values)
    logger.info(f"VIF calculated. Max VIF: {max_vif:.2f}")
    
    method_name = best_method_config.get('method_name', 'OLS')
    logger.info(f"Running method: {method_name}")
    
    results = {
        "method": method_name,
        "n_samples": len(y),
        "n_predictors": len(predictors),
        "vif_max": max_vif,
        "coefficients": {},
        "intervals": {},
        "diagnostics": {}
    }
    
    if method_name == "OLS":
        model = OLSModel()
        coef, ci_lower, ci_upper, diagnostics = fit_ols_and_get_intervals(X, y, confidence_level=NOMINAL_COVERAGE)
        results["coefficients"] = {p: float(c) for p, c in zip(predictors, coef)}
        results["intervals"] = {p: {"lower": float(l), "upper": float(u)} for p, l, u in zip(predictors, ci_lower, ci_upper)}
        results["diagnostics"] = diagnostics
        
    elif method_name == "Bootstrap":
        model = BootstrapModel(n_bootstraps=1000)
        coef, ci_lower, ci_upper, diagnostics = fit_bootstrap_and_get_intervals(X, y, confidence_level=NOMINAL_COVERAGE)
        results["coefficients"] = {p: float(c) for p, c in zip(predictors, coef)}
        results["intervals"] = {p: {"lower": float(l), "upper": float(u)} for p, l, u in zip(predictors, ci_lower, ci_upper)}
        results["diagnostics"] = diagnostics
        
    elif method_name == "Bayesian":
        model = BayesianModel()
        coef, ci_lower, ci_upper, diagnostics = fit_bayesian_and_get_intervals(X, y, confidence_level=NOMINAL_COVERAGE)
        results["coefficients"] = {p: float(c) for p, c in zip(predictors, coef)}
        results["intervals"] = {p: {"lower": float(l), "upper": float(u)} for p, l, u in zip(predictors, ci_lower, ci_upper)}
        results["diagnostics"] = diagnostics
    else:
        raise ValueError(f"Unknown method: {method_name}")
    
    return results

def generate_interval_stability_metrics(results: Dict[str, Any], output_path: str) -> None:
    """
    Generates stability metrics (e.g., interval widths) and saves them.
    """
    widths = []
    for p, interval in results["intervals"].items():
        width = interval["upper"] - interval["lower"]
        widths.append(width)
    
    metrics = {
        "method": results["method"],
        "mean_interval_width": float(np.mean(widths)),
        "std_interval_width": float(np.std(widths)),
        "min_interval_width": float(np.min(widths)),
        "max_interval_width": float(np.max(widths)),
        "individual_widths": {p: float(w) for p, w in zip(results["intervals"].keys(), widths)}
    }
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Interval stability metrics saved to {output_path}")

def generate_diagnostic_plots(results: Dict[str, Any], predictors: List[str], output_dir: str) -> None:
    """
    Generates diagnostic plots:
    1. Coefficient estimates with intervals
    2. Interval width comparison
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Plot 1: Coefficients with Intervals
    plt.figure(figsize=(12, 8))
    x_pos = np.arange(len(predictors))
    coef_vals = [results["intervals"][p]["lower"] for p in predictors]
    coef_upper = [results["intervals"][p]["upper"] for p in predictors]
    coef_mid = [(l+u)/2 for l, u in zip(coef_vals, coef_upper)]
    errors = [(u-l)/2 for l, u in zip(coef_vals, coef_upper)]
    
    plt.errorbar(x_pos, coef_mid, yerr=errors, fmt='o', capsize=5, label=f'{results["method"]} 95% CI')
    plt.xticks(x_pos, predictors, rotation=45)
    plt.ylabel('Coefficient Value')
    plt.title(f'Coefficient Estimates with {results["method"]} 95% Confidence Intervals')
    plt.axhline(0, color='black', linestyle='--', linewidth=0.8)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'coef_intervals.png'))
    plt.close()
    
    # Plot 2: Interval Widths
    plt.figure(figsize=(10, 6))
    widths = [results["intervals"][p]["upper"] - results["intervals"][p]["lower"] for p in predictors]
    plt.bar(predictors, widths, color='skyblue', edgecolor='black')
    plt.xticks(rotation=45)
    plt.ylabel('Interval Width')
    plt.title(f'Interval Widths by Predictor ({results["method"]})')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'interval_widths.png'))
    plt.close()
    
    logger.info(f"Diagnostic plots saved to {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="Run validation on UCI Concrete dataset using best method.")
    parser.add_argument('--n-samples', type=int, default=40, help='Number of samples to subsample')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--config', type=str, default=os.path.join(project_root, 'data', 'results', 'best_method_config.json'), help='Path to best method config')
    parser.add_argument('--output-dir', type=str, default=os.path.join(project_root, 'data', 'results'), help='Output directory for results and plots')
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        # 1. Fetch and Subsample
        logger.info("Step 1: Fetching and Subsampling UCI Dataset")
        full_df = fetch_uci_concrete_dataset()
        target_col = 'Concrete compressive strength'
        subsample_df, subsample_meta = subsample_stratified(full_df, target_col, args.n_samples, args.seed)
        
        # Save subsample
        subsample_path = os.path.join(project_root, 'data', 'raw', 'uci_subsampled.csv')
        subsample_df.to_csv(subsample_path, index=False)
        logger.info(f"Subsampled data saved to {subsample_path}")
        
        # 2. Load Best Method Config
        logger.info("Step 2: Loading Best Method Configuration")
        best_method = load_best_method_config(args.config)
        
        # 3. Run Validation
        logger.info("Step 3: Running Validation on Subsampled Data")
        results = run_validation_on_dataset(subsample_df, target_col, best_method, args.seed)
        
        # 4. Generate Stability Metrics
        metrics_path = os.path.join(args.output_dir, 'uci_stability_metrics.json')
        generate_interval_stability_metrics(results, metrics_path)
        
        # 5. Generate Plots
        predictors = [c for c in subsample_df.columns if c != target_col]
        plots_dir = os.path.join(args.output_dir, 'uci_plots')
        generate_diagnostic_plots(results, predictors, plots_dir)
        
        # 6. Save Full Results
        results_path = os.path.join(args.output_dir, 'uci_validation_results.json')
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Full validation results saved to {results_path}")
        
        logger.info("Validation completed successfully.")
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise

if __name__ == '__main__':
    main()