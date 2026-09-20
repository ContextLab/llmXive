"""
Stratified Permutation Module for Avian Foraging Behavior Analysis.

This module provides a reusable implementation of stratified permutation testing,
specifically designed to preserve species-level structure when evaluating model
performance. It ensures that label permutations only occur within species groups,
preventing accidental leakage of information across species boundaries.
"""

import numpy as np
from typing import List, Optional, Tuple, Callable, Union
from pathlib import Path
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def stratified_permutation(
    labels: np.ndarray,
    stratification_key: np.ndarray,
    n_permutations: int = 1000,
    random_state: Optional[int] = None
) -> np.ndarray:
    """
    Perform stratified permutation of labels, ensuring permutations only occur
    within groups defined by the stratification key.

    This function is critical for maintaining the integrity of species-level
    structure during permutation tests. By restricting permutations to within
    species groups, we prevent artificial inflation or deflation of model
    performance metrics that could occur if labels were shuffled across species.

    Parameters
    ----------
    labels : np.ndarray
        1D array of labels to be permuted. Shape: (n_samples,)
    stratification_key : np.ndarray
        1D array of group identifiers (species IDs). Shape: (n_samples,)
    n_permutations : int
        Number of permutation iterations to perform. Default: 1000
    random_state : int, optional
        Random seed for reproducibility. If None, uses global numpy random state.

    Returns
    -------
    np.ndarray
        2D array of permuted labels. Shape: (n_permutations, n_samples)
        Each row represents one permutation of the original labels.

    Raises
    ------
    ValueError
        If input arrays have mismatched lengths or are not 1D.
    """
    # Input validation
    if labels.ndim != 1:
        raise ValueError(f"labels must be 1D array, got {labels.ndim}D")
    if stratification_key.ndim != 1:
        raise ValueError(f"stratification_key must be 1D array, got {stratification_key.ndim}D")
    if len(labels) != len(stratification_key):
        raise ValueError(f"labels and stratification_key must have same length: "
                       f"{len(labels)} vs {len(stratification_key)}")

    # Set random state
    rng = np.random.default_rng(random_state)
    n_samples = len(labels)
    n_unique_groups = len(np.unique(stratification_key))

    logger.info(f"Starting stratified permutation with {n_permutations} iterations")
    logger.info(f"Total samples: {n_samples}, Unique groups: {n_unique_groups}")

    # Store permuted labels
    permuted_labels = np.zeros((n_permutations, n_samples), dtype=labels.dtype)

    # Get unique groups and their indices
    unique_groups = np.unique(stratification_key)
    group_indices = {group: np.where(stratification_key == group)[0] 
                   for group in unique_groups}

    # Perform permutations
    for i in range(n_permutations):
        # Create a copy of original labels
        current_permutation = labels.copy()
        
        # Shuffle labels within each group
        for group in unique_groups:
            group_idx = group_indices[group]
            if len(group_idx) > 1:  # Only shuffle if group has more than 1 sample
                # Get labels for this group
                group_labels = current_permutation[group_idx]
                # Shuffle within the group
                shuffled_labels = rng.permutation(group_labels)
                # Assign back
                current_permutation[group_idx] = shuffled_labels
        
        permuted_labels[i] = current_permutation

        if (i + 1) % 100 == 0:
            logger.info(f"Completed {i + 1}/{n_permutations} permutations")

    logger.info(f"Stratified permutation completed successfully")
    return permuted_labels


