import json
import os
import sys
import logging
import numpy as np
from pathlib import Path
from scipy import stats
from typing import Dict, Any, List, Tuple, Optional
import time

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger, log_script_start, log_script_end
from config import get_path

logger = get_logger(__name__)

# --- Data Loading Helpers ---

def load_unified_dataset(path: str) -> List[Dict[str, Any]]:
    """Load the unified dataset from JSONL."""
    data = []
    with open(path, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def load_predictions(path: str) -> List[Dict[str, Any]]:
    """Load raw predictions from T016b output."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Predictions file not found: {path}. Run T016b first.")
    data = []
    with open(path, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def load_gap_metrics(path: str) -> Dict[str, Any]:
    """Load generalization gap metrics from T016c."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Gap metrics file not found: {path}. Run T016c first.")
    with open(path, 'r') as f:
        return json.load(f)

# --- Physics Reward Validation ---

def check_physics_reward_exists(data: List[Dict[str, Any]]) -> None:
    """
    Verify that 'physics_reward' exists in the dataset.
    Aborts with a clear error if missing.
    """
    if not data:
        raise ValueError("Dataset is empty; cannot verify physics_reward.")
    
    # Check first record
    first_record = data[0]
    if 'physics_reward' not in first_record:
        raise RuntimeError(
            "CRITICAL ERROR: 'physics_reward' field is missing from the dataset. "
            "The statistical comparison against a physical baseline cannot proceed. "
            "Please verify the data source and transformation pipeline (T010)."
        )
    
    # Count how many records actually have it to ensure it's not just a header artifact
    count = sum(1 for r in data if 'physics_reward' in r)
    if count == 0:
        raise RuntimeError(
            "CRITICAL ERROR: No records contain 'physics_reward'. "
            "The physical baseline source is invalid."
        )
    logger.info(f"Verified physics_reward exists in {count}/{len(data)} records.")

# --- Statistical Analysis Functions ---

