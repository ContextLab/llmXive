"""
T022: Implement permutation test for R² significance on held-out test set.

This script performs a permutation test to assess the statistical significance
of the R² score obtained from the predictive model. It operates ONLY on the
held-out test set to prevent data leakage, using split indices from
`data/processed/split_indices.json` and the random seed from `config.py`.

Requirements:
- Must run after T017 (modeling) completes.
- Uses `utils.stats_helpers.permutation_test`.
- Outputs results to `data/processed/permutation_results.json`.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_path, get_seed, set_global_seed
from utils.stats_helpers import permutation_test


def load_features() -> pd.DataFrame:
    """Load the processed features dataset."""
    features_path = get_path("processed_features")
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found at {features_path}. "
                                "Ensure T015 (feature computation) has completed.")
    return pd.read_csv(features_path)


def load_split_indices() -> Dict[str, Any]:
    """Load the train/test split indices from the modeling step."""
    split_path = get_path("split_indices")
    if not os.path.exists(split_path):
        raise FileNotFoundError(f"Split indices file not found at {split_path}. "
                                "Ensure T017 (modeling) has completed.")
    with open(split_path, "r") as f:
        return json.load(f)


def prepare_test_data(
    features_df: pd.DataFrame,
    split_indices: Dict[str, Any]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare X and y for the held-out test set only.

    Args:
        features_df: The full features dataframe.
        split_indices: Dict containing 'test_indices' key.

    Returns:
        X_test: Feature matrix for test set.
        y_test: Target vector (median RT) for test set.
    """
    test_indices = split_indices.get("test_indices")
    if not test_indices:
        raise ValueError("No 'test_indices' found in split_indices.json.")

    # Filter dataframe to test set only
    test_df = features_df.iloc[test_indices].reset_index(drop=True)

    # Define feature columns (exclude 'participant_id' and 'median_rt')
    feature_cols = [col for col in test_df.columns if col not in ["participant_id", "median_rt"]]
    
    if not feature_cols:
        raise ValueError("No feature columns found in the dataset.")

    X_test = test_df[feature_cols].values
    y_test = test_df["median_rt"].values

    return X_test, y_test


def run_permutation_test(
    X: np.ndarray,
    y: np.ndarray,
    n_permutations: int = 1000,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Run the permutation test on the provided X and y.

    Uses the `permutation_test` helper from `utils.stats_helpers`.
    The helper computes the R² of the real model, then permutes y
    `n_permutations` times to build a null distribution of R² scores.

    Args:
        X: Feature matrix.
        y: Target vector.
        n_permutations: Number of permutations to run.
        random_state: Random seed for reproducibility.

    Returns:
        Dict containing observed_r2, p_value, null_distribution, and n_permutations.
    """
    # Fit the real model to get observed R²
    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)
    observed_r2 = r2_score(y, y_pred)

    # Perform permutation test
    # The helper function returns (p_value, null_distribution)
    # We pass the observed R² as the statistic to compare against
    p_value, null_dist = permutation_test(
        X, y,
        metric="r2",
        n_permutations=n_permutations,
        random_state=random_state
    )

    return {
        "observed_r2": float(observed_r2),
        "p_value": float(p_value),
        "null_distribution": [float(x) for x in null_dist],
        "n_permutations": n_permutations,
        "significant_at_005": p_value < 0.05,
        "significant_at_001": p_value < 0.01
    }


def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save the permutation test results to a JSON file."""
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Permutation test results saved to {output_path}")


def main():
    """Main entry point for the permutation test script."""
    parser = argparse.ArgumentParser(description="Run permutation test for R² significance.")
    parser.add_argument("--n-permutations", type=int, default=1000,
                        help="Number of permutations to run (default: 1000).")
    args = parser.parse_args()

    # Set global seed for reproducibility
    seed = get_seed()
    set_global_seed(seed)
    print(f"Using random seed: {seed}")

    # Load data
    print("Loading features...")
    features_df = load_features()

    print("Loading split indices...")
    split_indices = load_split_indices()

    # Prepare test data
    print("Preparing test set data...")
    X_test, y_test = prepare_test_data(features_df, split_indices)
    print(f"Test set size: {len(y_test)}")

    if len(y_test) == 0:
        raise ValueError("Test set is empty. Cannot run permutation test.")

    # Run permutation test
    print(f"Running permutation test with {args.n_permutations} shuffles...")
    results = run_permutation_test(
        X_test, y_test,
        n_permutations=args.n_permutations,
        random_state=seed
    )

    # Save results
    output_path = get_path("permutation_results")
    save_results(results, output_path)

    # Print summary
    print("\n--- Permutation Test Results ---")
    print(f"Observed R²: {results['observed_r2']:.4f}")
    print(f"P-value: {results['p_value']:.4f}")
    print(f"Significant at p < 0.05: {results['significant_at_005']}")
    print(f"Significant at p < 0.01: {results['significant_at_001']}")


if __name__ == "__main__":
    main()