def calculate_null_distribution(
    observed_metric: float,
    permuted_labels: np.ndarray,
    X: np.ndarray,
    metric_function: Callable,
    model_function: Callable,
    stratification_key: np.ndarray,
    n_permutations: int,
    random_state: Optional[int] = None
) -> Tuple[np.ndarray, float]:
    """
    Calculate the null distribution of a metric under stratified permutation.

    This function computes the metric for each permutation of labels and returns
    the distribution of values that would be expected if there were no true
    relationship between features and labels (within species groups).

    Parameters
    ----------
    observed_metric : float
        The metric value calculated on the original, unpermuted labels.
    permuted_labels : np.ndarray
        2D array of permuted labels from stratified_permutation().
    X : np.ndarray
        Feature matrix. Shape: (n_samples, n_features)
    metric_function : callable
        Function that calculates the metric given true labels and predicted labels.
        Signature: metric_function(y_true, y_pred) -> float
    model_function : callable
        Function that trains a model and returns predictions.
        Signature: model_function(X_train, y_train, X_test) -> y_pred
    stratification_key : np.ndarray
        1D array of group identifiers for stratification.
    n_permutations : int
        Number of permutations to evaluate.
    random_state : int, optional
        Random seed for reproducibility.

    Returns
    -------
    Tuple[np.ndarray, float]
        - Array of metric values for each permutation
        - P-value: proportion of permuted metrics >= observed metric
    """
    logger.info(f"Calculating null distribution with {n_permutations} permutations")

    null_metrics = np.zeros(n_permutations)
    
    # Assuming X is already split into train/test appropriately
    # or the model_function handles the split internally
    # For this implementation, we assume model_function handles the data split
    
    for i in range(n_permutations):
        y_permuted = permuted_labels[i]
        
        # Train model with permuted labels and get predictions
        # Note: In a real implementation, this would involve proper train/test splitting
        # For now, we assume model_function handles the cross-validation internally
        try:
            y_pred = model_function(X, y_permuted)
            metric_val = metric_function(y_permuted, y_pred)
            null_metrics[i] = metric_val
        except Exception as e:
            logger.warning(f"Permutation {i} failed: {e}")
            null_metrics[i] = np.nan

    # Remove NaN values
    null_metrics = null_metrics[~np.isnan(null_metrics)]
    
    if len(null_metrics) == 0:
        logger.error("No valid null metrics could be computed")
        return np.array([]), 1.0

    # Calculate p-value (one-tailed test: is observed significantly better than null?)
    # P-value = proportion of null metrics >= observed metric
    p_value = np.mean(null_metrics >= observed_metric)
    
    logger.info(f"Null distribution computed: mean={np.mean(null_metrics):.4f}, "
               f"std={np.std(null_metrics):.4f}, p-value={p_value:.4f}")
    
    return null_metrics, p_value


def run_stratified_permutation_test(
    X: np.ndarray,
    y: np.ndarray,
    stratification_key: np.ndarray,
    model_function: Callable,
    metric_function: Callable,
    n_permutations: int = 1000,
    random_state: Optional[int] = None,
    output_path: Optional[Union[str, Path]] = None
) -> dict:
    """
    Run a complete stratified permutation test.

    This is the main entry point for conducting a stratified permutation test.
    It orchestrates the permutation of labels, model training, metric calculation,
    and p-value computation while preserving species-level structure.

    Parameters
    ----------
    X : np.ndarray
        Feature matrix. Shape: (n_samples, n_features)
    y : np.ndarray
        True labels. Shape: (n_samples,)
    stratification_key : np.ndarray
        1D array of group identifiers (species IDs). Shape: (n_samples,)
    model_function : callable
        Function that trains a model and returns predictions.
        Signature: model_function(X, y) -> y_pred (or similar)
    metric_function : callable
        Function that calculates the metric.
        Signature: metric_function(y_true, y_pred) -> float
    n_permutations : int
        Number of permutations to perform. Default: 1000
    random_state : int, optional
        Random seed for reproducibility.
    output_path : str or Path, optional
        Path to save results as JSON. If None, results are not saved.

    Returns
    -------
    dict
        Dictionary containing:
        - 'observed_metric': Metric on original labels
        - 'null_distribution': Array of metrics from permuted labels
        - 'p_value': Proportion of null metrics >= observed metric
        - 'n_permutations': Number of permutations performed
        - 'random_state': Random seed used
        - 'n_samples': Number of samples
        - 'n_unique_groups': Number of unique groups in stratification_key
    """
    logger.info("=" * 60)
    logger.info("Starting Stratified Permutation Test")
    logger.info("=" * 60)
    logger.info(f"Samples: {len(X)}, Features: {X.shape[1] if len(X.shape) > 1 else 1}")
    logger.info(f"Unique groups: {len(np.unique(stratification_key))}")
    logger.info(f"Permutations: {n_permutations}")

    # Set random state
    rng = np.random.default_rng(random_state)
    if random_state is not None:
        logger.info(f"Random state set to: {random_state}")

    # Calculate observed metric
    # Note: In a real implementation, this would involve proper train/test splitting
    # For now, we assume model_function handles the cross-validation internally
    try:
        y_pred_observed = model_function(X, y)
        observed_metric = metric_function(y, y_pred_observed)
        logger.info(f"Observed metric: {observed_metric:.4f}")
    except Exception as e:
        logger.error(f"Failed to calculate observed metric: {e}")
        raise

    # Perform stratified permutation
    permuted_labels = stratified_permutation(
        y, stratification_key, n_permutations, random_state
    )

    # Calculate null distribution
    null_metrics = np.zeros(n_permutations)
    for i in range(n_permutations):
        try:
            y_pred_perm = model_function(X, permuted_labels[i])
            null_metrics[i] = metric_function(permuted_labels[i], y_pred_perm)
        except Exception as e:
            logger.warning(f"Permutation {i} failed: {e}")
            null_metrics[i] = np.nan

    # Remove NaN values
    valid_mask = ~np.isnan(null_metrics)
    null_metrics_valid = null_metrics[valid_mask]
    n_valid_permutations = len(null_metrics_valid)

    if n_valid_permutations == 0:
        logger.error("No valid permutations could be computed")
        raise RuntimeError("No valid permutations could be computed")

    # Calculate p-value
    p_value = np.mean(null_metrics_valid >= observed_metric)

    # Prepare results
    results = {
        'observed_metric': float(observed_metric),
        'null_distribution': null_metrics_valid.tolist(),
        'p_value': float(p_value),
        'n_permutations': n_valid_permutations,
        'requested_permutations': n_permutations,
        'random_state': random_state,
        'n_samples': int(len(X)),
        'n_unique_groups': int(len(np.unique(stratification_key))),
        'metric_name': metric_function.__name__ if hasattr(metric_function, '__name__') else 'custom_metric'
    }

    # Save results if output path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to: {output_path}")

    logger.info("=" * 60)
    logger.info("Stratified Permutation Test Complete")
    logger.info(f"Observed Metric: {observed_metric:.4f}")
    logger.info(f"P-value: {p_value:.4f}")
    logger.info(f"Significant at α=0.05: {'Yes' if p_value < 0.05 else 'No'}")
    logger.info("=" * 60)

    return results


