"""
Validation module for statistical tests and sensitivity analysis.

Implements:
- Permutation tests (label shuffling) to establish null distribution
- Paired t-tests against shuffled baselines
- Sensitivity analysis for valence binarization thresholds
"""
import os
import logging
import pickle
import gc
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union
import numpy as np
from scipy import stats
from sklearn.metrics import accuracy_score
import pandas as pd

# Import from existing project modules
from config import CONFIG
from train import load_preprocessed_data, run_nested_loso, save_model_bundle
from preprocessing import check_skewed_valence, preprocess_all_subjects
from importance import load_features_and_labels

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CONFIG['paths']['logs_dir'] / 'validate.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_permutation_test(
    observed_accuracy: float,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_permutations: int = 1000,
    random_state: Optional[int] = None
) -> Tuple[float, float, np.ndarray]:
    """
    Perform a permutation test comparing observed accuracy against a label-shuffled baseline.
    
    Args:
        observed_accuracy: The accuracy obtained from the real model.
        y_true: True labels from the test set.
        y_pred: Predicted labels from the real model.
        n_permutations: Number of permutations to run.
        random_state: Random seed for reproducibility.
        
    Returns:
        p_value: Probability of observing accuracy >= observed_accuracy under null.
        effect_size: Cohen's d effect size.
        null_distribution: Array of accuracies from shuffled labels.
    """
    if random_state is not None:
        np.random.seed(random_state)
        
    n_samples = len(y_true)
    null_accuracies = []
    
    logger.info(f"Running permutation test with {n_permutations} shuffles...")
    
    for i in range(n_permutations):
        # Shuffle labels
        y_shuffled = np.random.permutation(y_true)
        # Calculate accuracy with shuffled labels
        acc = accuracy_score(y_shuffled, y_pred)
        null_accuracies.append(acc)
        
        if (i + 1) % 100 == 0:
            logger.info(f"  Completed {i + 1}/{n_permutations} permutations")
    
    null_distribution = np.array(null_accuracies)
    
    # Calculate p-value (one-tailed: probability of getting >= observed accuracy)
    p_value = np.mean(null_distribution >= observed_accuracy)
    
    # Calculate Cohen's d
    mean_null = np.mean(null_distribution)
    std_null = np.std(null_distribution)
    if std_null > 0:
        effect_size = (observed_accuracy - mean_null) / std_null
    else:
        effect_size = 0.0
        
    logger.info(f"Permutation test complete: p={p_value:.4f}, Cohen's d={effect_size:.4f}")
    logger.info(f"Null distribution: mean={mean_null:.4f}, std={std_null:.4f}")
    
    return p_value, effect_size, null_distribution

def run_paired_ttest(
    observed_accuracies: List[float],
    shuffled_accuracies: List[float]
) -> Tuple[float, float]:
    """
    Perform a paired t-test comparing observed accuracies against shuffled baseline.
    
    Args:
        observed_accuracies: List of accuracies from real model (e.g., per fold).
        shuffled_accuracies: List of accuracies from shuffled labels (same length).
        
    Returns:
        t_statistic: T-statistic from the test.
        p_value: Two-tailed p-value.
    """
    if len(observed_accuracies) != len(shuffled_accuracies):
        raise ValueError("Accuracies lists must be of equal length for paired t-test")
        
    t_stat, p_val = stats.ttest_rel(observed_accuracies, shuffled_accuracies)
    
    logger.info(f"Paired t-test: t={t_stat:.4f}, p={p_val:.4f}")
    return t_stat, p_val

