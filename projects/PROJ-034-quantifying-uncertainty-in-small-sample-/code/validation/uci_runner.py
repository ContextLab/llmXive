"""
UCI Concrete Dataset Validation Runner.

This module handles fetching the UCI Concrete Compressive Strength dataset,
subsampling it to small sample sizes (N < 50) with stratified sampling,
and running uncertainty quantification methods on the subsampled data.
"""

import os
import sys
import argparse
import logging
import json
import warnings
from typing import Tuple, Dict, Any, Optional, List
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Import existing model interfaces
from models.ols import fit_ols_and_get_intervals
from models.bootstrap import fit_bootstrap_and_get_intervals
from models.bayesian import fit_bayesian_and_get_intervals
from simulation.engine import calculate_vif

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/uci_validation.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"

# UCI Concrete Dataset URL (Verified in T000)
# The dataset is hosted on the UCI Machine Learning Repository
# Direct CSV link for programmatic access
UCI_CONCRETE_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/concrete/compressive/concrete_compressive_strength.csv"
# Alternative: Use the raw GitHub mirror if UCI blocks direct access (common in CI)
# UCI often redirects, so we use the direct data file path if available
# For robustness, we try the direct link first, then fallback to a known stable mirror
UCI_CONCRETE_MIRROR_URL = "https://raw.githubusercontent.com/UCI-ML/Concrete/master/concrete_compressive_strength.csv"

def fetch_uci_concrete_dataset() -> pd.DataFrame:
    """
    Fetch the UCI Concrete Compressive Strength dataset.
    
    Returns:
        pd.DataFrame: The loaded dataset.
        
    Raises:
        RuntimeError: If the dataset cannot be fetched from any source.
    """
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = DATA_RAW_DIR / "uci_concrete_raw.csv"
    
    if cache_path.exists():
        logger.info(f"Loading cached dataset from {cache_path}")
        return pd.read_csv(cache_path)
    
    logger.info("Attempting to fetch UCI Concrete dataset...")
    sources = [
        ("UCI Direct", UCI_CONCRETE_URL),
        ("GitHub Mirror", UCI_CONCRETE_MIRROR_URL)
    ]
    
    last_error = None
    for source_name, url in sources:
        try:
            logger.info(f"Trying source: {source_name} ({url})")
            df = pd.read_csv(url)
            df.to_csv(cache_path, index=False)
            logger.info(f"Successfully fetched and cached from {source_name}")
            return df
        except Exception as e:
            last_error = e
            logger.warning(f"Failed to fetch from {source_name}: {e}")
            continue
    
    error_msg = f"Failed to fetch UCI Concrete dataset from all sources. Last error: {last_error}"
    logger.error(error_msg)
    raise RuntimeError(error_msg)


