import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from scipy import stats
from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_val_score
from scipy.stats import ks_2samp

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import ensure_dirs
from utils.logging_setup import get_logger

# Ensure directories exist
ensure_dirs()

logger = get_logger(__name__)

def load_model_and_data() -> Tuple[Any, pd.DataFrame, pd.Series]:
    """
    Load the trained model and the feature matrix used for training.
    Since T026 saves the model and T025 saves the feature matrix,
    we attempt to load them.
    """
    feature_matrix_path = project_root / "data" / "processed" / "feature_matrix.csv"
    
    if not feature_matrix_path.exists():
        raise FileNotFoundError(
            f"Feature matrix not found at {feature_matrix_path}. "
            "Please ensure T025 (Assemble final feature matrix) has been completed."
        )

    logger.info(f"Loading feature matrix from {feature_matrix_path}")
    df = pd.read_csv(feature_matrix_path)

    # Identify target column. Based on plan.md, the target is tDCS response.
    # We assume the column is named 'response' or 'tdcs_response'.
    target_col = None
    candidates = ['response', 'tdcs_response', 'target']
    for cand in candidates:
        if cand in df.columns:
            target_col = cand
            break
    
    if target_col is None:
        # Fallback: assume last column is target if 'response' not found
        # This is a heuristic; strict implementation should rely on schema.
        logger.warning(f"Target column not explicitly found. Using last column: {df.columns[-1]}")
        target_col = df.columns[-1]

    X = df.drop(columns=[target_col])
    y = df[target_col]

    # We need to refit the model for the permutation test to get the null distribution.
    # We load the best alpha from the CV results if available, otherwise use a default.
    cv_results_path = project_root / "data" / "processed" / "model_cv_results.json"
    best_alpha = 1.0
    if cv_results_path.exists():
        with open(cv_results_path, 'r') as f:
            cv_data = json.load(f)
            if 'best_alpha' in cv_data:
                best_alpha = cv_data['best_alpha']
                logger.info(f"Loaded best_alpha {best_alpha} from CV results")
            else:
                logger.warning("best_alpha not found in CV results, using default 1.0")
    else:
        logger.warning("model_cv_results.json not found, using default alpha=1.0")

    model = Ridge(alpha=best_alpha)
    return model, X, y

def run_permutation_test(
    model: Any,
    X: pd.DataFrame,
    y: pd.Series,
    n_permutations: int = 1000,
    random_state: int = 42
) -> Tuple[np.ndarray, float, float, float]:
    """
    Perform permutation testing to assess the significance of the model's R^2.
    
    Returns:
        null_distribution: Array of R^2 values from permuted data.
        observed_r2: R^2 of the model on original data.
        p_value: Proportion of null R^2 >= observed R^2.
        ks_statistic: KS statistic for uniformity of null distribution.
    """
    logger.info(f"Starting permutation test with {n_permutations} permutations...")
    logger.info(f"Dataset size: {len(y)} subjects")

    # Check sample size constraint
    if len(y) < 30:
        logger.warning(f"Sample size N={len(y)} < 30. Skipping permutation test as per protocol.")
        # Return empty/None indicators if skipping
        return np.array([]), 0.0, 1.0, 0.0

    # Calculate observed R^2
    model.fit(X, y)
    scores = cross_val_score(model, X, y, cv=5, scoring='r2')
    observed_r2 = np.mean(scores)
    logger.info(f"Observed mean R^2: {observed_r2:.4f}")

    # Initialize null distribution
    null_distribution = np.zeros(n_permutations)
    rng = np.random.default_rng(random_state)

    # Run permutations
    for i in range(n_permutations):
        # Shuffle target
        y_perm = y.sample(frac=1, random_state=rng.integers(0, 2**31)).reset_index(drop=True)
        
        # Refit and score
        model.fit(X, y_perm)
        perm_scores = cross_val_score(model, X, y_perm, cv=5, scoring='r2')
        null_distribution[i] = np.mean(perm_scores)
        
        if (i + 1) % 100 == 0:
            logger.debug(f"Permutation {i+1}/{n_permutations} completed")

    # Calculate p-value
    # One-sided test: is observed R^2 significantly greater than null?
    p_value = np.sum(null_distribution >= observed_r2) / n_permutations
    logger.info(f"Permutation p-value: {p_value:.4f}")

    # Kolmogorov-Smirnov test for uniformity of the null distribution
    # Under the null hypothesis (no effect), the R^2 values from permuted data
    # should be centered around 0 and roughly symmetric/uniform in the tails.
    # We test against a uniform distribution over the range of the null distribution
    # to check for unexpected structure, or more commonly, check if the null
    # distribution is centered at 0.
    # However, the task specifically asks to assess uniformity of the null distribution.
    # A common check is to see if the null distribution is consistent with a 
    # distribution centered at 0. 
    # Let's perform KS test against a uniform distribution spanning the min and max of the null.
    # Note: This is a specific interpretation of "assess uniformity". 
    # A more robust statistical test for the null hypothesis of "no effect" is simply the p-value.
    # But strictly following the prompt: "compute Kolmogorov-Smirnov statistic and p-value to assess uniformity".
    
    # We test if the null distribution is uniform.
    # We generate a theoretical uniform distribution with the same min/max as the observed null.
    ks_stat, ks_p = ks_2samp(null_distribution, np.random.uniform(np.min(null_distribution), np.max(null_distribution), n_permutations))
    
    # Actually, a better interpretation for "assess uniformity" in the context of null distributions
    # is often checking if the null is flat. But KS test is typically used to compare to a specific distribution.
    # Let's compare the null distribution to a Uniform(min, max) to see if it deviates from uniformity.
    # If the null is truly random noise, it might be Gaussian, not Uniform.
    # However, if the instruction insists on KS for uniformity, we proceed with KS vs Uniform.
    # Let's generate a theoretical uniform sample for comparison.
    uniform_sample = np.random.uniform(np.min(null_distribution), np.max(null_distribution), n_permutations)
    ks_stat, ks_p = ks_2samp(null_distribution, uniform_sample)
    
    logger.info(f"KS Statistic (vs Uniform): {ks_stat:.4f}, p-value: {ks_p:.4f}")

    return null_distribution, observed_r2, p_value, ks_stat

