import os
import sys
import logging
import numpy as np
import json
import time
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any
import pandas as pd
from scipy import stats
from utils import set_global_seed, setup_logging, record_artifact_hash
from config import ensure_directories
from llmxive_toolkit import paths

logger = logging.getLogger(__name__)


def calculate_observed_metric(X: np.ndarray, y: np.ndarray, model: Any) -> float:
    """
    Calculate the observed Pearson correlation coefficient (r) between
    model predictions and actual labels.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target labels (n_samples,)
        model: Fitted model with a .predict() method
        
    Returns:
        Pearson correlation coefficient (r)
    """
    predictions = model.predict(X)
    r, _ = stats.pearsonr(predictions, y)
    return float(r)


def run_bootstrap_ci(
    X: np.ndarray,
    y: np.ndarray,
    model_class: Any,
    n_iterations: int = 200,
    random_state: int = 42
) -> Tuple[float, float, float]:
    """
    Perform bootstrap resampling to calculate 95% CI for Pearson r.
    
    This helper function implements the core bootstrap logic without any
    runtime‑limit guard. It is retained for backward compatibility.
    
    Args:
        X: Feature matrix
        y: Target labels
        model_class: Class of the model to instantiate
        n_iterations: Number of bootstrap iterations
        random_state: Seed for reproducibility
        
    Returns:
        Tuple of (observed_r, lower_ci, upper_ci)
    """
    set_global_seed(random_state)
    ensure_directories()
    
    # Fit model on full data to get observed r
    model = model_class()
    model.fit(X, y)
    observed_r = calculate_observed_metric(X, y, model)
    
    bootstrap_r = []
    n_samples = len(y)
    
    for i in range(n_iterations):
        # Resample with replacement
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        X_resample = X[indices]
        y_resample = y[indices]
        
        # Fit model on resampled data
        model_boot = model_class()
        model_boot.fit(X_resample, y_resample)
        r_boot = calculate_observed_metric(X_resample, y_resample, model_boot)
        bootstrap_r.append(r_boot)
        
    bootstrap_r = np.array(bootstrap_r)
    lower_ci = float(np.percentile(bootstrap_r, 2.5))
    upper_ci = float(np.percentile(bootstrap_r, 97.5))
    
    return observed_r, lower_ci, upper_ci


def calculate_empirical_pvalue(observed_r: float, null_distribution: np.ndarray) -> float:
    """
    Calculate empirical p-value by comparing observed r against the null distribution.
    
    The p-value is calculated as the proportion of null distribution values that are
    as extreme or more extreme than the observed value (two-tailed test).
    
    Args:
        observed_r: The observed Pearson correlation coefficient from real data
        null_distribution: Array of correlation coefficients from permutation tests
        
    Returns:
        Empirical p-value
    """
    if len(null_distribution) == 0:
        raise ValueError("Null distribution is empty. Cannot calculate p-value.")
    
    # Two-tailed test: compare absolute values
    abs_observed = np.abs(observed_r)
    abs_null = np.abs(null_distribution)
    
    extreme_count = np.sum(abs_null >= abs_observed)
    p_value = extreme_count / len(null_distribution)
    
    logger.info(f"Observed r: {observed_r:.4f}")
    logger.info(f"Null distribution size: {len(null_distribution)}")
    logger.info(f"Extreme count (|null| >= |observed|): {extreme_count}")
    logger.info(f"Empirical p-value: {p_value:.4f}")
    
    return float(p_value)


def load_null_distribution(path: Path) -> np.ndarray:
    """
    Load the null distribution from a saved file.
    
    Args:
        path: Path to the null distribution file (CSV or NPY)
        
    Returns:
        NumPy array of correlation coefficients
    """
    if path.suffix == '.npy':
        return np.load(path)
    elif path.suffix == '.csv':
        df = pd.read_csv(path)
        # Assume first column contains the correlation values
        return df.iloc[:, 0].values
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")