def calculate_metrics_from_predictions(predictions: List[Dict[str, Any]]) -> Tuple[List[float], List[float], List[float], List[float]]:
    """
    Calculate per-sample metrics for Symbolic and Physical domains.
    Returns: (symbolic_diffs, physical_diffs, symbolic_preds, physical_preds)
    Note: For this specific task, we compute the difference in 'confidence' or a derived metric 
    between the predicted label and the true label logic, but the task asks for 
    "difference of metrics (Symbolic - Physical)".
    
    Interpretation: We will calculate a 'performance score' per sample.
    Score = 1 if predicted_label == true_label (or logic equivalent), else 0.
    Then we compare the distribution of these scores or the confidence values directly.
    
    However, the task specifically asks for "difference of metrics (Symbolic - Physical)".
    Let's define a metric M for each sample.
    M_symbolic = 1 if (label logic matches prediction) else 0? 
    Actually, a better interpretation for "difference" in a paired test context:
    We have a set of samples. Each sample has a 'symbolic' aspect and a 'physical' aspect.
    The task asks for Shapiro-Wilk on the *difference* of metrics.
    
    Let's compute:
    1. Symbolic Success: 1 if (predicted_label == true_label) based on symbolic logic.
    2. Physical Success: 1 if (predicted_label == true_label) based on physical logic.
    Wait, the model predicts ONE label. The "true" label is derived from the domain.
    
    Let's re-read T016b: "Split into symbolic test set... and physical test set".
    T016d: "Perform Shapiro-Wilk normality test on the difference of metrics (Symbolic - Physical)".
    
    If the sets are disjoint (split), we cannot do a paired test easily unless we have a paired structure.
    But the task implies a paired test ("Paired t-test" or "Wilcoxon signed-rank").
    This suggests we treat the *same* samples as having two potential labels?
    Or, we compare the metric distributions of the two groups? No, "difference of metrics" implies paired.
    
    Hypothesis: The dataset contains samples that have BOTH symbolic and physical ground truths.
    T016b output has `true_label` (likely symbolic) and `physical_label` (derived from physics_reward).
    So for each row:
    - Symbolic Error: 1 if pred != true_label
    - Physical Error: 1 if pred != physical_label
    Difference = Error_Symbolic - Error_Physical? Or Confidence_Symbolic - Confidence_Physical?
    
    Let's use the "Error Rate" (0 or 1) as the metric per sample.
    Metric_S = 1 if (predicted_label != true_label) else 0
    Metric_P = 1 if (predicted_label != physical_label) else 0
    Diff = Metric_S - Metric_P.
    Then test if Diff is significantly different from 0.
    
    If the sets are truly split (some samples only symbolic, some only physical), paired test is invalid.
    But T016b says "Split into symbolic test set ... and physical test set".
    If they are disjoint, we must use an unpaired test (Mann-Whitney U or t-test).
    However, the task explicitly mandates: "If normal, execute Paired t-test; else, execute Wilcoxon signed-rank test".
    This implies the data MUST be paired.
    Therefore, we assume the dataset contains rows where BOTH `true_label` and `physical_label` are valid and comparable.
    We will filter for rows where BOTH are present.
    """
    symbolic_errors = []
    physical_errors = []
    
    for row in predictions:
        # Check for presence of both labels
        if 'true_label' not in row or 'physical_label' not in row:
            continue
        if 'predicted_label' not in row:
            continue
        
        pred = row['predicted_label']
        true_sym = row['true_label']
        true_phys = row['physical_label']
        
        # Metric: 1 if error, 0 if correct
        err_sym = 1 if pred != true_sym else 0
        err_phys = 1 if pred != true_phys else 0
        
        symbolic_errors.append(err_sym)
        physical_errors.append(err_phys)
    
    if len(symbolic_errors) != len(physical_errors) or len(symbolic_errors) == 0:
        raise ValueError("Could not form paired samples for statistical testing. "
                         "Ensure predictions file has both 'true_label' and 'physical_label' for the same rows.")
    
    return symbolic_errors, physical_errors

def perform_statistical_tests(symbolic_vals: List[float], physical_vals: List[float]) -> Dict[str, Any]:
    """
    1. Shapiro-Wilk on the difference (Symbolic - Physical).
    2. If normal -> Paired t-test.
    3. Else -> Wilcoxon signed-rank test.
    4. Return p_value, is_significant, and normality test result.
    """
    diffs = np.array(symbolic_vals) - np.array(physical_vals)
    
    # 1. Shapiro-Wilk
    shapiro_stat, shapiro_p = stats.shapiro(diffs)
    normality_result = {
        "statistic": float(shapiro_stat),
        "p_value": float(shapiro_p),
        "is_normal": shapiro_p > 0.05  # Standard alpha 0.05
    }
    
    logger.info(f"Shapiro-Wilk: stat={shapiro_stat:.4f}, p={shapiro_p:.4f}, normal={normality_result['is_normal']}")
    
    p_value = 0.0
    test_name = ""
    
    if normality_result['is_normal']:
        # Paired t-test
        t_stat, p_value = stats.ttest_rel(symbolic_vals, physical_vals)
        test_name = "Paired t-test"
    else:
        # Wilcoxon signed-rank
        w_stat, p_value = stats.wilcoxon(symbolic_vals, physical_vals)
        test_name = "Wilcoxon signed-rank test"
    
    is_significant = p_value < 0.05
    
    return {
        "normality_test_result": normality_result,
        "test_name": test_name,
        "p_value": float(p_value),
        "is_significant": is_significant
    }

