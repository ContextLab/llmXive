import os
import sys
import logging
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path
from typing import Tuple, Optional, List
import time
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_N_PERMUTATIONS = 5000
DEFAULT_SEED = 42
ALPHA = 0.05

def permuted_t_test(x: np.ndarray, y: np.ndarray, n_permutations: int = DEFAULT_N_PERMUTATIONS, seed: int = DEFAULT_SEED) -> float:
    """
    Perform a non-parametric permutation t-test to assess if the means of two groups (x, y)
    are significantly different.

    Args:
        x: 1D array of values for group 1 (e.g., controls)
        y: 1D array of values for group 2 (e.g., patients)
        n_permutations: Number of permutations to perform
        seed: Random seed for reproducibility

    Returns:
        p_value: The two-tailed p-value from the permutation test
    """
    rng = np.random.default_rng(seed)
    n1, n2 = len(x), len(y)
    n = n1 + n2
    observed_diff = np.mean(x) - np.mean(y)
    observed_abs_diff = abs(observed_diff)

    # Combine data
    combined = np.concatenate([x, y])
    count_extreme = 0

    logger.info(f"Running permutation t-test with {n_permutations} permutations...")
    start_time = time.time()

    for i in range(n_permutations):
        # Shuffle labels implicitly by shuffling data
        shuffled = rng.permutation(combined)
        perm_x = shuffled[:n1]
        perm_y = shuffled[n1:]
        perm_diff = abs(np.mean(perm_x) - np.mean(perm_y))
        if perm_diff >= observed_abs_diff:
            count_extreme += 1

        if (i + 1) % 1000 == 0:
            elapsed = time.time() - start_time
            logger.info(f"Progress: {i+1}/{n_permutations} ({(i+1)/n_permutations*100:.1f}%) - Time: {elapsed:.2f}s")

    p_value = (count_extreme + 1) / (n_permutations + 1)
    logger.info(f"Permutation t-test completed. P-value: {p_value:.4f}")
    return p_value

def permutation_accuracy_test(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_class: type,
    X: np.ndarray,
    n_permutations: int = DEFAULT_N_PERMUTATIONS,
    seed: int = DEFAULT_SEED,
    cv_splits: int = 5
) -> Tuple[float, float, np.ndarray]:
    """
    Perform a permutation test to assess the significance of a classification accuracy.
    This function shuffles the labels (y_true) and re-runs the classification pipeline
    to build a null distribution of accuracies.

    Args:
        y_true: Original binary labels (0 or 1)
        y_pred: Original predictions (used to calculate observed accuracy)
        model_class: The sklearn model class to use (e.g., LogisticRegression)
        X: Feature matrix (n_samples, n_features)
        n_permutations: Number of permutations to perform
        seed: Random seed
        cv_splits: Number of CV folds for the inner loop (if needed)

    Returns:
        observed_accuracy: The accuracy on the real labels
        p_value: The proportion of permuted accuracies >= observed accuracy
        null_distribution: Array of accuracies from permuted labels
    """
    rng = np.random.default_rng(seed)
    n_samples = len(y_true)
    observed_accuracy = np.mean(y_true == y_pred)

    logger.info(f"Starting permutation accuracy test. Observed Accuracy: {observed_accuracy:.4f}")
    logger.info(f"Running {n_permutations} permutations to build null distribution...")

    null_distribution = np.zeros(n_permutations)
    start_time = time.time()

    for i in range(n_permutations):
        # Shuffle labels
        y_shuffled = rng.permutation(y_true)

        # Re-run classification with shuffled labels
        # We use a simple train/test split here for speed, or CV if specified
        # To ensure consistency with the main pipeline, we assume a standard split
        # For this specific test, we'll do a quick 80/20 split to estimate accuracy
        # In a full pipeline, this would call the nested CV function from models.py
        
        # Simple split for permutation speed
        split_idx = int(0.8 * n_samples)
        indices = np.arange(n_samples)
        
        # Shuffle indices for split
        perm_indices = rng.permutation(indices)
        train_idx = perm_indices[:split_idx]
        test_idx = perm_indices[split_idx:]
        
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y_shuffled[train_idx], y_shuffled[test_idx]
        
        if len(np.unique(y_train)) < 2 or len(np.unique(y_test)) < 2:
            # Skip if split is invalid (all one class)
            null_distribution[i] = 0.5 # Chance level
            continue

        model = model_class()
        try:
            model.fit(X_train, y_train)
            y_pred_shuffled = model.predict(X_test)
            null_distribution[i] = np.mean(y_test == y_pred_shuffled)
        except Exception as e:
            logger.warning(f"Permutation {i} failed: {e}. Setting to chance.")
            null_distribution[i] = 0.5

        if (i + 1) % 1000 == 0:
            elapsed = time.time() - start_time
            logger.info(f"Progress: {i+1}/{n_permutations} ({(i+1)/n_permutations*100:.1f}%) - Time: {elapsed:.2f}s")

    # Calculate p-value: proportion of null accuracies >= observed accuracy
    p_value = np.sum(null_distribution >= observed_accuracy) / n_permutations
    
    logger.info(f"Permutation accuracy test completed. P-value: {p_value:.4f}")
    return observed_accuracy, p_value, null_distribution

