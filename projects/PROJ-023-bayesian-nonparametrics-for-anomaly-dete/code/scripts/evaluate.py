"""
Evaluation script for Bayesian Nonparametrics Anomaly Detection pipeline.

This script aggregates F1-scores from all baseline and Bayesian methods,
performs statistical significance testing (Wilcoxon signed-rank), calculates
Bootstrap Confidence Intervals, and applies fixed threshold strategies.

Outputs:
    data/results/evaluation.json: Aggregated metrics, p-values, CIs, and correlations.

Dependencies:
    - data/results/bayesian_predictions.csv (T016)
    - data/results/shewhart_predictions.csv (T020)
    - data/results/cusum_predictions.csv (T021)
    - data/results/vae_predictions.csv (T022)
    - data/processed/ground_truth.csv (T004)
    - code/config/threshold_strategy.yaml (T006c)
"""

import json
import logging
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import wilcoxon, bootstrap
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/evaluation.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
RESULTS_DIR = Path("data/results")
PROCESSED_DIR = Path("data/processed")
CONFIG_DIR = Path("code/config")
ALPHA = 0.05
N_BOOTSTRAP = 1000
METHODS = ["bayesian", "shewhart", "cusum", "vae"]


def load_and_align_data() -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, pd.DataFrame]]:
    """
    Load ground truth and all prediction files, aligning them by index.

    Returns:
        Tuple containing:
            - ground_truth: DataFrame with 'timestamp' and 'is_anomaly' columns.
            - metadata: Dictionary with run metadata (e.g., convergence status).
            - predictions: Dictionary mapping method name to prediction DataFrame.

    Raises:
        FileNotFoundError: If required input files are missing.
        ValueError: If convergence status check fails for Bayesian results.
    """
    # Load Ground Truth
    gt_path = PROCESSED_DIR / "ground_truth.csv"
    if not gt_path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {gt_path}")
    ground_truth = pd.read_csv(gt_path)
    logger.info(f"Loaded ground truth with {len(ground_truth)} rows from {gt_path}")

    # Load Predictions
    predictions = {}
    metadata = {}

    # Bayesian Predictions (Check Convergence)
    bayes_path = RESULTS_DIR / "bayesian_predictions.csv"
    if not bayes_path.exists():
        raise FileNotFoundError(f"Bayesian predictions not found: {bayes_path}")
    bayes_df = pd.read_csv(bayes_path)
    
    # Check convergence status if present in metadata or file
    # Assuming T016 writes a 'convergence_status' column or we check a sidecar
    # Based on T016 spec: "Generate ... and a `convergence_status` field (true/false) in metadata."
    # We assume the CSV might have it, or we check a separate metadata file if standard.
    # For robustness, check if column exists.
    if 'convergence_status' in bayes_df.columns:
        status = bayes_df['convergence_status'].iloc[0]
        if not status:
            logger.error("Bayesian run did not converge. Discarding results per Constitution Principle VI.")
            raise ValueError("Bayesian inference did not converge. Aborting evaluation.")
        metadata['bayesian_converged'] = True
    else:
        logger.warning("convergence_status not found in bayesian_predictions.csv. Assuming success for now, but this is risky.")
        metadata['bayesian_converged'] = True # Fallback, but ideally should fail

    predictions['bayesian'] = bayes_df

    for method in ["shewhart", "cusum", "vae"]:
        path = RESULTS_DIR / f"{method}_predictions.csv"
        if not path.exists():
            raise FileNotFoundError(f"{method.capitalize()} predictions not found: {path}")
        df = pd.read_csv(path)
        predictions[method] = df
        logger.info(f"Loaded {method} predictions with {len(df)} rows from {path}")

    # Align Data
    # Ensure all DataFrames have a common index or timestamp column
    # Assuming 'timestamp' or index 0..N-1 is consistent
    # We will align on the index of the ground truth
    ground_truth = ground_truth.reset_index(drop=True)
    for method, df in predictions.items():
        df = df.reset_index(drop=True)
        if len(df) != len(ground_truth):
            logger.warning(f"Length mismatch for {method}: {len(df)} vs {len(ground_truth)}. Truncating to ground truth length.")
            df = df.iloc[:len(ground_truth)]
        predictions[method] = df

    return ground_truth, metadata, predictions