def calculate_bootstrap_ci(symbolic_vals: List[float], physical_vals: List[float], n_iterations: int = 10000, seed: int = 42) -> Tuple[float, float]:
    """
    Perform Bootstrap Confidence Interval on the Generalization Gap (Mean(Symbolic) - Mean(Physical)).
    """
    np.random.seed(seed)
    symbolic_arr = np.array(symbolic_vals)
    physical_arr = np.array(physical_vals)
    n = len(symbolic_arr)
    
    gaps = []
    for _ in range(n_iterations):
        # Resample with replacement
        indices = np.random.choice(n, n, replace=True)
        boot_sym = symbolic_arr[indices]
        boot_phys = physical_arr[indices]
        
        gap = np.mean(boot_sym) - np.mean(boot_phys)
        gaps.append(gap)
    
    gaps = np.array(gaps)
    # 95% CI
    lower = np.percentile(gaps, 2.5)
    upper = np.percentile(gaps, 97.5)
    
    logger.info(f"Bootstrap CI (95%): [{lower:.4f}, {upper:.4f}]")
    return (float(lower), float(upper))

# --- Main Execution ---

def main():
    log_script_start(logger, "T016d - Statistical Test Sequence")
    
    # Paths
    predictions_path = get_path("data/results/raw_predictions.jsonl")
    gap_metrics_path = get_path("data/results/gap_metrics.json")
    output_path = get_path("data/results/comparative_analysis.json")
    
    # 1. Load Data
    logger.info("Loading predictions...")
    predictions = load_predictions(predictions_path)
    
    logger.info("Validating physics_reward existence...")
    # We need to load the original unified dataset or check predictions for physics_reward
    # The task says: "If physics_reward is missing, abort".
    # We can check the predictions file if it was populated by T016b with physics_reward info,
    # or load the unified dataset again.
    # T016b output includes 'physical_label' derived from physics_reward.
    # To be safe, let's load the unified dataset to check the raw field.
    unified_path = get_path("data/processed/unified_dataset.jsonl")
    unified_data = load_unified_dataset(unified_path)
    check_physics_reward_exists(unified_data)
    
    # 2. Calculate Paired Metrics
    logger.info("Calculating paired metrics (Symbolic vs Physical error rates)...")
    sym_errors, phys_errors = calculate_metrics_from_predictions(predictions)
    
    # 3. Statistical Tests
    logger.info("Performing statistical tests...")
    stats_results = perform_statistical_tests(sym_errors, phys_errors)
    
    # 4. Bootstrap CI
    logger.info("Calculating Bootstrap Confidence Interval...")
    # Load the gap value just for reference, but recalculate CI on the raw diffs
    gap_metrics = load_gap_metrics(gap_metrics_path)
    bootstrap_ci = calculate_bootstrap_ci(sym_errors, phys_errors)
    
    # 5. Compile Results
    # Calculate side-by-side metrics (Accuracies)
    sym_acc = 1.0 - np.mean(sym_errors)
    phys_acc = 1.0 - np.mean(phys_errors)
    
    analysis_results = {
        "symbolic_metrics": {
            "accuracy": float(sym_acc),
            "error_rate": float(1 - sym_acc),
            "n_samples": len(sym_errors)
        },
        "physical_metrics": {
            "accuracy": float(phys_acc),
            "error_rate": float(1 - phys_acc),
            "n_samples": len(phys_errors)
        },
        "generalization_gap": float(gap_metrics.get("generalization_gap", sym_acc - phys_acc)),
        "statistical_test": {
            "normality_test_result": stats_results["normality_test_result"],
            "test_method": stats_results["test_name"],
            "p_value": stats_results["p_value"],
            "is_significant": stats_results["is_significant"]
        },
        "bootstrap_confidence_interval": {
            "confidence_level": 0.95,
            "lower": bootstrap_ci[0],
            "upper": bootstrap_ci[1],
            "iterations": 10000
        },
        "physics_baseline_source": "Bridge-to-Worlds (physics_reward field)"
    }
    
    # 6. Save Output
    logger.info(f"Saving results to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(analysis_results, f, indent=2)
    
    log_script_end(logger, "T016d - Statistical Test Sequence")
    logger.info("Done.")

if __name__ == "__main__":
    main()