def save_null_distribution(null_dist: np.ndarray, path: Path) -> None:
    """
    Save the null distribution to a file.
    
    Args:
        null_dist: NumPy array of correlation coefficients
        path: Path to save the file
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, null_dist)
    logger.info(f"Null distribution saved to {path}")


def run_modeling_pipeline(
    feature_matrix_path: Path,
    labels_path: Path,
    null_distribution_path: Path,
    output_artifact_path: Path,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Main pipeline function to calculate observed metric, load null distribution,
    compute empirical p-value, and save results.
    
    Args:
        feature_matrix_path: Path to feature matrix CSV
        labels_path: Path to labels CSV
        null_distribution_path: Path to null distribution file
        output_artifact_path: Path to save the result artifact JSON
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary containing results
    """
    set_global_seed(random_state)
    ensure_directories()
    setup_logging()
    
    # Load data
    logger.info(f"Loading features from {feature_matrix_path}")
    X = pd.read_csv(feature_matrix_path).values
    
    logger.info(f"Loading labels from {labels_path}")
    labels_df = pd.read_csv(labels_path)
    y = labels_df.iloc[:, 0].values  # Assume first column is the target
    
    # Load null distribution (generated by T022)
    logger.info(f"Loading null distribution from {null_distribution_path}")
    if not null_distribution_path.exists():
        raise FileNotFoundError(
            f"Null distribution file not found at {null_distribution_path}. "
            "Please ensure T022 has been executed successfully."
        )
    null_dist = load_null_distribution(null_distribution_path)
    
    # Simple Elastic Net model for observed metric
    from sklearn.linear_model import ElasticNet
    model = ElasticNet(alpha=0.5, l1_ratio=0.5, random_state=random_state, max_iter=5000)
    model.fit(X, y)
    observed_r = calculate_observed_metric(X, y, model)
    
    # Calculate empirical p-value
    p_value = calculate_empirical_pvalue(observed_r, null_dist)
    
    # Prepare results
    results = {
        "observed_r": observed_r,
        "p_value": p_value,
        "null_distribution_size": len(null_dist),
        "null_distribution_stats": {
            "mean": float(np.mean(null_dist)),
            "std": float(np.std(null_dist)),
            "min": float(np.min(null_dist)),
            "max": float(np.max(null_dist))
        }
    }
    
    # Save results
    output_artifact_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_artifact_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_artifact_path}")
    record_artifact_hash(output_artifact_path)
    
    return results