def calculate_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    
    Args:
        group1: First group of values.
        group2: Second group of values.
        
    Returns:
        Cohen's d value.
    """
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1), np.std(group2)
    
    # Pooled standard deviation
    n1, n2 = len(group1), len(group2)
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
        
    return (mean1 - mean2) / pooled_std

def run_sensitivity_analysis(
    base_accuracy: float,
    thresholds: List[float],
    y_scores: np.ndarray,
    y_true: np.ndarray
) -> Dict[str, Any]:
    """
    Run sensitivity analysis by varying the valence binarization threshold.
    
    Args:
        base_accuracy: Accuracy at the default threshold (5.0).
        thresholds: List of thresholds to test (centered around 5.0).
        y_scores: Continuous valence scores.
        y_true: True binary labels (for reference).
        
    Returns:
        Dictionary containing sensitivity results.
    """
    logger.info(f"Running sensitivity analysis over {len(thresholds)} thresholds...")
    
    results = {
        'thresholds': thresholds,
        'accuracies': [],
        'variations': []
    }
    
    for thresh in thresholds:
        # Binarize based on current threshold
        y_pred_thresh = (y_scores >= thresh).astype(int)
        
        # Calculate accuracy against true labels
        acc = accuracy_score(y_true, y_pred_thresh)
        results['accuracies'].append(acc)
        
        # Calculate variation from base accuracy
        variation = abs(acc - base_accuracy)
        results['variations'].append(variation)
        
        logger.info(f"  Threshold {thresh:.2f}: accuracy={acc:.4f}, variation={variation:.4f}")
    
    # Check if all variations are within acceptable range (< 3%)
    max_variation = max(results['variations'])
    is_stable = max_variation < 0.03
    
    results['max_variation'] = max_variation
    results['is_stable'] = is_stable
    
    logger.info(f"Sensitivity analysis complete: max_variation={max_variation:.4f}, stable={is_stable}")
    
    return results

def validate_pipeline(
    model_bundle_path: Optional[Path] = None,
    n_permutations: int = 1000,
    threshold_range: Tuple[float, float] = (4.9, 5.1),
    n_thresholds: int = 11
) -> Dict[str, Any]:
    """
    Main validation function that runs all statistical tests and sensitivity analysis.
    
    Args:
        model_bundle_path: Path to the trained model bundle.
        n_permutations: Number of permutations for the test.
        threshold_range: Range of thresholds for sensitivity analysis (min, max).
        n_thresholds: Number of thresholds to test.
        
    Returns:
        Dictionary containing all validation results.
    """
    logger.info("Starting validation pipeline...")
    
    # Load preprocessed data
    data_path = CONFIG['paths']['processed_data_dir']
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}")
        
    subjects_data = load_preprocessed_data(data_path)
    
    if not subjects_data:
        raise ValueError("No subject data found for validation")
    
    # Aggregate all data for validation
    all_y_true = []
    all_y_pred = []
    all_y_scores = []
    all_y_continuous = []
    
    for subject_id, subject_data in subjects_data.items():
        if 'y_true' in subject_data and 'y_pred' in subject_data:
            all_y_true.extend(subject_data['y_true'])
            all_y_pred.extend(subject_data['y_pred'])
            if 'y_scores' in subject_data:
                all_y_scores.extend(subject_data['y_scores'])
            if 'y_continuous' in subject_data:
                all_y_continuous.extend(subject_data['y_continuous'])
    
    if not all_y_true:
        raise ValueError("No validation data available")
    
    all_y_true = np.array(all_y_true)
    all_y_pred = np.array(all_y_pred)
    all_y_scores = np.array(all_y_scores) if all_y_scores else None
    all_y_continuous = np.array(all_y_continuous) if all_y_continuous else None
    
    # Calculate observed accuracy
    observed_accuracy = accuracy_score(all_y_true, all_y_pred)
    logger.info(f"Observed accuracy: {observed_accuracy:.4f}")
    
    # Run permutation test
    p_value, effect_size, null_distribution = run_permutation_test(
        observed_accuracy,
        all_y_true,
        all_y_pred,
        n_permutations=n_permutations
    )
    
    # Generate shuffled baseline accuracies for t-test
    shuffled_accuracies = []
    for _ in range(len(subjects_data)):  # One per subject/fold
        y_shuffled = np.random.permutation(all_y_true)
        acc = accuracy_score(y_shuffled, all_y_pred)
        shuffled_accuracies.append(acc)
    
    # Run paired t-test
    t_stat, t_p_value = run_paired_ttest(
        [observed_accuracy] * len(shuffled_accuracies),
        shuffled_accuracies
    )
    
    # Run sensitivity analysis
    sensitivity_results = None
    if all_y_continuous is not None and all_y_scores is not None:
        # Generate thresholds centered around 5.0
        threshold_step = (threshold_range[1] - threshold_range[0]) / (n_thresholds - 1)
        thresholds = [threshold_range[0] + i * threshold_step for i in range(n_thresholds)]
        
        sensitivity_results = run_sensitivity_analysis(
            observed_accuracy,
            thresholds,
            all_y_continuous,
            all_y_true
        )
    
    # Compile results
    validation_results = {
        'observed_accuracy': observed_accuracy,
        'permutation_test': {
            'p_value': p_value,
            'effect_size': effect_size,
            'null_distribution': null_distribution.tolist(),
            'n_permutations': n_permutations,
            'significant': p_value < 0.05
        },
        'paired_ttest': {
            't_statistic': t_stat,
            'p_value': t_p_value,
            'significant': t_p_value < 0.05
        },
        'sensitivity_analysis': sensitivity_results,
        'summary': {
            'p_value_permutation': p_value,
            'p_value_ttest': t_p_value,
            'effect_size_cohens_d': effect_size,
            'is_significant': p_value < 0.05 and t_p_value < 0.05,
            'sensitivity_stable': sensitivity_results['is_stable'] if sensitivity_results else None
        }
    }
    
    # Save results
    output_path = CONFIG['paths']['results_dir'] / 'validation_results.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert numpy arrays to lists for JSON serialization
    import json
    with open(output_path, 'w') as f:
        json.dump(validation_results, f, indent=2, default=str)
    
    logger.info(f"Validation results saved to {output_path}")
    
    return validation_results

def main():
    """Main entry point for validation script."""
    logger.info("Starting validation script...")
    
    try:
        # Run validation pipeline
        results = validate_pipeline(
            n_permutations=1000,
            threshold_range=(4.9, 5.1),
            n_thresholds=11
        )
        
        # Print summary
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        print(f"Observed Accuracy: {results['observed_accuracy']:.4f}")
        print(f"Permutation Test p-value: {results['permutation_test']['p_value']:.4f}")
        print(f"Permutation Test Significant: {results['permutation_test']['significant']}")
        print(f"Cohen's d Effect Size: {results['permutation_test']['effect_size']:.4f}")
        print(f"Paired T-test p-value: {results['paired_ttest']['p_value']:.4f}")
        print(f"Paired T-test Significant: {results['paired_ttest']['significant']}")
        
        if results['sensitivity_analysis']:
            print(f"Sensitivity Analysis Max Variation: {results['sensitivity_analysis']['max_variation']:.4f}")
            print(f"Sensitivity Analysis Stable (<3%): {results['sensitivity_analysis']['is_stable']}")
        
        print("="*60)
        
        # Exit with appropriate code
        if results['summary']['is_significant']:
            logger.info("Validation PASSED: Results are statistically significant.")
            return 0
        else:
            logger.warning("Validation WARNING: Results are not statistically significant.")
            return 1
            
    except Exception as e:
        logger.error(f"Validation failed with error: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()