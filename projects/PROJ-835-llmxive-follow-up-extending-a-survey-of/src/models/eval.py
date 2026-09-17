"""
Evaluation module for US3: Statistical Validation & Sensitivity Analysis.

This module calculates Precision, Recall, F1-score, and compares the model
performance against a stratified random baseline (FR-003).
It also performs correlation analysis between Mahalanobis distance and labels.
"""
import os
import sys
import json
import logging
import time
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
from sklearn.utils import resample

# Import project utilities
from src.utils.config import set_random_seed, get_path, ensure_dir, load_state, update_artifact_hash
from src.utils.logging_config import get_module_logger
from src.utils.env_config import enforce_cpu_only

# Initialize logger
logger = get_module_logger(__name__)

# Paths
PROJECT_ROOT = get_path("")
DATA_DIR = get_path("data")
RESULTS_DIR = get_path("results")
STATE_FILE = get_path("state/projects/PROJ-835-llmxive-follow-up-extending-a-survey-of.yaml")

# Input files
PREDICTIONS_FILE = get_path("results/predictions.csv")
ANOMALY_SCORES_FILE = get_path("data/anomaly_scores.parquet")
EMBEDDINGS_FILE = get_path("data/embeddings.parquet")

# Output files
CORRELATION_RESULTS_FILE = get_path("results/correlation.json")
EVAL_REPORT_FILE = get_path("results/report.md")
RESOURCE_LOG_FILE = get_path("results/resource_log.json")


def load_predictions(file_path: str) -> pd.DataFrame:
    """Load predictions from CSV."""
    logger.info(f"Loading predictions from {file_path}")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Predictions file not found: {file_path}")
    df = pd.read_csv(file_path)
    # Ensure expected columns exist
    required_cols = ['sample_id', 'true_label', 'predicted_label', 'prob_jailbreak']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Predictions file missing columns: {missing}")
    return df


def load_anomaly_scores(file_path: str) -> pd.DataFrame:
    """Load anomaly scores from Parquet."""
    logger.info(f"Loading anomaly scores from {file_path}")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Anomaly scores file not found: {file_path}")
    df = pd.read_parquet(file_path)
    # Ensure expected columns exist
    required_cols = ['sample_id', 'mahalanobis_distance', 'true_label']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Anomaly scores file missing columns: {missing}")
    return df


def calculate_baseline_metrics(y_true: np.ndarray, n_samples: int, n_classes: int = 2) -> Dict[str, float]:
    """
    Calculate stratified random baseline metrics.
    The baseline predicts each class with probability equal to its prevalence in the training set.
    Here we simulate a single stratified random guess run.
    """
    # Calculate class proportions
    unique, counts = np.unique(y_true, return_counts=True)
    proportions = counts / len(y_true)

    # Generate stratified random predictions
    # We use the observed proportions to sample predictions
    pred_indices = np.random.choice(n_classes, size=n_samples, p=proportions)
    y_pred_baseline = pred_indices

    # Calculate metrics
    precision = precision_score(y_true, y_pred_baseline, average='binary', zero_division=0)
    recall = recall_score(y_true, y_pred_baseline, average='binary', zero_division=0)
    f1 = f1_score(y_true, y_pred_baseline, average='binary', zero_division=0)

    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'method': 'stratified_random_baseline'
    }