def train_nested_cv(
    X: np.ndarray,
    y: np.ndarray,
    outer_folds: int = 5,
    inner_folds: int = 5,
    random_state: int = 42,
    l1_ratios: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Perform nested cross‑validation using Elastic Net (α fixed at 0.5,
    l1_ratio tuned in the inner loop).
    
    The outer loop evaluates model performance; the inner loop selects the
    l1_ratio that minimises mean absolute error.
    
    Returns a dictionary containing:
        - 'r_per_fold': list of Pearson r for each outer fold
        - 'mae_per_fold': list of MAE for each outer fold
        - 'pearson_r_mean': mean Pearson r across outer folds (float)
        - 'mae_mean': mean MAE across outer folds (float)
        - 'r_mean': alias for 'pearson_r_mean' (kept for backward compatibility)
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        outer_folds: Number of outer CV folds (default 5)
        inner_folds: Number of inner CV folds for hyper‑parameter tuning (default 5)
        random_state: Seed for reproducibility
        l1_ratios: Optional list of l1_ratio values to search. If None,
                   a default linear grid from 0.0 to 1.0 (inclusive) with 11 points is used.
    
    Returns:
        dict with performance metrics.
    """
    from sklearn.linear_model import ElasticNet
    from sklearn.model_selection import KFold
    from sklearn.metrics import mean_absolute_error

    set_global_seed(random_state)

    if l1_ratios is None:
        # Default grid: 0.0, 0.1, ..., 1.0 (11 values)
        l1_ratios = np.linspace(0.0, 1.0, 11).tolist()

    outer_cv = KFold(n_splits=outer_folds, shuffle=True, random_state=random_state)

    r_scores: List[float] = []
    mae_scores: List[float] = []

    for outer_fold, (train_idx, test_idx) in enumerate(outer_cv.split(X), start=1):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # ---- Inner CV for hyper‑parameter selection ----
        inner_cv = KFold(n_splits=inner_folds, shuffle=True, random_state=random_state)
        inner_mae_means: List[float] = []

        for l1_ratio in l1_ratios:
            mae_inner_folds: List[float] = []
            for inner_train_idx, inner_val_idx in inner_cv.split(X_train):
                X_inner_train, X_val = X_train[inner_train_idx], X_train[inner_val_idx]
                y_inner_train, y_val = y_train[inner_train_idx], y_train[inner_val_idx]

                model = ElasticNet(
                    alpha=0.5,                 # Fixed α as required by FR‑003
                    l1_ratio=l1_ratio,
                    random_state=random_state,
                    max_iter=5000
                )
                model.fit(X_inner_train, y_inner_train)
                preds = model.predict(X_val)
                mae = mean_absolute_error(y_val, preds)
                mae_inner_folds.append(mae)
            # Average MAE for this l1_ratio across inner folds
            inner_mae_means.append(np.mean(mae_inner_folds))

        # Choose l1_ratio with lowest inner MAE
        best_l1_ratio = l1_ratios[int(np.argmin(inner_mae_means))]

        # ---- Train on full outer training set with best l1_ratio ----
        best_model = ElasticNet(
            alpha=0.5,
            l1_ratio=best_l1_ratio,
            random_state=random_state,
            max_iter=5000
        )
        best_model.fit(X_train, y_train)

        # ---- Evaluate on outer test set ----
        test_preds = best_model.predict(X_test)
        r, _ = stats.pearsonr(test_preds, y_test)
        mae = mean_absolute_error(y_test, test_preds)

        r_scores.append(float(r))
        mae_scores.append(float(mae))

        logger.info(
            f"Outer Fold {outer_fold}/{outer_folds}: "
            f"best_l1_ratio={best_l1_ratio:.5f}, r={r:.4f}, MAE={mae:.4f}"
        )

    # Compute means
    pearson_r_mean = float(np.mean(r_scores))
    mae_mean = float(np.mean(mae_scores))

    results = {
        "r_per_fold": r_scores,
        "mae_per_fold": mae_scores,
        "pearson_r_mean": pearson_r_mean,
        "mae_mean": mae_mean,
        # Backward‑compatible aliases
        "r_mean": pearson_r_mean,
        "r": pearson_r_mean,
        "mae": mae_mean
    }

    logger.info(f"Nested CV completed: pearson_r_mean={pearson_r_mean:.4f}, mae_mean={mae_mean:.4f}")
    return results


def run_global_permutation_test(
    X: np.ndarray,
    y: np.ndarray,
    n_permutations: int = 1000,
    seed: int = 42,
    max_permutations: int = 1000
) -> Tuple[np.ndarray, float]:
    """
    Perform global permutation testing (FR‑004).

    For each permutation, the target labels are shuffled **once per outer CV
    iteration**, the full nested CV is executed, and the resulting mean Pearson
    correlation (r) is stored. The function returns the null distribution of
    mean r values and the empirical p-value compared to the observed metric.

    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        n_permutations: Number of permutations to perform.
        seed: Random seed for reproducibility.
        max_permutations: Upper bound on allowed permutations (runtime guard).

    Returns:
        A tuple (null_distribution, p_value) where:
            - null_distribution is a NumPy array of shape (n_permutations,)
              containing the mean r from each permutation.
            - p_value is the empirical two‑tailed p‑value.
    """
    if n_permutations > max_permutations:
        raise ValueError(
            f"Requested {n_permutations} permutations exceeds the allowed maximum "
            f"of {max_permutations}. Reduce n_permutations or increase max_permutations."
        )

    set_global_seed(seed)

    # Compute observed metric once on the original data
    observed_results = train_nested_cv(X, y, random_state=seed)
    observed_r = observed_results["pearson_r_mean"]

    # Prepare outer CV splitter (same as in train_nested_cv)
    from sklearn.model_selection import KFold
    outer_cv = KFold(n_splits=5, shuffle=True, random_state=seed)

    null_r = np.empty(n_permutations, dtype=float)

    for i in range(n_permutations):
        # For each permutation we will compute the mean r across outer folds,
        # shuffling the labels separately for each outer fold.
        r_folds: List[float] = []
        # Use a deterministic RNG per permutation for reproducibility
        perm_rng = np.random.RandomState(seed + i)

        for train_idx, test_idx in outer_cv.split(X):
            # Shuffle labels for this outer fold
            y_shuffled = y.copy()
            perm_rng.shuffle(y_shuffled)

            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y_shuffled[train_idx], y_shuffled[test_idx]

            # ---- Inner CV for hyper‑parameter selection (same logic as train_nested_cv) ----
            from sklearn.linear_model import ElasticNet
            from sklearn.metrics import mean_absolute_error

            inner_cv = KFold(n_splits=5, shuffle=True, random_state=seed + i)
            # Use the same default grid as train_nested_cv
            l1_ratios = np.linspace(0.0, 1.0, 11).tolist()
            inner_mae_means: List[float] = []

            for l1_ratio in l1_ratios:
                mae_inner_folds: List[float] = []
                for inner_train_idx, inner_val_idx in inner_cv.split(X_train):
                    X_inner_train, X_val = X_train[inner_train_idx], X_train[inner_val_idx]
                    y_inner_train, y_val = y_train[inner_train_idx], y_train[inner_val_idx]

                    model = ElasticNet(
                        alpha=0.5,
                        l1_ratio=l1_ratio,
                        random_state=seed + i,
                        max_iter=5000
                    )
                    model.fit(X_inner_train, y_inner_train)
                    preds = model.predict(X_val)
                    mae_inner_folds.append(mean_absolute_error(y_val, preds))
                inner_mae_means.append(np.mean(mae_inner_folds))

            # Select best l1_ratio for this outer fold
            best_l1_ratio = l1_ratios[int(np.argmin(inner_mae_means))]

            # Train best model on the outer training data
            best_model = ElasticNet(
                alpha=0.5,
                l1_ratio=best_l1_ratio,
                random_state=seed + i,
                max_iter=5000
            )
            best_model.fit(X_train, y_train)

            # Evaluate on the outer test set
            test_preds = best_model.predict(X_test)
            r, _ = stats.pearsonr(test_preds, y_test)
            r_folds.append(float(r))

        # Mean Pearson r for this permutation
        null_r[i] = float(np.mean(r_folds))

    # Compute empirical p‑value
    p_value = calculate_empirical_pvalue(observed_r, null_r)

    logger.info(
        f"Global permutation test completed: {n_permutations} permutations, "
        f"observed r={observed_r:.4f}, p-value={p_value:.4f}"
    )

    return null_r, p_value


def bootstrap_ci(
    r_values: np.ndarray,
    n_iterations: int = 200,
    random_state: int = 42,
    max_runtime_seconds: int = 6 * 3600,
    output_path: Optional[Path] = None
) -> Tuple[float, float]:
    """
    Perform bootstrap resampling to obtain a 95 % confidence interval for the
    observed Pearson correlation coefficient using the supplied outer‑fold
    r values. A runtime‑limit guard aborts the procedure (with a warning) if
    the projected total runtime would exceed the CI budget (default 6 hours).

    Args:
        r_values: Array of outer‑fold Pearson r values (length = number of folds).
        n_iterations: Number of bootstrap resamples (default 200).
        random_state: Seed for reproducibility.
        max_runtime_seconds: Upper bound on total runtime (default 6 h).
        output_path: Optional path to write the CI JSON artifact. If provided,
                     the file will contain {"ci_lower": ..., "ci_upper": ...}.

    Returns:
        Tuple (ci_lower, ci_upper).
    """
    if r_values.size == 0:
        raise ValueError("r_values array is empty; cannot compute bootstrap CI.")

    set_global_seed(random_state)
    ensure_directories()

    # Default output location if none provided
    if output_path is None:
        output_path = paths.artifacts("bootstrap_ci.json")

    bootstrap_means = []
    n_samples = r_values.shape[0]

    start_time = time.time()
    for i in range(n_iterations):
        # Projected runtime guard
        elapsed = time.time() - start_time
        if i > 0:
            projected_total = elapsed / (i + 1) * n_iterations
            if projected_total > max_runtime_seconds:
                logger.warning(
                    f"Bootstrap CI aborted after {i+1} iterations: projected runtime "
                    f"{projected_total/3600:.2f} h exceeds limit of {max_runtime_seconds/3600:.2f} h."
                )
                break

        # Resample r values with replacement and compute mean
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        sample_mean = float(np.mean(r_values[indices]))
        bootstrap_means.append(sample_mean)

    if not bootstrap_means:
        raise RuntimeError("No bootstrap iterations were completed; cannot compute CI.")

    bootstrap_means = np.array(bootstrap_means)
    ci_lower = float(np.percentile(bootstrap_means, 2.5))
    ci_upper = float(np.percentile(bootstrap_means, 97.5))

    # Write artifact if a path is supplied
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ci_dict = {"ci_lower": ci_lower, "ci_upper": ci_upper}
    with open(output_path, 'w') as f:
        json.dump(ci_dict, f, indent=2)
    logger.info(f"Bootstrap CI saved to {output_path}")
    record_artifact_hash(output_path)

    return ci_lower, ci_upper


def compute_empirical_pvalue(
    observed_r: float,
    null_distribution: np.ndarray,
    mae: float,
    ci_lower: float,
    ci_upper: float,
    n_permutations: int,
    n_bootstrap: int,
    output_path: Path
) -> float:
    """
    Compute the empirical p‑value for the observed Pearson correlation coefficient
    against a permutation null distribution and store the full result in a JSON artifact.

    This function satisfies Task T013. It writes a JSON file containing the fields:
    ``pearson_r``, ``mae``, ``p_value``, ``ci_lower``, ``ci_upper``,
    ``n_permutations``, and ``n_bootstrap``.

    Args:
        observed_r: Observed Pearson correlation coefficient (float).
        null_distribution: 1‑D NumPy array of correlation coefficients obtained from
                           permutation testing.
        mae: Mean Absolute Error from the nested‑CV model (float).
        ci_lower: Lower bound of the 95 % bootstrap confidence interval (float).
        ci_upper: Upper bound of the 95 % bootstrap confidence interval (float).
        n_permutations: Number of permutations performed (int).
        n_bootstrap: Number of bootstrap resamples used for CI (int).
        output_path: Path where the JSON result artifact should be saved
                     (e.g., ``artifacts/model_result.json``).

    Returns:
        The computed empirical p‑value (float).
    """
    # Compute p‑value using the existing helper (two‑tailed)
    p_value = calculate_empirical_pvalue(observed_r, null_distribution)

    # Prepare result dictionary with all required fields
    result = {
        "pearson_r": float(observed_r),
        "mae": float(mae),
        "p_value": float(p_value),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "n_permutations": int(n_permutations),
        "n_bootstrap": int(n_bootstrap)
    }

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON artifact
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Empirical p‑value ({p_value:.4f}) written to {output_path}")
    # Record artifact hash for reproducibility tracking
    record_artifact_hash(output_path)

    return p_value


def main():
    """Entry point for the modeling pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate empirical p-value from null distribution")
    parser.add_argument("--features", type=str, required=True, help="Path to feature matrix CSV")
    parser.add_argument("--labels", type=str, required=True, help="Path to labels CSV")
    parser.add_argument("--null-dist", type=str, required=True, help="Path to null distribution file")
    parser.add_argument("--output", type=str, required=True, help="Path to output artifact JSON")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    results = run_modeling_pipeline(
        feature_matrix_path=Path(args.features),
        labels_path=Path(args.labels),
        null_distribution_path=Path(args.null_dist),
        output_artifact_path=Path(args.output),
        random_state=args.seed
    )
    
    print(f"Observed r: {results['observed_r']:.4f}")
    print(f"Empirical p-value: {results['p_value']:.4f}")
    print(f"Null distribution size: {results['null_distribution_size']}")

if __name__ == "__main__":
    main()