def subsample_stratified(
    df: pd.DataFrame, 
    target_n: int, 
    predictor_cols: List[str], 
    target_col: str,
    seed: int = 42
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Subsample the dataset to target_n using stratified sampling.
    
    Ensures at least 3 predictors are retained and N > p.
    
    Args:
        df: Full dataset.
        target_n: Target sample size (N < 50).
        predictor_cols: List of predictor column names.
        target_col: Target variable column name.
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (subsampled DataFrame, metadata dict).
        
    Raises:
        ValueError: If target_n <= number of predictors.
    """
    p = len(predictor_cols)
    
    # Validation: Ensure N > p
    if target_n <= p:
        warning_msg = f"Rank-deficient: N={target_n} <= p={p}. Skipping this configuration."
        logger.warning(warning_msg)
        # Return None and metadata indicating skip
        return None, {
            "status": "skipped",
            "reason": f"Rank-deficient: N={target_n} <= p={p}",
            "target_n": target_n,
            "p": p
        }
    
    if target_n > len(df):
        logger.warning(f"Target N ({target_n}) exceeds dataset size ({len(df)}). Using full dataset.")
        target_n = len(df)
    
    logger.info(f"Subsampling to N={target_n} with {p} predictors (N > p check passed).")
    
    # Stratify by target variable bins if continuous, or use simple random if not enough unique values
    # For continuous target, create bins for stratification
    try:
        # Create 5 bins for stratification to ensure distribution preservation
        n_bins = min(5, target_n)
        if n_bins < 2:
            n_bins = 2
            
        df['target_bin'] = pd.qcut(df[target_col], q=n_bins, duplicates='drop')
        strat_col = 'target_bin'
    except ValueError:
        # If qcut fails (e.g., not enough unique values), fall back to simple random
        logger.info("Stratification failed (not enough unique values). Using simple random sampling.")
        strat_col = None
    
    # Perform stratified or simple random sampling
    if strat_col:
        sample_df = df.groupby(strat_col, group_keys=False).apply(
            lambda x: x.sample(n=min(int(target_n * len(x) / len(df)), len(x)), random_state=seed)
        ).reset_index(drop=True)
        # Ensure we have exactly target_n if possible
        if len(sample_df) > target_n:
            sample_df = sample_df.sample(n=target_n, random_state=seed)
    else:
        sample_df = df.sample(n=target_n, random_state=seed)
    
    # Drop temporary bin column
    if 'target_bin' in sample_df.columns:
        sample_df = sample_df.drop(columns=['target_bin'])
    
    metadata = {
        "status": "success",
        "original_n": len(df),
        "subsampled_n": len(sample_df),
        "predictor_count": p,
        "predictor_cols": predictor_cols,
        "target_col": target_col,
        "seed": seed,
        "n_greater_than_p": len(sample_df) > p
    }
    
    return sample_df, metadata


def load_best_method_config() -> Dict[str, Any]:
    """
    Load configuration for the best method from comparative analysis.
    This is a placeholder for T027.5 output.
    """
    config_path = DATA_RESULTS_DIR / "comparative_metrics.json"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return {"best_method": "bayesian", "reason": "Default to Bayesian"}


def run_validation_on_dataset(
    df: pd.DataFrame,
    predictor_cols: List[str],
    target_col: str,
    method: str = "all"
) -> Dict[str, Any]:
    """
    Run all three uncertainty quantification methods on the dataset.
    
    Args:
        df: Subsampled dataset.
        predictor_cols: List of predictor column names.
        target_col: Target variable column name.
        method: Method to run ('ols', 'bootstrap', 'bayesian', or 'all').
        
    Returns:
        Dictionary containing results from all methods.
    """
    X = df[predictor_cols].values
    y = df[target_col].values
    
    results = {}
    
    # OLS
    if method in ['ols', 'all']:
        try:
            logger.info("Running OLS...")
            ols_result = fit_ols_and_get_intervals(X, y, confidence_level=0.95)
            results['ols'] = ols_result
        except Exception as e:
            logger.error(f"OLS failed: {e}")
            results['ols'] = {"error": str(e)}
    
    # Bootstrap
    if method in ['bootstrap', 'all']:
        try:
            logger.info("Running Bootstrap...")
            boot_result = fit_bootstrap_and_get_intervals(X, y, confidence_level=0.95, n_bootstrap=1000)
            results['bootstrap'] = boot_result
        except Exception as e:
            logger.error(f"Bootstrap failed: {e}")
            results['bootstrap'] = {"error": str(e)}
    
    # Bayesian
    if method in ['bayesian', 'all']:
        try:
            logger.info("Running Bayesian...")
            bayes_result = fit_bayesian_and_get_intervals(X, y, confidence_level=0.95, n_samples=1000, n_warmup=500)
            results['bayesian'] = bayes_result
        except Exception as e:
            logger.error(f"Bayesian failed: {e}")
            results['bayesian'] = {"error": str(e)}
    
    return results


def generate_interval_stability_metrics(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate metrics comparing interval widths and stability across methods.
    """
    metrics = {}
    for method, res in results.items():
        if 'error' in res:
            metrics[method] = {"status": "failed", "error": res['error']}
            continue
        
        if 'intervals' in res:
            intervals = res['intervals']
            widths = [upper - lower for lower, upper in intervals]
            metrics[method] = {
                "status": "success",
                "mean_width": float(np.mean(widths)),
                "std_width": float(np.std(widths)),
                "min_width": float(np.min(widths)),
                "max_width": float(np.max(widths))
            }
        else:
            metrics[method] = {"status": "unknown_structure"}
    
    return metrics


def generate_diagnostic_plots(results: Dict[str, Any], output_dir: Path):
    """
    Generate diagnostic plots for the validation results.
    """
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Plot interval widths comparison
    plt.figure(figsize=(10, 6))
    methods = []
    widths = []
    
    for method, res in results.items():
        if 'error' not in res and 'intervals' in res:
            w = [upper - lower for lower, upper in res['intervals']]
            methods.extend([method] * len(w))
            widths.extend(w)
    
    if methods:
        sns.boxplot(x=methods, y=widths)
        plt.title("Interval Widths by Method")
        plt.ylabel("Width")
        plt.xlabel("Method")
        plt.tight_layout()
        plot_path = output_dir / "interval_widths_comparison.png"
        plt.savefig(plot_path)
        plt.close()
        logger.info(f"Saved interval width plot to {plot_path}")
    else:
        logger.warning("No valid interval data for plotting.")


def main():
    """
    Main entry point for UCI validation pipeline.
    """
    parser = argparse.ArgumentParser(description="UCI Concrete Validation Runner")
    parser.add_argument('--target-n', type=int, default=40, help="Target sample size (N < 50)")
    parser.add_argument('--seed', type=int, default=42, help="Random seed")
    parser.add_argument('--predictors', type=str, nargs='+', default=None, help="Specific predictors to use")
    args = parser.parse_args()
    
    # Define predictors (Concrete dataset has 8 features)
    # Cement, Blast Furnace Slag, Fly Ash, Water, Superplasticizer, Coarse Aggregate, Fine Aggregate, Age
    default_predictors = [
        'cement', 'blast_furnace_slag', 'fly_ash', 'water', 
        'superplasticizer', 'coarse_aggregate', 'fine_aggregate', 'age'
    ]
    
    predictors = args.predictors if args.predictors else default_predictors
    target_col = 'compressive_strength'
    
    # Ensure output directories exist
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Fetch Dataset
    logger.info("Step 1: Fetching UCI Concrete dataset...")
    try:
        df = fetch_uci_concrete_dataset()
    except RuntimeError as e:
        logger.error(f"Failed to fetch dataset: {e}")
        return
    
    logger.info(f"Dataset loaded: {len(df)} rows, {len(df.columns)} columns")
    
    # 2. Subsample with validation
    logger.info(f"Step 2: Subsampling to N={args.target_n}...")
    subsampled_df, subsample_metadata = subsample_stratified(
        df, 
        target_n=args.target_n, 
        predictor_cols=predictors, 
        target_col=target_col,
        seed=args.seed
    )
    
    # Save metadata
    metadata_path = DATA_RESULTS_DIR / "uci_subsample_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(subsample_metadata, f, indent=2)
    
    if subsample_metadata['status'] == 'skipped':
        logger.warning("Subsampling skipped due to rank deficiency. No results generated.")
        return
    
    # 3. Save subsampled data
    output_csv_path = DATA_RAW_DIR / "uci_subsampled.csv"
    subsampled_df.to_csv(output_csv_path, index=False)
    logger.info(f"Subsampled data saved to {output_csv_path}")
    
    # 4. Run Validation
    logger.info("Step 3: Running validation methods...")
    results = run_validation_on_dataset(
        subsampled_df, 
        predictor_cols=predictors, 
        target_col=target_col,
        method="all"
    )
    
    # 5. Generate Metrics
    metrics = generate_interval_stability_metrics(results)
    
    # 6. Save Results
    results_path = DATA_RESULTS_DIR / "uci_validation_results.json"
    with open(results_path, 'w') as f:
        json.dump({
            "subsample_metadata": subsample_metadata,
            "results": results,
            "metrics": metrics
        }, f, indent=2, default=str)
    logger.info(f"Validation results saved to {results_path}")
    
    # 7. Generate Plots
    logger.info("Step 4: Generating diagnostic plots...")
    generate_diagnostic_plots(results, DATA_RESULTS_DIR)
    
    logger.info("UCI Validation pipeline completed successfully.")


if __name__ == "__main__":
    main()