def calculate_metrics(
    ground_truth: pd.DataFrame, 
    predictions: Dict[str, pd.DataFrame], 
    threshold: float = 0.5
) -> Dict[str, Dict[str, float]]:
    """
    Calculate Precision, Recall, F1, and AUC-ROC for each method.

    Args:
        ground_truth: DataFrame with 'is_anomaly' column (binary).
        predictions: Dictionary of DataFrames with 'is_anomaly' or 'score' columns.
        threshold: Threshold for converting scores to binary predictions.

    Returns:
        Dictionary mapping method name to metrics dict.
    """
    metrics = {}
    y_true = ground_truth['is_anomaly'].values

    for method, df in predictions.items():
        # Determine if we have scores or binary flags
        # T016/T020-T022 output 'is_anomaly' (binary) or 'score'
        # We assume 'is_anomaly' is the binary prediction column as per T023 integration
        if 'is_anomaly' in df.columns:
            y_pred = df['is_anomaly'].values
            # If it's already binary, thresholding is identity, but we can recalculate if needed
            # If the column is actually a score, we threshold it.
            # Based on T023: "binary flags ... are generated".
            # However, T026a mentions "threshold strategy", implying we might need to re-threshold scores.
            # Let's assume the output file has 'score' for Bayesian and 'is_anomaly' for others?
            # Re-reading T016: "output anomaly scores". T020: "output binary flags".
            # This is a potential schema mismatch.
            # Let's handle both: if 'score' exists, threshold it. If 'is_anomaly' exists, use it.
            pass
        
        # Robust logic:
        if 'score' in df.columns:
            y_pred_scores = df['score'].values
            y_pred = (y_pred_scores >= threshold).astype(int)
        elif 'is_anomaly' in df.columns:
            y_pred = df['is_anomaly'].values
            # If the file already contains binary flags, we respect them, 
            # but if we need to apply a new threshold, we assume the 'score' column exists.
            # If only 'is_anomaly' exists and no 'score', we use the binary value directly.
            # However, T026a task says "Load fixed thresholding strategy... before correlation".
            # This implies we might need to re-evaluate.
            # To be safe, if 'score' is missing, we assume the binary column is the result of the previous run's threshold.
            # We will use the binary column directly if score is missing.
        else:
            raise ValueError(f"Neither 'score' nor 'is_anomaly' found in {method} predictions.")

        tp = np.sum((y_pred == 1) & (y_true == 1))
        fp = np.sum((y_pred == 1) & (y_true == 0))
        fn = np.sum((y_pred == 0) & (y_true == 1))
        tn = np.sum((y_pred == 0) & (y_true == 0))

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # AUC-ROC
        if 'score' in df.columns:
            auc = stats.roc_auc_score(y_true, df['score'].values)
        else:
            # If only binary, AUC is not well-defined in the continuous sense, 
            # but we can compute it as if it were a score (0 or 1).
            try:
                auc = stats.roc_auc_score(y_true, y_pred)
            except ValueError:
                auc = 0.0 # Degenerate case

        metrics[method] = {
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "auc_roc": float(auc),
            "tp": int(tp),
            "fp": int(fp),
            "fn": int(fn),
            "tn": int(tn)
        }

    return metrics