def run_validation_pipeline(features_path: str, labels_path: str, output_path: str):
    """
    Main entry point for running the validation pipeline.
    Loads features and labels, runs permutation tests, and saves results.

    Args:
        features_path: Path to the features CSV file
        labels_path: Path to the labels CSV file
        output_path: Path to save the results JSON
    """
    logger.info(f"Loading features from {features_path}")
    features_df = pd.read_csv(features_path)
    X = features_df.values

    logger.info(f"Loading labels from {labels_path}")
    labels_df = pd.read_csv(labels_path)
    # Assuming the label column is named 'label' or 'diagnosis'
    label_col = 'label' if 'label' in labels_df.columns else 'diagnosis'
    y_true = labels_df[label_col].values

    if len(X) != len(y_true):
        raise ValueError(f"Feature matrix shape {X.shape} does not match labels length {len(y_true)}")

    # For this specific task, we need to generate predictions first.
    # Since T026/T027/T028 are completed, we assume a model exists or we train one briefly.
    # We will train a Logistic Regression on the full data to get predictions,
    # then run the permutation test against chance.
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_predict

    logger.info("Training model to generate baseline predictions for validation...")
    model = LogisticRegression(max_iter=1000)
    y_pred = cross_val_predict(model, X, y_true, cv=5)

    observed_acc, p_val, null_dist = permutation_accuracy_test(
        y_true=y_true,
        y_pred=y_pred,
        model_class=LogisticRegression,
        X=X,
        n_permutations=DEFAULT_N_PERMUTATIONS,
        seed=DEFAULT_SEED
    )

    results = {
        "observed_accuracy": float(observed_acc),
        "permutation_p_value": float(p_val),
        "n_permutations": DEFAULT_N_PERMUTATIONS,
        "significance_flag": p_val < ALPHA,
        "null_distribution_stats": {
            "mean": float(np.mean(null_dist)),
            "std": float(np.std(null_dist)),
            "min": float(np.min(null_dist)),
            "max": float(np.max(null_dist))
        }
    }

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Validation results saved to {output_path}")
    return results

def main():
    """
    Command line entry point for the validation pipeline.
    """
    # Default paths relative to project root
    base_dir = Path(__file__).resolve().parent.parent.parent
    features_path = base_dir / "data" / "processed" / "features.csv"
    labels_path = base_dir / "data" / "metadata" / "subject_labels.csv"
    output_path = base_dir / "data" / "processed" / "validation_results.json"

    if not features_path.exists():
        logger.error(f"Features file not found: {features_path}")
        sys.exit(1)
    
    if not labels_path.exists():
        logger.error(f"Labels file not found: {labels_path}")
        sys.exit(1)

    results = run_validation_pipeline(
        features_path=str(features_path),
        labels_path=str(labels_path),
        output_path=str(output_path)
    )

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()