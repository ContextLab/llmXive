"""
Permutation testing for model validation on the hold-out set.

Implements FR-005 and SC-003:
- Shuffles phenotype labels n=1000 times on the independent hold-out set
- Calculates model-level p-value based on accuracy/AUC comparison
- Outputs results to artifacts/reports/holdout_metrics.json
"""
import os
import logging
import json
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.base import clone

# Import from sibling modules using the provided API surface
from analysis.validation import load_split_data, load_model
from config import get_path, load_config
from utils.logging import setup_logger

logger = setup_logger(__name__)


def load_holdout_data(split_dir: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Load the hold-out set features and labels.
    
    Returns:
        X_holdout, y_holdout: Features and labels for the hold-out set
        X_train, y_train: Features and labels for the training set (for reference)
    """
    split_data = load_split_data(split_dir)
    
    X_holdout = split_data['X_holdout']
    y_holdout = split_data['y_holdout']
    X_train = split_data['X_train']
    y_train = split_data['y_train']
    
    logger.info(f"Loaded hold-out set: {X_holdout.shape[0]} samples, {X_holdout.shape[1]} features")
    logger.info(f"Loaded training set: {X_train.shape[0]} samples, {X_train.shape[1]} features")
    
    return X_holdout, y_holdout, X_train, y_train


def calculate_metric(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate the performance metric (AUC for binary classification, accuracy otherwise).
    
    Args:
        y_true: True labels
        y_pred: Predicted probabilities or labels
        
    Returns:
        Metric score
    """
    # Try AUC first (requires binary classification)
    try:
        # Check if y_pred contains probabilities (values between 0 and 1, not just 0/1)
        if np.all((y_pred >= 0) & (y_pred <= 1)) and len(np.unique(y_pred)) > 2:
            return roc_auc_score(y_true, y_pred)
        else:
            # If predictions are hard labels, convert to probabilities for AUC if possible
            # or fall back to accuracy
            return accuracy_score(y_true, y_pred)
    except Exception:
        # Fall back to accuracy if AUC fails
        return accuracy_score(y_true, y_pred)


def run_permutation_test(
    model: Any,
    X_holdout: np.ndarray,
    y_holdout: np.ndarray,
    n_permutations: int = 1000,
    random_state: Optional[int] = None,
    metric_name: str = "AUC"
) -> Tuple[float, float, float, np.ndarray]:
    """
    Run permutation testing on the hold-out set.
    
    Args:
        model: Trained model object
        X_holdout: Features for hold-out set
        y_holdout: True labels for hold-out set
        n_permutations: Number of permutations to run
        random_state: Random seed for reproducibility
        metric_name: Name of the metric being tested
        
    Returns:
        Tuple of (observed_metric, permuted_mean, permuted_std, permuted_scores)
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    logger.info(f"Starting permutation test with {n_permutations} iterations...")
    logger.info(f"Using metric: {metric_name}")
    
    # Calculate observed metric on original hold-out set
    y_pred_original = model.predict_proba(X_holdout)[:, 1] if hasattr(model, 'predict_proba') else model.predict(X_holdout)
    observed_metric = calculate_metric(y_holdout, y_pred_original)
    logger.info(f"Observed {metric_name}: {observed_metric:.4f}")
    
    # Run permutations
    permuted_metrics = []
    
    for i in range(n_permutations):
        # Shuffle labels
        y_permuted = y_holdout.copy()
        np.random.shuffle(y_permuted)
        
        # Calculate metric with shuffled labels
        y_pred_permuted = model.predict_proba(X_holdout)[:, 1] if hasattr(model, 'predict_proba') else model.predict(X_holdout)
        permuted_metric = calculate_metric(y_permuted, y_pred_permuted)
        permuted_metrics.append(permuted_metric)
        
        if (i + 1) % 100 == 0:
            logger.info(f"Completed {i + 1}/{n_permutations} permutations")
    
    permuted_metrics = np.array(permuted_metrics)
    permuted_mean = np.mean(permuted_metrics)
    permuted_std = np.std(permuted_metrics)
    
    logger.info(f"Permutation mean: {permuted_mean:.4f}, std: {permuted_std:.4f}")
    
    return observed_metric, permuted_mean, permuted_std, permuted_metrics


def calculate_p_value(observed: float, permuted: np.ndarray, greater_is_better: bool = True) -> float:
    """
    Calculate the p-value from permutation test results.
    
    Args:
        observed: Observed metric value
        permuted: Array of permuted metric values
        greater_is_better: Whether higher metric values are better
        
    Returns:
        p-value
    """
    if greater_is_better:
        # Count how many permuted values are >= observed
        count = np.sum(permuted >= observed)
    else:
        # Count how many permuted values are <= observed
        count = np.sum(permuted <= observed)
    
    # Add 1 to numerator and denominator for conservative estimate
    p_value = (count + 1) / (len(permuted) + 1)
    
    return p_value


def save_holdout_metrics(
    output_path: Path,
    observed_metric: float,
    permuted_mean: float,
    permuted_std: float,
    p_value: float,
    n_permutations: int,
    metric_name: str,
    success_criteria_met: bool
) -> None:
    """
    Save the hold-out metrics and permutation test results.
    
    Args:
        output_path: Path to save the JSON file
        observed_metric: Observed metric value on hold-out set
        permuted_mean: Mean of permuted metrics
        permuted_std: Standard deviation of permuted metrics
        p_value: Calculated p-value
        n_permutations: Number of permutations run
        metric_name: Name of the metric
        success_criteria_met: Whether SC-003 is met (p <= 0.05)
    """
    results = {
        "metric_name": metric_name,
        "observed_metric": float(observed_metric),
        "permuted_mean": float(permuted_mean),
        "permuted_std": float(permuted_std),
        "p_value": float(p_value),
        "n_permutations": n_permutations,
        "success_criteria_met": success_criteria_met,
        "criteria": "p <= 0.05",
        "threshold": 0.05
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved hold-out metrics to {output_path}")


def permutation_test_pipeline(
    model_path: Optional[Path] = None,
    split_dir: Optional[Path] = None,
    output_path: Optional[Path] = None,
    n_permutations: int = 1000,
    random_state: Optional[int] = 42
) -> Dict[str, Any]:
    """
    Run the complete permutation testing pipeline.
    
    Args:
        model_path: Path to the trained model pickle file
        split_dir: Directory containing split data
        output_path: Path to save the results JSON
        n_permutations: Number of permutations to run
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary containing the results
    """
    config = load_config()
    
    # Set default paths if not provided
    if model_path is None:
        model_path = get_path(config, 'model_path')
    if split_dir is None:
        split_dir = get_path(config, 'split_dir')
    if output_path is None:
        output_path = get_path(config, 'holdout_metrics_path')
    
    logger.info(f"Model path: {model_path}")
    logger.info(f"Split directory: {split_dir}")
    logger.info(f"Output path: {output_path}")
    
    # Load the model
    logger.info("Loading trained model...")
    model = load_model(model_path)
    logger.info("Model loaded successfully")
    
    # Load hold-out data
    logger.info("Loading hold-out data...")
    X_holdout, y_holdout, X_train, y_train = load_holdout_data(split_dir)
    
    # Run permutation test
    observed_metric, permuted_mean, permuted_std, permuted_metrics = run_permutation_test(
        model,
        X_holdout,
        y_holdout,
        n_permutations=n_permutations,
        random_state=random_state
    )
    
    # Calculate p-value
    p_value = calculate_p_value(observed_metric, permuted_metrics, greater_is_better=True)
    logger.info(f"Calculated p-value: {p_value:.4f}")
    
    # Check success criteria (SC-003: p <= 0.05)
    success_criteria_met = p_value <= 0.05
    logger.info(f"Success criteria (p <= 0.05) met: {success_criteria_met}")
    
    # Determine metric name
    metric_name = "AUC" if observed_metric > 0.5 else "Accuracy"
    
    # Save results
    save_holdout_metrics(
        output_path,
        observed_metric,
        permuted_mean,
        permuted_std,
        p_value,
        n_permutations,
        metric_name,
        success_criteria_met
    )
    
    results = {
        "observed_metric": observed_metric,
        "permuted_mean": permuted_mean,
        "permuted_std": permuted_std,
        "p_value": p_value,
        "n_permutations": n_permutations,
        "success_criteria_met": success_criteria_met,
        "metric_name": metric_name
    }
    
    return results


def main():
    """Main entry point for permutation testing."""
    logger.info("Starting permutation test pipeline...")
    
    try:
        results = permutation_test_pipeline()
        
        logger.info("Permutation test completed successfully")
        logger.info(f"Observed metric: {results['observed_metric']:.4f}")
        logger.info(f"P-value: {results['p_value']:.4f}")
        logger.info(f"Success criteria met: {results['success_criteria_met']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Permutation test failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