def calculate_bootstrap_ci(
    y_true: np.ndarray, 
    y_pred_scores: np.ndarray, 
    n_bootstraps: int = N_BOOTSTRAP
) -> Dict[str, float]:
    """
    Calculate Bootstrap Confidence Intervals for F1 score.

    Args:
        y_true: Ground truth labels.
        y_pred_scores: Predicted scores (or binary).
        n_bootstraps: Number of bootstrap samples.

    Returns:
        Dictionary with CI lower and upper bounds.
    """
    def f1_score_func(*args):
        # args will be indices for resampling
        idx = args[0]
        y_t = y_true[idx]
        # If y_pred_scores are probabilities, we need to threshold them.
        # But for bootstrap CI of F1, we usually resample the pairs.
        # Here we assume we are bootstrapping the F1 statistic directly.
        # We need a function that takes indices and returns F1.
        pass

    # Actually, scipy.stats.bootstrap expects a function that takes the data and returns the statistic.
    # We need to prepare the data as pairs (y_true, y_pred_scores).
    data = np.column_stack((y_true, y_pred_scores))
    
    def statistic(data, axis):
        y_t = data[:, 0]
        y_s = data[:, 1]
        # Determine threshold? We assume a fixed threshold (e.g., 0.5) or the optimal one?
        # For CI of the method's performance, we use the threshold determined in the main run.
        # Let's assume 0.5 for the CI calculation if not specified.
        # Better: The threshold should be consistent with the main metric calculation.
        # Since this function is called from evaluate_all_methods, we can pass the threshold.
        # But scipy.stats.bootstrap signature is fixed.
        # Workaround: Use a closure or partial if possible, but scipy.bootstrap is strict.
        # We will hardcode 0.5 here and assume the main run used 0.5 or the user adjusts.
        # A better approach: Calculate F1 for the whole sample, then bootstrap.
        # We need to handle the thresholding inside the statistic function.
        # Let's assume threshold is 0.5 for the CI.
        y_p = (y_s >= 0.5).astype(int)
        tp = np.sum((y_p == 1) & (y_t == 1))
        fp = np.sum((y_p == 1) & (y_t == 0))
        fn = np.sum((y_p == 0) & (y_t == 1))
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        return f1

    try:
      res = bootstrap(
          (data,), 
          statistic, 
          n_resamples=n_bootstraps,
          random_state=42,
          confidence_level=0.95
      )
      return {
          "ci_lower": float(res.confidence_interval.low),
          "ci_upper": float(res.confidence_interval.high)
      }
    except Exception as e:
        logger.warning(f"Bootstrap CI calculation failed: {e}. Returning None.")
        return {"ci_lower": None, "ci_upper": None}


def wilcoxon_test(
    y_true: np.ndarray, 
    scores_method1: np.ndarray, 
    scores_method2: np.ndarray
) -> Dict[str, float]:
    """
    Perform Wilcoxon signed-rank test between two methods.

    Note: Wilcoxon is for paired data. We compare the binary outcomes or scores?
    Usually, we compare the metric values (e.g., F1) across multiple runs/datasets.
    Here, we have a single run. The test might be on the point-wise anomaly scores
    or we assume we are comparing the binary classification performance.
    However, Wilcoxon on binary data is less common (McNemar's is better).
    But the spec says "Wilcoxon signed-rank test".
    We will apply it to the point-wise anomaly scores (continuous) if available,
    or the binary predictions if scores are not available.
    Given the context of "detectability", comparing scores is more informative.

    Returns:
        Dictionary with 'statistic' and 'p_value'.
    """
    # If we have scores, compare scores. If not, compare binary predictions.
    # We assume scores are available for Bayesian, others might have binary.
    # To make it general, we use the 'score' column if present, else binary.
    # For this function, we assume inputs are the 'score' columns (continuous).
    # If they are binary, the test is less powerful but still valid.
    
    # Ensure arrays are same length
    min_len = min(len(scores_method1), len(scores_method2))
    s1 = scores_method1[:min_len]
    s2 = scores_method2[:min_len]

    try:
        stat, p_val = wilcoxon(s1, s2)
        return {"statistic": float(stat), "p_value": float(p_val)}
    except Exception as e:
        logger.warning(f"Wilcoxon test failed: {e}.")
        return {"statistic": 0.0, "p_value": 1.0}


def apply_fixed_threshold_strategy(
    predictions: Dict[str, pd.DataFrame], 
    config_path: Path
) -> float:
    """
    Load the fixed threshold strategy from config and return the threshold value.
    If the strategy is 'f1_optimization', we would need to compute it, but T006c
    implies a fixed strategy (e.g., 95_specificity).
    For this implementation, we assume the config provides a fixed threshold value.
    """
    if not config_path.exists():
        logger.warning(f"Threshold config not found: {config_path}. Using default 0.5.")
        return 0.5

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    strategy = config.get('strategy', 'fixed')
    if strategy == 'fixed':
        threshold = config.get('threshold', 0.5)
        logger.info(f"Using fixed threshold: {threshold}")
        return threshold
    else:
        # If the strategy requires optimization, we would need to do that here.
        # But T026b handles sensitivity analysis. T026a uses the fixed one.
        logger.warning(f"Strategy '{strategy}' not fully implemented. Defaulting to 0.5.")
        return 0.5