def calculate_model_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate Precision, Recall, F1 for the model."""
    precision = precision_score(y_true, y_pred, average='binary', zero_division=0)
    recall = recall_score(y_true, y_pred, average='binary', zero_division=0)
    f1 = f1_score(y_true, y_pred, average='binary', zero_division=0)

    # Confusion matrix
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'true_negatives': int(tn),
        'false_positives': int(fp),
        'false_negatives': int(fn),
        'true_positives': int(tp),
        'method': 'logistic_regression'
    }


def calculate_correlation_and_hypothesis_test(
    distances: np.ndarray,
    labels: np.ndarray
) -> Dict[str, Any]:
    """
    Calculate Pearson correlation between Mahalanobis distance and jailbreak labels.
    Perform hypothesis test (p-value).
    """
    # Ensure arrays are float for correlation
    distances = distances.astype(float)
    labels = labels.astype(float)

    # Pearson correlation
    correlation, p_value = stats.pearsonr(distances, labels)

    # Hypothesis test: H0: correlation = 0
    # Reject H0 if p < 0.05 or |r| > 0.3 (as per SC-005)
    is_significant = p_value < 0.05
    is_strong = abs(correlation) > 0.3
    threshold_met = is_significant or is_strong

    return {
        'pearson_r': float(correlation),
        'p_value': float(p_value),
        'is_significant': bool(is_significant),
        'is_strong': bool(is_strong),
        'threshold_met': bool(threshold_met),
        'sample_size': int(len(distances))
    }


def save_correlation_results(results: Dict[str, Any], output_path: str) -> None:
    """Save correlation results to JSON."""
    ensure_dir(os.path.dirname(output_path))
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved correlation results to {output_path}")


def generate_report(
    model_metrics: Dict[str, float],
    baseline_metrics: Dict[str, float],
    correlation_results: Dict[str, Any],
    resource_log: Dict[str, Any]
) -> str:
    """Generate a Markdown report."""
    report = []
    report.append("# Evaluation Report")
    report.append("")
    report.append("## Model Performance (Logistic Regression)")
    report.append("")
    report.append(f"- **Precision**: {model_metrics['precision']:.4f}")
    report.append(f"- **Recall**: {model_metrics['recall']:.4f}")
    report.append(f"- **F1-Score**: {model_metrics['f1']:.4f}")
    report.append("")
    report.append("### Confusion Matrix")
    report.append(f"- True Positives: {model_metrics['true_positives']}")
    report.append(f"- False Positives: {model_metrics['false_positives']}")
    report.append(f"- True Negatives: {model_metrics['true_negatives']}")
    report.append(f"- False Negatives: {model_metrics['false_negatives']}")
    report.append("")
    report.append("## Baseline Comparison (Stratified Random)")
    report.append("")
    report.append(f"- **Precision**: {baseline_metrics['precision']:.4f}")
    report.append(f"- **Recall**: {baseline_metrics['recall']:.4f}")
    report.append(f"- **F1-Score**: {baseline_metrics['f1']:.4f}")
    report.append("")
    report.append("### Improvement Over Baseline")
    report.append(f"- Precision Delta: {model_metrics['precision'] - baseline_metrics['precision']:.4f}")
    report.append(f"- Recall Delta: {model_metrics['recall'] - baseline_metrics['recall']:.4f}")
    report.append(f"- F1 Delta: {model_metrics['f1'] - baseline_metrics['f1']:.4f}")
    report.append("")
    report.append("## Correlation Analysis (Mahalanobis Distance vs Labels)")
    report.append("")
    report.append(f"- **Pearson r**: {correlation_results['pearson_r']:.4f}")
    report.append(f"- **P-value**: {correlation_results['p_value']:.6f}")
    report.append(f"- **Significant (p < 0.05)**: {correlation_results['is_significant']}")
    report.append(f"- **Strong (|r| > 0.3)**: {correlation_results['is_strong']}")
    report.append(f"- **Threshold Met (SC-005)**: {correlation_results['threshold_met']}")
    report.append(f"- **Sample Size**: {correlation_results['sample_size']}")
    report.append("")
    report.append("## Resource Usage")
    report.append("")
    report.append(f"- **Total Wall-Clock Time**: {resource_log.get('total_time_seconds', 'N/A'):.2f} seconds")
    report.append(f"- **Peak Memory (MB)**: {resource_log.get('peak_memory_mb', 'N/A')}")
    report.append(f"- **CPU Mode**: {resource_log.get('cpu_only', 'N/A')}")
    report.append("")
    return "\n".join(report)


def save_report(report_content: str, output_path: str) -> None:
    """Save report to Markdown file."""
    ensure_dir(os.path.dirname(output_path))
    with open(output_path, 'w') as f:
        f.write(report_content)
    logger.info(f"Saved report to {output_path}")


def save_resource_log(log_data: Dict[str, Any], output_path: str) -> None:
    """Save resource log to JSON."""
    ensure_dir(os.path.dirname(output_path))
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Saved resource log to {output_path}")


def main():
    """Main entry point for evaluation."""
    enforce_cpu_only()
    start_time = time.time()
    peak_memory_mb = 0

    parser = argparse.ArgumentParser(description="Evaluate model performance and correlations.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    set_random_seed(args.seed)

    try:
        # 1. Load Data
        predictions_df = load_predictions(PREDICTIONS_FILE)
        anomaly_df = load_anomaly_scores(ANOMALY_SCORES_FILE)

        # Merge if necessary to ensure alignment, though T024/T022b should produce aligned IDs
        # We'll use predictions_df for model metrics and anomaly_df for correlation
        # Ensure 'true_label' is consistent
        y_true_model = predictions_df['true_label'].values
        y_pred_model = predictions_df['predicted_label'].values

        # 2. Calculate Model Metrics
        logger.info("Calculating model metrics...")
        model_metrics = calculate_model_metrics(y_true_model, y_pred_model)

        # 3. Calculate Baseline Metrics
        logger.info("Calculating stratified random baseline metrics...")
        baseline_metrics = calculate_baseline_metrics(y_true_model, len(y_true_model))

        # 4. Correlation Analysis
        logger.info("Calculating correlation between Mahalanobis distance and labels...")
        # Use the anomaly scores dataframe for correlation
        distances = anomaly_df['mahalanobis_distance'].values
        labels = anomaly_df['true_label'].values
        correlation_results = calculate_correlation_and_hypothesis_test(distances, labels)

        # Save correlation results
        save_correlation_results(correlation_results, CORRELATION_RESULTS_FILE)

        # 5. Resource Profiling
        end_time = time.time()
        total_time = end_time - start_time

        # Estimate memory (simplified for CPU-only script)
        try:
            import psutil
            process = psutil.Process(os.getpid())
            peak_memory_mb = process.memory_info().rss / (1024 * 1024)
        except ImportError:
            peak_memory_mb = 0.0

        resource_log = {
            'total_time_seconds': total_time,
            'peak_memory_mb': peak_memory_mb,
            'cpu_only': True,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        save_resource_log(resource_log, RESOURCE_LOG_FILE)

        # 6. Generate and Save Report
        logger.info("Generating evaluation report...")
        report_content = generate_report(
            model_metrics,
            baseline_metrics,
            correlation_results,
            resource_log
        )
        save_report(report_content, EVAL_REPORT_FILE)

        # 7. Update State
        logger.info("Updating state file...")
        update_artifact_hash(STATE_FILE, CORRELATION_RESULTS_FILE)
        update_artifact_hash(STATE_FILE, EVAL_REPORT_FILE)
        update_artifact_hash(STATE_FILE, RESOURCE_LOG_FILE)

        logger.info("Evaluation complete.")
        print(json.dumps({
            'status': 'success',
            'f1_model': model_metrics['f1'],
            'f1_baseline': baseline_metrics['f1'],
            'correlation_r': correlation_results['pearson_r'],
            'threshold_met': correlation_results['threshold_met']
        }))

    except Exception as e:
        logger.exception("Evaluation failed.")
        print(json.dumps({'status': 'error', 'message': str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()