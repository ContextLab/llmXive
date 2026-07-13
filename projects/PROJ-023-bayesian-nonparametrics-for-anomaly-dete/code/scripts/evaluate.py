"""
Evaluation script for Bayesian Nonparametrics Anomaly Detection project.

This script aggregates metrics from various detection methods, performs
statistical significance testing, and implements fixed thresholding strategies
as mandated by FR-012.

Outputs:
    data/results/evaluation.json: Comprehensive evaluation metrics including
    F1 scores, AUC-ROC, bootstrap confidence intervals, statistical test results,
    and fixed thresholding parameters.
"""

import json
import logging
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import precision_recall_curve, roc_auc_score, f1_score

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.metrics import (
    calculate_precision_recall_f1,
    calculate_auc_roc,
    calculate_bootstrap_ci,
    bonferroni_correction,
    wilcoxon_signed_rank_test
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_and_align_data(
    ground_truth_path: Path,
    prediction_paths: Dict[str, Path]
) -> Dict[str, pd.DataFrame]:
    """
    Load ground truth and prediction files, aligning them by timestamp/index.

    Args:
        ground_truth_path: Path to ground truth CSV with anomaly labels
        prediction_paths: Dictionary mapping method names to their prediction CSV paths

    Returns:
        Dictionary of aligned DataFrames with columns: ['timestamp', 'ground_truth', 'score']
    """
    logger.info(f"Loading ground truth from {ground_truth_path}")
    gt_df = pd.read_csv(ground_truth_path)
    gt_df['timestamp'] = pd.to_datetime(gt_df['timestamp'])
    gt_df = gt_df.sort_values('timestamp').reset_index(drop=True)

    aligned_data = {}
    for method, path in prediction_paths.items():
        logger.info(f"Loading predictions for {method} from {path}")
        pred_df = pd.read_csv(path)
        pred_df['timestamp'] = pd.to_datetime(pred_df['timestamp'])
        pred_df = pred_df.sort_values('timestamp').reset_index(drop=True)

        # Align with ground truth
        merged = pd.merge(
            gt_df[['timestamp', 'anomaly']],
            pred_df[['timestamp', 'score']],
            on='timestamp',
            how='inner'
        )

        if len(merged) != len(gt_df):
            logger.warning(
                f"Mismatch in {method}: {len(merged)} aligned rows vs "
                f"{len(gt_df)} ground truth rows"
            )

        merged = merged.rename(columns={'anomaly': 'ground_truth'})
        aligned_data[method] = merged

    return aligned_data

def calculate_metrics(
    df: pd.DataFrame,
    score_col: str = 'score',
    gt_col: str = 'ground_truth',
    threshold: Optional[float] = None
) -> Dict[str, float]:
    """
    Calculate precision, recall, F1, and AUC-ROC for a single method.

    Args:
        df: DataFrame with ground truth and score columns
        score_col: Name of the score column
        gt_col: Name of the ground truth column
        threshold: Optional fixed threshold for binary classification

    Returns:
        Dictionary with precision, recall, f1, auc_roc, and binary metrics
    """
    y_true = df[gt_col].values.astype(int)
    y_score = df[score_col].values

    # Calculate AUC-ROC (threshold-independent)
    try:
        auc_roc = roc_auc_score(y_true, y_score)
    except ValueError as e:
        logger.warning(f"Could not calculate AUC-ROC: {e}")
        auc_roc = 0.0

    # Calculate binary metrics at given threshold or optimal threshold
    if threshold is None:
        # Use threshold that maximizes F1
        precision, recall, thresholds = precision_recall_curve(y_true, y_score)
        f1_scores = 2 * (precision * recall) / (precision + recall + 1e-10)
        best_idx = np.argmax(f1_scores)
        threshold = thresholds[best_idx] if best_idx < len(thresholds) else 0.5

    y_pred = (y_score >= threshold).astype(int)

    # Calculate precision, recall, F1
    precision, recall, f1, _ = calculate_precision_recall_f1(y_true, y_pred)

    # Calculate confusion matrix components
    tp = int(np.sum((y_pred == 1) & (y_true == 1)))
    fp = int(np.sum((y_pred == 1) & (y_true == 0)))
    fn = int(np.sum((y_pred == 0) & (y_true == 1)))
    tn = int(np.sum((y_pred == 0) & (y_true == 0)))

    return {
        'precision': float(precision),
        'recall': float(recall),
        'f1': float(f1),
        'auc_roc': float(auc_roc),
        'threshold_used': float(threshold),
        'tp': tp,
        'fp': fp,
        'fn': fn,
        'tn': tn
    }

def calculate_bootstrap_ci(
    df: pd.DataFrame,
    score_col: str = 'score',
    gt_col: str = 'ground_truth',
    n_bootstrap: int = 1000,
    ci_level: float = 0.95,
    seed: int = 42
) -> Dict[str, Dict[str, float]]:
    """
    Calculate bootstrap confidence intervals for F1 scores.

    Args:
        df: DataFrame with ground truth and score columns
        score_col: Name of the score column
        gt_col: Name of the ground truth column
        n_bootstrap: Number of bootstrap samples
        ci_level: Confidence level (e.g., 0.95 for 95% CI)
        seed: Random seed for reproducibility

    Returns:
        Dictionary with F1 CI bounds
    """
    np.random.seed(seed)
    y_true = df[gt_col].values.astype(int)
    y_score = df[score_col].values
    n_samples = len(y_true)

    f1_scores = []
    for _ in range(n_bootstrap):
        # Bootstrap sample
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        y_true_boot = y_true[indices]
        y_score_boot = y_score[indices]

        # Calculate F1 at optimal threshold for this bootstrap sample
        precision, recall, thresholds = precision_recall_curve(y_true_boot, y_score_boot)
        f1_boot = 2 * (precision * recall) / (precision + recall + 1e-10)
        best_idx = np.argmax(f1_boot)
        threshold_boot = thresholds[best_idx] if best_idx < len(thresholds) else 0.5

        y_pred_boot = (y_score_boot >= threshold_boot).astype(int)
        _, _, f1_val, _ = calculate_precision_recall_f1(y_true_boot, y_pred_boot)
        f1_scores.append(f1_val)

    lower = np.percentile(f1_scores, (1 - ci_level) / 2 * 100)
    upper = np.percentile(f1_scores, (1 + ci_level) / 2 * 100)
    mean_f1 = np.mean(f1_scores)

    return {
        'mean_f1': float(mean_f1),
        'ci_lower': float(lower),
        'ci_upper': float(upper),
        'ci_level': ci_level,
        'n_bootstrap': n_bootstrap
    }

def wilcoxon_test(
    df_bayesian: pd.DataFrame,
    df_baseline: pd.DataFrame,
    score_col: str = 'score',
    gt_col: str = 'ground_truth'
) -> Dict[str, float]:
    """
    Perform Wilcoxon signed-rank test to compare Bayesian vs baseline methods.

    Args:
        df_bayesian: DataFrame with Bayesian predictions
        df_baseline: DataFrame with baseline predictions
        score_col: Name of the score column
        gt_col: Name of the ground truth column

    Returns:
        Dictionary with test statistic and p-value
    """
    y_true = df_bayesian[gt_col].values.astype(int)

    # Calculate F1 scores for Bayesian and baseline at their optimal thresholds
    def get_f1_series(df):
        y_score = df[score_col].values
        precision, recall, thresholds = precision_recall_curve(y_true, y_score)
        f1_scores = 2 * (precision * recall) / (precision + recall + 1e-10)
        best_idx = np.argmax(f1_scores)
        threshold = thresholds[best_idx] if best_idx < len(thresholds) else 0.5
        y_pred = (y_score >= threshold).astype(int)
        _, _, f1_val, _ = calculate_precision_recall_f1(y_true, y_pred)
        return f1_val

    # For paired test, we need multiple samples. Here we use bootstrap samples
    # to create paired observations
    n_bootstrap = 1000
    np.random.seed(42)
    n_samples = len(y_true)

    bayesian_f1s = []
    baseline_f1s = []

    for _ in range(n_bootstrap):
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        y_true_boot = y_true[indices]
        bayesian_score_boot = df_bayesian[score_col].values[indices]
        baseline_score_boot = df_baseline[score_col].values[indices]

        # Calculate F1 for Bayesian
        precision_b, recall_b, thresholds_b = precision_recall_curve(y_true_boot, bayesian_score_boot)
        f1_b = 2 * (precision_b * recall_b) / (precision_b + recall_b + 1e-10)
        best_idx_b = np.argmax(f1_b)
        threshold_b = thresholds_b[best_idx_b] if best_idx_b < len(thresholds_b) else 0.5
        y_pred_b = (bayesian_score_boot >= threshold_b).astype(int)
        _, _, f1_b_val, _ = calculate_precision_recall_f1(y_true_boot, y_pred_b)
        bayesian_f1s.append(f1_b_val)

        # Calculate F1 for baseline
        precision_base, recall_base, thresholds_base = precision_recall_curve(y_true_boot, baseline_score_boot)
        f1_base = 2 * (precision_base * recall_base) / (precision_base + recall_base + 1e-10)
        best_idx_base = np.argmax(f1_base)
        threshold_base = thresholds_base[best_idx_base] if best_idx_base < len(thresholds_base) else 0.5
        y_pred_base = (baseline_score_boot >= threshold_base).astype(int)
        _, _, f1_base_val, _ = calculate_precision_recall_f1(y_true_boot, y_pred_base)
        baseline_f1s.append(f1_base_val)

    # Perform Wilcoxon signed-rank test
    stat, p_value = wilcoxon_signed_rank_test(bayesian_f1s, baseline_f1s)

    return {
        'statistic': float(stat),
        'p_value': float(p_value),
        'method': 'wilcoxon_signed_rank'
    }

def apply_fixed_threshold_strategy(
    df: pd.DataFrame,
    score_col: str = 'score',
    gt_col: str = 'ground_truth',
    specificity_target: float = 0.95,
    method: str = 'specificity'
) -> Dict[str, Any]:
    """
    Apply fixed thresholding strategy based on target specificity.

    This implements FR-012: fixed thresholding strategy (e.g., % specificity)
    enforced before correlation analysis.

    Args:
        df: DataFrame with ground truth and score columns
        score_col: Name of the score column
        gt_col: Name of the ground truth column
        specificity_target: Target specificity (e.g., 0.95 for 95%)
        method: Thresholding method ('specificity', 'precision', 'f1_opt')

    Returns:
        Dictionary with threshold, achieved metrics, and strategy parameters
    """
    y_true = df[gt_col].values.astype(int)
    y_score = df[score_col].values

    # Sort scores and calculate specificity at each threshold
    sorted_indices = np.argsort(y_score)[::-1]  # Descending
    sorted_scores = y_score[sorted_indices]
    sorted_labels = y_true[sorted_indices]

    n_negative = np.sum(y_true == 0)
    n_positive = np.sum(y_true == 1)

    if n_negative == 0:
        logger.warning("No negative samples found, using default threshold")
        return {
            'threshold': 0.5,
            'achieved_specificity': 1.0,
            'achieved_sensitivity': 0.0,
            'method': method,
            'target_specificity': specificity_target,
            'note': 'No negative samples'
        }

    # Calculate cumulative true negatives (specificity)
    # Specificity = TN / (TN + FP) = TN / n_negative
    # As we lower threshold, we include more positives (lower scores),
    # so TN decreases and FP increases

    thresholds = []
    specificities = []
    sensitivities = []

    for i in range(len(sorted_scores)):
        # Current threshold is the score at position i
        current_threshold = sorted_scores[i]

        # Predictions: all samples with score >= current_threshold are positive
        y_pred = (y_score >= current_threshold).astype(int)

        # Calculate metrics
        tn = np.sum((y_pred == 0) & (y_true == 0))
        fp = np.sum((y_pred == 1) & (y_true == 0))
        tp = np.sum((y_pred == 1) & (y_true == 1))
        fn = np.sum((y_pred == 0) & (y_true == 1))

        specificity = tn / n_negative if n_negative > 0 else 1.0
        sensitivity = tp / n_positive if n_positive > 0 else 0.0

        thresholds.append(current_threshold)
        specificities.append(specificity)
        sensitivities.append(sensitivity)

    # Find threshold that achieves target specificity
    # We want the highest threshold that gives at least target specificity
    valid_indices = [i for i, spec in enumerate(specificities) if spec >= specificity_target]

    if not valid_indices:
        # If no threshold achieves target, use the one closest to target
        closest_idx = np.argmin([abs(s - specificity_target) for s in specificities])
        best_threshold = thresholds[closest_idx]
        achieved_spec = specificities[closest_idx]
        achieved_sens = sensitivities[closest_idx]
        logger.warning(
            f"Could not achieve target specificity {specificity_target}. "
            f"Using closest: {achieved_spec:.4f}"
        )
    else:
        # Use the highest threshold that achieves target specificity
        best_idx = max(valid_indices)
        best_threshold = thresholds[best_idx]
        achieved_spec = specificities[best_idx]
        achieved_sens = sensitivities[best_idx]

    # Calculate additional metrics at this threshold
    y_pred_fixed = (y_score >= best_threshold).astype(int)
    precision, recall, f1, _ = calculate_precision_recall_f1(y_true, y_pred_fixed)

    return {
        'threshold': float(best_threshold),
        'achieved_specificity': float(achieved_spec),
        'achieved_sensitivity': float(achieved_sens),
        'precision': float(precision),
        'recall': float(recall),
        'f1': float(f1),
        'method': method,
        'target_specificity': specificity_target
    }

def evaluate_all_methods(
    aligned_data: Dict[str, pd.DataFrame],
    ground_truth_path: Path,
    prediction_paths: Dict[str, Path],
    fixed_threshold_specificity: float = 0.95
) -> Dict[str, Any]:
    """
    Evaluate all methods with metrics, bootstrap CI, statistical tests,
    and fixed thresholding strategy.

    Args:
        aligned_data: Dictionary of aligned DataFrames
        ground_truth_path: Path to ground truth file
        prediction_paths: Dictionary of prediction file paths
        fixed_threshold_specificity: Target specificity for fixed thresholding

    Returns:
        Comprehensive evaluation results dictionary
    """
    results = {
        'methods': {},
        'statistical_tests': {},
        'fixed_thresholding': {},
        'metadata': {
            'ground_truth_file': str(ground_truth_path),
            'fixed_threshold_specificity_target': fixed_threshold_specificity
        }
    }

    # Evaluate each method
    for method, df in aligned_data.items():
        logger.info(f"Evaluating method: {method}")

        # Standard metrics with optimal threshold
        metrics = calculate_metrics(df)
        results['methods'][method] = {
            'metrics': metrics,
            'bootstrap_ci': calculate_bootstrap_ci(df)
        }

        # Fixed thresholding strategy (FR-012)
        fixed_threshold_result = apply_fixed_threshold_strategy(
            df,
            specificity_target=fixed_threshold_specificity
        )
        results['fixed_thresholding'][method] = fixed_threshold_result

    # Statistical tests: Bayesian vs each baseline
    if 'bayesian' in aligned_data:
        for baseline_method in aligned_data:
            if baseline_method != 'bayesian':
                logger.info(f"Performing statistical test: bayesian vs {baseline_method}")
                test_result = wilcoxon_test(
                    aligned_data['bayesian'],
                    aligned_data[baseline_method]
                )
                test_key = f"bayesian_vs_{baseline_method}"
                results['statistical_tests'][test_key] = test_result

    # Apply Bonferroni correction to p-values
    p_values = [
        test['p_value']
        for test in results['statistical_tests'].values()
        if 'p_value' in test
    ]

    if p_values:
        corrected_results = bonferroni_correction(p_values)
        for i, (key, _) in enumerate(results['statistical_tests'].items()):
            if 'p_value' in results['statistical_tests'][key]:
                results['statistical_tests'][key]['p_value_bonferroni'] = corrected_results[i]

    return results

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save evaluation results to JSON file.

    Args:
        results: Evaluation results dictionary
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for evaluation script."""
    parser = argparse.ArgumentParser(
        description='Evaluate anomaly detection methods'
    )
    parser.add_argument(
        '--ground-truth',
        type=Path,
        default=Path('data/processed/ground_truth.csv'),
        help='Path to ground truth CSV'
    )
    parser.add_argument(
        '--predictions-dir',
        type=Path,
        default=Path('data/results'),
        help='Directory containing prediction CSV files'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/results/evaluation.json'),
        help='Path to output JSON file'
    )
    parser.add_argument(
        '--specificity',
        type=float,
        default=0.95,
        help='Target specificity for fixed thresholding (FR-012)'
    )

    args = parser.parse_args()

    # Define prediction files
    prediction_paths = {
        'shewhart': args.predictions_dir / 'shewhart_predictions.csv',
        'bayesian': args.predictions_dir / 'bayesian_predictions.csv',
        'cusum': args.predictions_dir / 'cusum_predictions.csv',
        'vae': args.predictions_dir / 'vae_predictions.csv'
    }

    # Filter to existing files
    existing_paths = {
        k: v for k, v in prediction_paths.items() if v.exists()
    }

    if not existing_paths:
        logger.error("No prediction files found. Run baseline scripts first.")
        sys.exit(1)

    logger.info(f"Found prediction files: {list(existing_paths.keys())}")

    # Load and align data
    aligned_data = load_and_align_data(args.ground_truth, existing_paths)

    # Evaluate all methods
    results = evaluate_all_methods(
        aligned_data,
        args.ground_truth,
        existing_paths,
        fixed_threshold_specificity=args.specificity
    )

    # Save results
    save_results(results, args.output)

    # Print summary
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    for method, data in results['methods'].items():
        f1 = data['metrics']['f1']
        auc = data['metrics']['auc_roc']
        print(f"{method:12s}: F1={f1:.4f}, AUC-ROC={auc:.4f}")

    print("\nFixed Thresholding (95% Specificity Target):")
    for method, data in results['fixed_thresholding'].items():
        print(f"  {method:12s}: threshold={data['threshold']:.4f}, "
              f"F1={data['f1']:.4f}")

    if results['statistical_tests']:
        print("\nStatistical Tests (Wilcoxon):")
        for test_name, test_data in results['statistical_tests'].items():
            p_val = test_data.get('p_value_bonferroni', test_data.get('p_value', 0))
            print(f"  {test_name}: p-value={p_val:.4f}")

    print("="*60)

if __name__ == '__main__':
    main()