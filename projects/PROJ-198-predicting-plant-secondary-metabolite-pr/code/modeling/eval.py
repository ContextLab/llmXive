import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.metrics import r2_score, mean_squared_error

from modeling.train import train_models_loo, load_pca_features
from modeling.phylo import load_phylogeny, construct_covariance_matrix
from data.align import align_data
from utils.logging import get_logger

logger = get_logger(__name__)

def load_model_results(results_path: Optional[str] = None) -> Dict[str, Any]:
    """Load model results from a JSON file."""
    if results_path is None:
        results_path = "data/processed/model_results.json"
    path = Path(results_path)
    if not path.exists():
        raise FileNotFoundError(f"Model results file not found: {results_path}")
    with open(path, 'r') as f:
        return json.load(f)

def save_metrics(metrics: Dict[str, Any], output_path: Optional[str] = None) -> None:
    """Save metrics to a JSON file."""
    if output_path is None:
        output_path = "data/processed/metrics.json"
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {output_path}")

def evaluate_models(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_name: str = "Model"
) -> Dict[str, float]:
    """Calculate R² and Pearson correlation on hold-out sets."""
    r2 = r2_score(y_true, y_pred)
    if len(np.unique(y_true)) > 1:
        pearson_corr, _ = pearsonr(y_true, y_pred)
    else:
        pearson_corr = 0.0
    mse = mean_squared_error(y_true, y_pred)
    logger.info(f"Evaluation for {model_name}: R²={r2:.4f}, Pearson={pearson_corr:.4f}, MSE={mse:.4f}")
    return {
        "r2": r2,
        "pearson_correlation": pearson_corr,
        "mse": mse
    }

def run_phylogenetic_permutation(
    y: np.ndarray,
    X: np.ndarray,
    tree_path: str,
    n_permutations: int = 100,
    random_state: Optional[int] = None
) -> Dict[str, float]:
    """
    Shuffle labels while preserving tree structure to calculate baseline R².

    This function implements a phylogenetic permutation test (PGLS baseline).
    It shuffles the response variable (y) across the tips of the phylogenetic tree
    in a way that respects the tree's structure (e.g., by permuting independent contrasts
    or using a Brownian motion model simulation) to generate a null distribution.

    For this implementation, we use a simplified approach:
    1. Load the phylogeny.
    2. Calculate the phylogenetic covariance matrix (V).
    3. Perform a Cholesky decomposition of V to decorrelate the data.
    4. Shuffle the decorrelated residuals/labels.
    5. Transform back and calculate R².
    6. Repeat n_permutations times to get a baseline distribution.

    Args:
        y: Response variable array (metabolite abundance).
        X: Feature matrix (BGC counts).
        tree_path: Path to the Newick tree file.
        n_permutations: Number of permutations to perform.
        random_state: Random seed for reproducibility.

    Returns:
        Dictionary containing 'mean_baseline_r2', 'std_baseline_r2', 'min_baseline_r2', 'max_baseline_r2'.
    """
    if random_state is not None:
        np.random.seed(random_state)

    logger.info(f"Starting phylogenetic permutation test with {n_permutations} permutations.")

    # Load phylogeny and construct covariance matrix
    try:
        tree = load_phylogeny(tree_path)
        cov_matrix = construct_covariance_matrix(tree)
    except Exception as e:
        logger.error(f"Failed to load phylogeny or construct covariance matrix: {e}")
        raise

    # Ensure dimensions match
    if cov_matrix.shape[0] != len(y):
        raise ValueError(f"Phylogeny ({cov_matrix.shape[0]} tips) does not match data length ({len(y)}).")

    # Cholesky decomposition to decorrelate
    # V = L * L^T  =>  V^{-1} = (L^T)^{-1} * L^{-1}
    # We want to transform y and X such that the errors are i.i.d.
    # If y = X*beta + e, where e ~ N(0, V), then L^{-1} * y = L^{-1} * X * beta + L^{-1} * e
    # where L^{-1} * e ~ N(0, I).
    try:
        L = np.linalg.cholesky(cov_matrix)
        L_inv = np.linalg.inv(L)
    except np.linalg.LinAlgError:
        logger.warning("Covariance matrix is not positive definite. Adding jitter.")
        jitter = np.eye(cov_matrix.shape[0]) * 1e-6
        L = np.linalg.cholesky(cov_matrix + jitter)
        L_inv = np.linalg.inv(L)

    # Decorrelate data
    y_decorrelated = L_inv @ y
    X_decorrelated = L_inv @ X

    baseline_r2s = []

    # Train a simple model on the original decorrelated data to get a baseline for comparison?
    # No, the task is to shuffle labels to get a NULL distribution.
    # We will shuffle y_decorrelated, then transform back (or just predict on X_decorrelated with shuffled y)
    # Actually, the standard phylogenetic permutation shuffles the independent contrasts.
    # Simplified approach: Shuffle y_decorrelated, then predict using X_decorrelated.
    # This breaks the phylogenetic signal in y while keeping X fixed (assuming X is not phylogenetically structured or we are testing against that).
    # A more rigorous test would permute the tips of the tree for both X and y, but here we focus on y permutation.

    for i in range(n_permutations):
        # Shuffle the decorrelated response
        y_permuted_decorrelated = np.random.permutation(y_decorrelated)

        # We can either transform back or just fit on decorrelated space.
        # Fitting on decorrelated space is equivalent to fitting the PGLS on the original data with permuted y.
        # Let's fit a simple OLS on the decorrelated space to get R².
        # y_permuted = X_decorrelated * beta + error
        # We use a simple linear model (ElasticNet with alpha=0 for OLS, or just np.linalg.lstsq)
        # Using sklearn for consistency with the rest of the pipeline
        model = ElasticNet(alpha=0.0, l1_ratio=0.0, max_iter=1000)
        try:
            model.fit(X_decorrelated, y_permuted_decorrelated)
            y_pred = model.predict(X_decorrelated)
            r2 = r2_score(y_permuted_decorrelated, y_pred)
            baseline_r2s.append(r2)
        except Exception as e:
            logger.warning(f"Permutation {i} failed: {e}. Skipping.")
            continue

    if not baseline_r2s:
        raise RuntimeError("No valid permutations could be completed.")

    result = {
        "mean_baseline_r2": float(np.mean(baseline_r2s)),
        "std_baseline_r2": float(np.std(baseline_r2s)),
        "min_baseline_r2": float(np.min(baseline_r2s)),
        "max_baseline_r2": float(np.max(baseline_r2s)),
        "n_permutations": n_permutations
    }

    logger.info(f"Phylogenetic permutation baseline R²: mean={result['mean_baseline_r2']:.4f}, std={result['std_baseline_r2']:.4f}")
    return result

