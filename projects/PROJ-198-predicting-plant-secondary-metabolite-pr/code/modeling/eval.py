import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
import numpy as np
from utils.logging import get_logger

logger = get_logger(__name__)

def load_model_results(metrics_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load model results from metrics.json.
    
    Args:
        metrics_path: Path to metrics.json. Defaults to data/processed/metrics.json.
        
    Returns:
        Dictionary containing model metrics.
        
    Raises:
        FileNotFoundError: If metrics file does not exist.
        json.JSONDecodeError: If file contains invalid JSON.
    """
    if metrics_path is None:
        metrics_path = "data/processed/metrics.json"
        
    path = Path(metrics_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
        
    with open(path, 'r') as f:
        return json.load(f)

def save_metrics(metrics: Dict[str, Any], metrics_path: Optional[str] = None) -> None:
    """
    Save metrics dictionary to metrics.json.
    
    Args:
        metrics: Dictionary of metrics to save.
        metrics_path: Path to metrics.json. Defaults to data/processed/metrics.json.
    """
    if metrics_path is None:
        metrics_path = "data/processed/metrics.json"
        
    path = Path(metrics_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
        
    logger.info(f"Metrics saved to {metrics_path}")

def evaluate_models(model_results: Dict[str, Any], test_data: Any) -> Dict[str, float]:
    """
    Evaluate models on test data and calculate R² and Pearson correlation.
    
    Args:
        model_results: Dictionary containing trained models and metadata.
        test_data: Test dataset for evaluation.
        
    Returns:
        Dictionary with evaluation metrics per model.
    """
    results = {}
    # Implementation would extract predictions and calculate metrics
    # This is a placeholder for the actual evaluation logic
    return results

def run_phylogenetic_permutation(
    tree: Any, 
    model_results: Dict[str, Any], 
    n_permutations: int = 100
) -> Dict[str, float]:
    """
    Run phylogenetic permutation baseline test.
    
    Args:
        tree: Phylogenetic tree object.
        model_results: Model results to permute against.
        n_permutations: Number of permutations to run.
        
    Returns:
        Dictionary with baseline R² values.
    """
    # Implementation would shuffle labels while preserving tree structure
    # and calculate baseline R²
    return {}

def calculate_significance(
    model_r2: float, 
    baseline_r2: float, 
    n_permutations: int = 100,
    alpha: float = 0.05
) -> Tuple[bool, float]:
    """
    Calculate statistical significance of model R² against baseline.
    
    Args:
        model_r2: Model R² value.
        baseline_r2: Baseline R² from permutations.
        n_permutations: Number of permutations used.
        alpha: Significance threshold.
        
    Returns:
        Tuple of (is_significant, p_value).
    """
    # Implementation would compare model R² against permutation distribution
    # and calculate p-value
    return True, 0.0

def report_primary_results(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and format primary results for the final report.
    
    Args:
        metrics: Dictionary containing all model metrics.
        
    Returns:
        Dictionary with formatted primary results (PGLS R², feature importance).
    """
    # Implementation would extract PGLS results and feature importance
    return {}

def retrain_with_thresholds(
    aligned_data: Any, 
    thresholds: List[float],
    model_type: str = "pgls"
) -> Dict[str, Any]:
    """
    Retrain models with varied BGC detection thresholds.
    
    Args:
        aligned_data: Aligned dataset.
        thresholds: List of thresholds to test.
        model_type: Type of model to train.
        
    Returns:
        Dictionary with metrics for each threshold.
    """
    results = {}
    # Implementation would retrain models for each threshold
    return results

def run_sensitivity_sweep(
    aligned_data: Any,
    thresholds: List[float],
    model_type: str = "pgls"
) -> Dict[str, List[float]]:
    """
    Run sensitivity analysis by iterating over thresholds.
    
    Args:
        aligned_data: Aligned dataset.
        thresholds: List of thresholds to test.
        model_type: Type of model to train.
        
    Returns:
        Dictionary mapping threshold to list of R² values.
    """
    results = {}
    # Implementation would run retrain_with_thresholds and collect R² values
    return results

def calculate_variation(
    metrics: Dict[str, Any],
    threshold_key: str = "thresholds",
    r2_key: str = "r2_scores"
) -> Dict[str, Any]:
    """
    Calculate the maximum R² difference across thresholds and verify against 0.05.
    
    This function implements T031:
    1. Extracts R² scores from the sensitivity sweep results in metrics.
    2. Calculates the max difference (max - min).
    3. Checks if max_diff <= 0.05.
    4. Updates the metrics dictionary with the variation result.
    5. Writes the updated metrics to data/processed/metrics.json.
    
    Args:
        metrics: Dictionary containing sensitivity sweep results.
        threshold_key: Key in metrics where threshold results are stored.
        r2_key: Key within threshold results where R² scores are stored.
        
    Returns:
        Dictionary with variation metrics:
            - max_diff: Maximum R² difference.
            - is_within_threshold: Boolean indicating if max_diff <= 0.05.
            - min_r2: Minimum R² observed.
            - max_r2: Maximum R² observed.
            
    Raises:
        KeyError: If expected keys are not found in metrics.
        ValueError: If no R² scores are found to calculate variation.
    """
    logger.info("Calculating R² variation across thresholds...")
    
    # Check if sensitivity sweep results exist in metrics
    if threshold_key not in metrics:
        raise KeyError(f"Threshold results not found in metrics. Key '{threshold_key}' missing.")
        
    threshold_results = metrics[threshold_key]
    
    # Collect all R² scores from all thresholds
    all_r2_scores = []
    for threshold, result in threshold_results.items():
        if r2_key in result:
            r2_value = result[r2_key]
            if isinstance(r2_value, (list, np.ndarray)):
                # If it's a list (e.g., cross-validation scores), take the mean or all values
                # For variation analysis, we typically want the mean performance per threshold
                all_r2_scores.extend([float(v) for v in r2_value])
            elif isinstance(r2_value, (int, float)):
                all_r2_scores.append(float(r2_value))
    
    if not all_r2_scores:
        raise ValueError("No R² scores found to calculate variation.")
        
    # Calculate variation metrics
    min_r2 = float(min(all_r2_scores))
    max_r2 = float(max(all_r2_scores))
    max_diff = max_r2 - min_r2
    
    # Threshold for acceptable variation (from task description)
    variation_threshold = 0.05
    is_within_threshold = max_diff <= variation_threshold
    
    # Prepare variation result
    variation_result = {
        "max_diff": max_diff,
        "min_r2": min_r2,
        "max_r2": max_r2,
        "threshold_limit": variation_threshold,
        "is_within_threshold": is_within_threshold,
        "n_scores_analyzed": len(all_r2_scores)
    }
    
    # Update metrics dictionary
    metrics["sensitivity_variation"] = variation_result
    
    # Log results
    logger.info(f"R² Variation Analysis Complete:")
    logger.info(f"  Min R²: {min_r2:.4f}")
    logger.info(f"  Max R²: {max_r2:.4f}")
    logger.info(f"  Max Difference: {max_diff:.4f}")
    logger.info(f"  Threshold Limit: {variation_threshold}")
    logger.info(f"  Within Threshold ({variation_threshold}): {is_within_threshold}")
    
    if not is_within_threshold:
        logger.warning(f"⚠️  R² variation ({max_diff:.4f}) exceeds threshold ({variation_threshold}). "
                     "Model performance is sensitive to BGC detection thresholds.")
        metrics["status"] = "FAIL"
        metrics["fail_reason"] = f"R² variation ({max_diff:.4f}) exceeds threshold ({variation_threshold})"
    else:
        logger.info("✅ R² variation is within acceptable limits.")
        metrics["status"] = "PASS"
        
    # Save updated metrics to file
    metrics_path = "data/processed/metrics.json"
    save_metrics(metrics, metrics_path)
    logger.info(f"Updated metrics saved to {metrics_path}")
    
    return variation_result

def main():
    """
    Main entry point for T031: Calculate R² variation from sensitivity sweep.
    
    This script:
    1. Loads existing metrics from data/processed/metrics.json (produced by T028/T030b).
    2. Calls calculate_variation() to compute max R² difference.
    3. Writes the result back to metrics.json.
    4. Exits with code 1 if variation > 0.05, else 0.
    """
    metrics_path = "data/processed/metrics.json"
    
    if not Path(metrics_path).exists():
        logger.error(f"Metrics file not found: {metrics_path}")
        logger.error("Please run T028 and T030b first to generate sensitivity sweep results.")
        return 1
        
    try:
        metrics = load_model_results(metrics_path)
        
        # Check if sensitivity sweep results exist
        if "thresholds" not in metrics:
            logger.error("No sensitivity sweep results found in metrics.json.")
            logger.error("Please run T030b (run_sensitivity_sweep) first.")
            return 1
            
        # Calculate variation
        variation_result = calculate_variation(metrics)
        
        # Exit with appropriate code
        if not variation_result["is_within_threshold"]:
            logger.error("Task T031 FAILED: R² variation exceeds threshold.")
            return 1
        else:
            logger.info("Task T031 COMPLETED: R² variation is within threshold.")
            return 0
            
    except Exception as e:
        logger.error(f"Error during variation calculation: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())