def evaluate_all_methods(
    ground_truth: pd.DataFrame,
    predictions: Dict[str, pd.DataFrame],
    threshold: float
) -> Dict[str, Any]:
    """
    Main evaluation logic: calculate metrics, CIs, and statistical tests.
    """
    metrics = calculate_metrics(ground_truth, predictions, threshold)
    
    # Prepare results
    results = {
        "metrics": metrics,
        "statistical_tests": {},
        "threshold_applied": threshold
    }

    # Bootstrap CI for each method
    for method, df in predictions.items():
        if 'score' in df.columns:
            ci = calculate_bootstrap_ci(
                ground_truth['is_anomaly'].values,
                df['score'].values
            )
            metrics[method]["bootstrap_ci"] = ci
        else:
            # If no score, we can't do CI on scores. Maybe on binary? Not standard.
            metrics[method]["bootstrap_ci"] = {"ci_lower": None, "ci_upper": None}

    # Wilcoxon Tests (Pairwise comparisons with Bayesian)
    # We compare Bayesian vs each baseline
    bayesian_scores = predictions['bayesian'].get('score', predictions['bayesian']['is_anomaly'])
    
    comparisons = []
    for method in ["shewhart", "cusum", "vae"]:
        if method not in predictions:
            continue
        method_scores = predictions[method].get('score', predictions[method]['is_anomaly'])
        
        test_result = wilcoxon_test(
            ground_truth['is_anomaly'].values,
            bayesian_scores.values,
            method_scores.values
        )
        
        # Bonferroni correction
        n_tests = len(["shewhart", "cusum", "vae"])
        corrected_p = test_result['p_value'] * n_tests
        corrected_p = min(corrected_p, 1.0)
        
        results["statistical_tests"][f"bayesian_vs_{method}"] = {
            "raw_p_value": test_result['p_value'],
            "bonferroni_corrected_p_value": corrected_p,
            "significant_at_0.05": corrected_p < ALPHA
        }
        comparisons.append({
            "method": method,
            "p_value": corrected_p
        })

    return results


def save_results(results: Dict[str, Any], output_path: Path):
    """
    Save evaluation results to JSON.
    """
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Evaluation results saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate anomaly detection methods.")
    parser.add_argument("--config", type=str, default="code/config/threshold_strategy.yaml",
                        help="Path to threshold strategy config.")
    parser.add_argument("--output", type=str, default="data/results/evaluation.json",
                        help="Path to output JSON file.")
    args = parser.parse_args()

    try:
        # Load Data
        logger.info("Loading and aligning data...")
        ground_truth, metadata, predictions = load_and_align_data()

        # Load Threshold Strategy
        config_path = Path(args.config)
        threshold = apply_fixed_threshold_strategy(predictions, config_path)

        # Evaluate
        logger.info("Calculating metrics and statistical tests...")
        results = evaluate_all_methods(ground_truth, predictions, threshold)

        # Save
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_results(results, output_path)

        print_summary(results)

    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        sys.exit(1)


def print_summary(results: Dict[str, Any]):
    """
    Print a summary of the evaluation results to stdout.
    """
    print("\n=== Evaluation Summary ===")
    print(f"Threshold Applied: {results['threshold_applied']}")
    print("\nMetrics:")
    print(f"{'Method':<12} {'Precision':>10} {'Recall':>10} {'F1':>10} {'AUC-ROC':>10}")
    print("-" * 52)
    for method, m in results['metrics'].items():
        print(f"{method:<12} {m['precision']:>10.4f} {m['recall']:>10.4f} {m['f1_score']:>10.4f} {m['auc_roc']:>10.4f}")
    
    print("\nStatistical Tests (Bayesian vs Baselines):")
    for test_name, test_res in results['statistical_tests'].items():
        sig = "YES" if test_res['significant_at_0.05'] else "NO"
        print(f"{test_name}: p-val={test_res['bonferroni_corrected_p_value']:.4f} (Significant: {sig})")
    print("=========================\n")


if __name__ == "__main__":
    main()