def calculate_significance(
    model_r2: float,
    baseline_stats: Dict[str, float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Compare model R² against baseline (p < 0.05 check).

    Args:
        model_r2: The R² score from the actual model.
        baseline_stats: Statistics from run_phylogenetic_permutation.
        alpha: Significance level.

    Returns:
        Dictionary with 'is_significant', 'p_value', 'z_score'.
    """
    mean_base = baseline_stats['mean_baseline_r2']
    std_base = baseline_stats['std_baseline_r2']

    if std_base == 0:
        p_value = 0.0 if model_r2 > mean_base else 1.0
    else:
        z_score = (model_r2 - mean_base) / std_base
        # Approximate p-value from Z-score (one-tailed)
        from scipy.stats import norm
        p_value = 1 - norm.cdf(z_score)

    is_significant = p_value < alpha

    logger.info(f"Significance test: R²={model_r2:.4f}, Baseline Mean={mean_base:.4f}, Z={z_score:.4f}, p={p_value:.4f}, Significant={is_significant}")

    return {
        "is_significant": is_significant,
        "p_value": float(p_value),
        "z_score": float(z_score) if std_base > 0 else 0.0
    }

def report_primary_results(
    metrics_path: str,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract, format, and log the PGLS R² and feature importance as the primary result.
    Ensures FR-010 compliance.
    """
    if output_path is None:
        output_path = "data/processed/primary_results.json"

    with open(metrics_path, 'r') as f:
        metrics = json.load(f)

    # Assume metrics contains 'pgls' or 'primary_model' results
    # Adjust key based on actual output from T024/T024b
    primary_result = metrics.get('primary_model', metrics.get('pgls', {}))

    report = {
        "primary_r2": primary_result.get('r2'),
        "feature_importance": primary_result.get('feature_importance', []),
        "model_type": "PGLS",
        "timestamp": str(pd.Timestamp.now())
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Primary results reported to {output_path}")
    return report

def main():
    """
    Main entry point for running the phylogenetic permutation test.
    This script is designed to be run after T024 (PGLS training) and T025 (Evaluation).
    It expects the aligned data and phylogeny to be available.
    """
    # Configuration
    DATA_PATH = "data/processed/aligned_matrix.csv"
    PHYLO_PATH = "data/raw/phylogeny/species_tree.nwk" # Adjust path as per project structure
    N_PERMUTATIONS = 100
    OUTPUT_PATH = "data/processed/permutation_baseline.json"

    logger.info("Starting phylogenetic permutation baseline calculation.")

    # Load data
    try:
        df = pd.read_csv(DATA_PATH)
        # Assume 'species' column exists and is index or used for merging
        # Assume 'metabolite_abundance' is the target and 'bgc_counts' are features
        # Adjust column names based on actual aligned matrix schema
        if 'metabolite_abundance' not in df.columns:
            # Fallback or error handling
            raise ValueError("Column 'metabolite_abundance' not found in aligned matrix.")
        
        y = df['metabolite_abundance'].values
        X = df.drop(columns=['species', 'metabolite_abundance']).values
    except Exception as e:
        logger.error(f"Failed to load aligned data: {e}")
        raise

    # Run permutation
    try:
        baseline_results = run_phylogenetic_permutation(
            y=y,
            X=X,
            tree_path=PHYLO_PATH,
            n_permutations=N_PERMUTATIONS
        )
    except Exception as e:
        logger.error(f"Permutation test failed: {e}")
        raise

    # Save results
    path = Path(OUTPUT_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(baseline_results, f, indent=2)

    logger.info(f"Phylogenetic permutation baseline saved to {OUTPUT_PATH}")
    return baseline_results

if __name__ == "__main__":
    main()