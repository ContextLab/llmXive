"""
Sensitivity Analysis for LLM Code Maintainability Study (T029)

Adjusts effect sizes (Cohen's d) using misclassification rates derived from
the ground truth manual labels to account for potential classifier error.

Logic:
1. Load `data/ground_truth/manual_labels.csv` (Ground Truth) and `data/processed/matched_pairs.csv` (Predicted).
2. Calculate Misclassification Rates (False Positive Rate, False Negative Rate)
   for the LLM vs Human classifier.
3. Load `data/processed/metrics_longitudinal.csv` (Churn/Latency data).
4. Re-estimate the true effect size (Cohen's d) between LLM and Human groups
   using the observed effect size and the misclassification rates.
   Formula: d_true = d_observed / (1 - FPR - FNR)  [Approximation for balanced pairs]
5. Save results to `data/processed/sensitivity_analysis.json`.
"""
import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import math

# Add parent directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
MANUAL_LABELS_PATH = PROJECT_ROOT / "data" / "ground_truth" / "manual_labels.csv"
MATCHED_PAIRS_PATH = PROJECT_ROOT / "data" / "processed" / "matched_pairs.csv"
METRICS_PATH = PROJECT_ROOT / "data" / "processed" / "metrics_longitudinal.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "sensitivity_analysis.json"

class SensitivityAnalysisError(Exception):
    """Custom exception for sensitivity analysis failures."""
    pass