def save_results(
    null_distribution: np.ndarray,
    observed_r2: float,
    p_value: float,
    ks_stat: float,
    ks_p: float,
    n_permutations: int
):
    """Save the permutation test results to CSV and JSON."""
    processed_dir = project_root / "data" / "processed"
    
    # Save null distribution
    perm_csv_path = processed_dir / "perm_null_distribution.csv"
    df_null = pd.DataFrame({'r2_value': null_distribution})
    df_null.to_csv(perm_csv_path, index=False)
    logger.info(f"Saved null distribution to {perm_csv_path}")

    # Save KS test results
    ks_json_path = processed_dir / "ks_test.json"
    ks_data = {
        "ks_statistic": float(ks_stat),
        "ks_p_value": float(ks_p),
        "n_permutations": n_permutations,
        "test_description": "Kolmogorov-Smirnov test comparing null R^2 distribution to a uniform distribution"
    }
    with open(ks_json_path, 'w') as f:
        json.dump(ks_data, f, indent=2)
    logger.info(f"Saved KS test results to {ks_json_path}")

    # Also save a summary of the permutation test
    summary_path = processed_dir / "permutation_test_summary.json"
    summary_data = {
        "observed_r2": float(observed_r2),
        "p_value": float(p_value),
        "n_permutations": n_permutations,
        "null_distribution_mean": float(np.mean(null_distribution)) if len(null_distribution) > 0 else None,
        "null_distribution_std": float(np.std(null_distribution)) if len(null_distribution) > 0 else None,
        "ks_statistic": float(ks_stat),
        "ks_p_value": float(ks_p)
    }
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
    logger.info(f"Saved permutation test summary to {summary_path}")

def main():
    """Main entry point for permutation testing."""
    logger.info("Starting Permutation Testing (T033)...")
    
    try:
        model, X, y = load_model_and_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Determine number of permutations
    n_subjects = len(y)
    if n_subjects >= 30:
        n_permutations = 1000
    else:
        logger.warning(f"Skipping permutation test: N={n_subjects} < 30")
        # Still create empty outputs or log skip? The task says "log skip".
        # We will create the files with a note that it was skipped.
        processed_dir = project_root / "data" / "processed"
        with open(processed_dir / "ks_test.json", 'w') as f:
            json.dump({"status": "skipped", "reason": "N < 30"}, f, indent=2)
        with open(processed_dir / "perm_null_distribution.csv", 'w') as f:
            f.write("r2_value\n") # Empty file with header
        sys.exit(0)

    null_dist, obs_r2, p_val, ks_stat = run_permutation_test(
        model, X, y, n_permutations=n_permutations, random_state=42
    )

    # Calculate KS p-value properly
    # We compare the null distribution to a uniform distribution
    # as requested to "assess uniformity"
    uniform_sample = np.random.uniform(np.min(null_dist), np.max(null_dist), len(null_dist))
    _, ks_p = ks_2samp(null_dist, uniform_sample)

    save_results(null_dist, obs_r2, p_val, ks_stat, ks_p, n_permutations)

    logger.info("Permutation testing completed successfully.")

if __name__ == "__main__":
    main()