def validate_stratification(
    stratification_key: np.ndarray,
    min_group_size: int = 2,
    max_group_proportion: float = 0.5
) -> dict:
    """
    Validate the stratification key for appropriate group structure.

    This function checks that the stratification key has suitable properties
    for permutation testing, ensuring there are enough groups and that no
    single group dominates the dataset.

    Parameters
    ----------
    stratification_key : np.ndarray
        1D array of group identifiers.
    min_group_size : int
        Minimum acceptable size for any group. Default: 2
    max_group_proportion : float
        Maximum acceptable proportion of samples in any single group. Default: 0.5

    Returns
    -------
    dict
        Dictionary containing validation results:
        - 'is_valid': bool
        - 'warnings': list of warning messages
        - 'n_groups': number of unique groups
        - 'min_group_size': actual minimum group size
        - 'max_group_size': actual maximum group size
        - 'group_sizes': dict mapping groups to their sizes
    """
    warnings = []
    is_valid = True

    unique_groups, counts = np.unique(stratification_key, return_counts=True)
    n_groups = len(unique_groups)
    total_samples = len(stratification_key)

    group_sizes = dict(zip(unique_groups, counts))
    min_actual_size = min(counts)
    max_actual_size = max(counts)
    max_proportion = max_actual_size / total_samples

    # Check minimum number of groups
    if n_groups < 5:
        warnings.append(f"Only {n_groups} unique groups found. "
                      f"Consider having at least 5 groups for reliable permutation testing.")
        is_valid = False

    # Check minimum group size
    if min_actual_size < min_group_size:
        warnings.append(f"Minimum group size is {min_actual_size}, which is below "
                      f"the recommended minimum of {min_group_size}.")
        is_valid = False

    # Check maximum group proportion
    if max_proportion > max_group_proportion:
        warnings.append(f"Maximum group proportion is {max_proportion:.2%}, which exceeds "
                      f"the recommended maximum of {max_group_proportion:.2%}. "
                      f"This may bias permutation results.")
        is_valid = False

    return {
        'is_valid': is_valid,
        'warnings': warnings,
        'n_groups': n_groups,
        'min_group_size': min_actual_size,
        'max_group_size': max_actual_size,
        'group_sizes': group_sizes,
        'total_samples': total_samples
    }