def setup_output_directories():
    """Ensure output directory exists."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ensured: {OUTPUT_PATH.parent}")

def load_ground_truth_labels() -> Dict[str, str]:
    """
    Load manual labels. Returns a dict: {block_id: 'LLM' or 'Human'}
    """
    if not MANUAL_LABELS_PATH.exists():
        raise FileNotFoundError(f"Ground truth file not found: {MANUAL_LABELS_PATH}")
    
    labels = {}
    with open(MANUAL_LABELS_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Assuming columns: block_id, manual_label
            block_id = row.get('block_id')
            manual_label = row.get('manual_label')
            if block_id and manual_label:
                labels[block_id] = manual_label
    logger.info(f"Loaded {len(labels)} ground truth labels.")
    return labels

def load_predicted_labels() -> Dict[str, str]:
    """
    Load predicted labels from matched_pairs.csv.
    Returns a dict: {block_id: 'LLM' or 'Human'}
    """
    if not MATCHED_PAIRS_PATH.exists():
        raise FileNotFoundError(f"Matched pairs file not found: {MATCHED_PAIRS_PATH}")
    
    predictions = {}
    with open(MATCHED_PAIRS_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            block_id = row.get('block_id')
            predicted_label = row.get('predicted_label') # Assuming column name
            if block_id and predicted_label:
                predictions[block_id] = predicted_label
    logger.info(f"Loaded {len(predictions)} predicted labels.")
    return predictions

def calculate_misclassification_rates(
    ground_truth: Dict[str, str], 
    predictions: Dict[str, str]
) -> Dict[str, float]:
    """
    Calculate False Positive Rate (FPR) and False Negative Rate (FNR).
    
    Definitions based on 'LLM' as the positive class:
    - FPR (Human labeled LLM): P(Pred=LLM | True=Human)
    - FNR (LLM labeled Human): P(Pred=Human | True=LLM)
    """
    tp = fp = tn = fn = 0
    
    common_keys = set(ground_truth.keys()) & set(predictions.keys())
    if not common_keys:
        raise SensitivityAnalysisError("No overlapping block IDs between ground truth and predictions.")
    
    for block_id in common_keys:
        true_label = ground_truth[block_id]
        pred_label = predictions[block_id]
        
        # Normalize labels
        true_label = true_label.strip().upper()
        pred_label = pred_label.strip().upper()
        
        if true_label == 'LLM' and pred_label == 'LLM':
            tp += 1
        elif true_label == 'Human' and pred_label == 'LLM':
            fp += 1
        elif true_label == 'Human' and pred_label == 'Human':
            tn += 1
        elif true_label == 'LLM' and pred_label == 'Human':
            fn += 1
        else:
            logger.warning(f"Unexpected label combo for {block_id}: {true_label} vs {pred_label}")

    total_actual_human = tn + fp
    total_actual_llm = tp + fn

    fpr = fp / total_actual_human if total_actual_human > 0 else 0.0
    fnr = fn / total_actual_llm if total_actual_llm > 0 else 0.0

    logger.info(f"Confusion Matrix: TP={tp}, FP={fp}, TN={tn}, FN={fn}")
    logger.info(f"FPR (Human->LLM): {fpr:.4f}, FNR (LLM->Human): {fnr:.4f}")

    return {
        "fpr": fpr,
        "fnr": fnr,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "total_sampled": len(common_keys)
    }

def calculate_cohens_d(group1_values: list, group2_values: list) -> float:
    """
    Calculate Cohen's d effect size.
    d = (mean1 - mean2) / pooled_std
    """
    if not group1_values or not group2_values:
        return 0.0
    
    n1 = len(group1_values)
    n2 = len(group2_values)
    mean1 = sum(group1_values) / n1
    mean2 = sum(group2_values) / n2
    
    # Pooled standard deviation
    var1 = sum((x - mean1) ** 2 for x in group1_values) / (n1 - 1) if n1 > 1 else 0
    var2 = sum((x - mean2) ** 2 for x in group2_values) / (n2 - 1) if n2 > 1 else 0
    
    pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def load_metrics_and_adjust_effect_sizes(
    metrics_path: Path,
    matched_pairs_path: Path,
    misclassification: Dict[str, float]
) -> Dict[str, Any]:
    """
    1. Load metrics and matched pairs.
    2. Compute observed Cohen's d for Churn and Latency.
    3. Adjust effect sizes using the misclassification rates.
       Adjustment Formula: d_corrected = d_observed / (1 - FPR - FNR)
       (Assumes symmetric misclassification impact on means in matched pairs)
    """
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    # Load metrics
    metrics_data = []
    with open(metrics_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            metrics_data.append(row)
    
    if not metrics_data:
        raise SensitivityAnalysisError("No metrics data found.")
    
    # Load matched pairs to get labels
    pair_labels = {}
    with open(matched_pairs_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pair_labels[row['block_id']] = row['predicted_label']
    
    # Group metrics by label
    llm_churn = []
    human_churn = []
    llm_latency = []
    human_latency = []
    
    for row in metrics_data:
        bid = row.get('block_id')
        if bid not in pair_labels:
            continue
        
        label = pair_labels[bid].strip().upper()
        try:
            churn = float(row.get('churn_lines', 0))
            latency = float(row.get('latency_days', 0))
        except ValueError:
            continue
        
        if label == 'LLM':
            llm_churn.append(churn)
            llm_latency.append(latency)
        elif label == 'Human':
            human_churn.append(churn)
            human_latency.append(latency)
    
    # Calculate Observed Effect Sizes
    d_churn_obs = calculate_cohens_d(llm_churn, human_churn)
    d_latency_obs = calculate_cohens_d(llm_latency, human_latency)
    
    # Adjust Effect Sizes
    # Formula: d_true = d_obs / (1 - FPR - FNR)
    # If (1 - FPR - FNR) is <= 0, we cannot correct (perfect noise or worse).
    correction_factor = 1.0 - misclassification['fpr'] - misclassification['fnr']
    
    if correction_factor <= 0:
        logger.warning("Correction factor <= 0. Misclassification is too high to correct effect size. Setting to NaN.")
        d_churn_adj = float('nan')
        d_latency_adj = float('nan')
    else:
        d_churn_adj = d_churn_obs / correction_factor
        d_latency_adj = d_latency_obs / correction_factor

    return {
        "observed": {
            "churn": d_churn_obs,
            "latency": d_latency_obs
        },
        "adjusted": {
            "churn": d_churn_adj,
            "latency": d_latency_adj
        },
        "correction_factor": correction_factor,
        "metrics_counts": {
            "llm_churn": len(llm_churn),
            "human_churn": len(human_churn),
            "llm_latency": len(llm_latency),
            "human_latency": len(human_latency)
        }
    }

def run_sensitivity_analysis():
    """Main entry point for T029."""
    setup_output_directories()
    
    try:
        # 1. Load Data
        logger.info("Loading ground truth labels...")
        ground_truth = load_ground_truth_labels()
        
        logger.info("Loading predicted labels...")
        predictions = load_predicted_labels()
        
        # 2. Calculate Misclassification Rates
        logger.info("Calculating misclassification rates...")
        misclassification = calculate_misclassification_rates(ground_truth, predictions)
        
        # 3. Load Metrics and Adjust Effect Sizes
        logger.info("Loading metrics and adjusting effect sizes...")
        results = load_metrics_and_adjust_effect_sizes(
            METRICS_PATH,
            MATCHED_PAIRS_PATH,
            misclassification
        )
        
        # 4. Compile Final Output
        output_data = {
            "task_id": "T029",
            "description": "Sensitivity Analysis: Adjusted Effect Sizes",
            "misclassification_rates": misclassification,
            "effect_size_analysis": results,
            "methodology": "Adjusted Cohen's d using formula: d_adj = d_obs / (1 - FPR - FNR)",
            "timestamp": str(Path(__file__).parent.parent) # Placeholder for actual timestamp logic if needed
        }
        
        # 5. Save Results
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        logger.info(f"Sensitivity analysis complete. Results saved to {OUTPUT_PATH}")
        print(f"SUCCESS: Sensitivity Analysis completed. Output: {OUTPUT_PATH}")
        return True

    except Exception as e:
        logger.error(f"Sensitivity Analysis failed: {e}", exc_info=True)
        print(f"FAILED: {e}")
        return False

def main():
    success = run_sensitivity_analysis()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
