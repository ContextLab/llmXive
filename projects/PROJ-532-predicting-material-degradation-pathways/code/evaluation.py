import os
import json
import logging
import pickle
from pathlib import Path
from typing import Tuple, Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score, classification_report
from sklearn.utils import shuffle

# Local imports
from utils import setup_logging, save_json, load_json, ensure_dir, get_env_var

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DATA_PROCESSED = Path("data/processed")
RESULTS_METRICS = Path("results/metrics")
RESULTS_PLOTS = Path("results/plots")
RESULTS_ARTIFACTS = Path("results/artifacts")

# Ensure directories exist
ensure_dir(DATA_PROCESSED)
ensure_dir(RESULTS_METRICS)
ensure_dir(RESULTS_PLOTS)
ensure_dir(RESULTS_ARTIFACTS)

def generate_stratified_baseline(y_true: np.ndarray, n_samples: Optional[int] = None) -> np.ndarray:
    """
    Generate a stratified random baseline preserving class distribution
    and the multi-label correlation structure by shuffling the joint label vector.
    
    Args:
        y_true: 2D array of shape (n_samples, n_labels) with binary labels.
        n_samples: Number of samples to generate (defaults to len(y_true)).
        
    Returns:
        2D array of shape (n_samples, n_labels) with shuffled labels.
    """
    if n_samples is None:
        n_samples = len(y_true)
    
    # Shuffle the joint label vector (row-wise) to preserve multi-label correlations
    y_shuffled = shuffle(y_true, random_state=42)
    
    # If we need fewer samples, slice
    if n_samples < len(y_shuffled):
        y_shuffled = y_shuffled[:n_samples]
        
    return y_shuffled

def perform_permutation_test(y_true: np.ndarray, y_pred: np.ndarray, n_permutations: int = 1000) -> float:
    """
    Perform a permutation test to validate p < 0.05.
    
    Args:
        y_true: True labels (2D array).
        y_pred: Predicted labels (2D array).
        n_permutations: Number of permutations (default 1000).
        
    Returns:
        p-value from the permutation test.
    """
    # Calculate observed macro-F1
    observed_f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
    
    # Generate null distribution
    null_f1_scores = []
    for i in range(n_permutations):
        y_shuffled = generate_stratified_baseline(y_true)
        f1_null = f1_score(y_true, y_shuffled, average='macro', zero_division=0)
        null_f1_scores.append(f1_null)
    
    # Calculate p-value
    p_value = np.sum(null_f1_scores >= observed_f1) / n_permutations
    logger.info(f"Permutation test: observed F1={observed_f1:.4f}, p-value={p_value:.4f}")
    
    return p_value

def calculate_macro_f1(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate macro-F1 score for multi-label classification.
    
    Args:
        y_true: True labels (2D array).
        y_pred: Predicted labels (2D array).
        
    Returns:
        Macro-F1 score.
    """
    return f1_score(y_true, y_pred, average='macro', zero_division=0)

def generate_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, 
                              label_names: List[str], output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Generate confusion matrices for each degradation pathway and identify error modes.
    
    Args:
        y_true: True labels (2D array).
        y_pred: Predicted labels (2D array).
        label_names: List of label names corresponding to columns in y_true/y_pred.
        output_path: Optional path to save the confusion matrix data.
        
    Returns:
        Dictionary containing confusion matrix data and error mode analysis.
    """
    n_labels = y_true.shape[1]
    results = {
        "per_label_confusion_matrices": {},
        "error_modes": {},
        "summary": {
            "total_samples": len(y_true),
            "n_labels": n_labels,
            "label_names": label_names
        }
    }
    
    for i, label_name in enumerate(label_names):
        # Extract binary labels for this specific pathway
        y_true_binary = y_true[:, i]
        y_pred_binary = y_pred[:, i]
        
        # Generate 2x2 confusion matrix: [[TN, FP], [FN, TP]]
        cm = confusion_matrix(y_true_binary, y_pred_binary)
        
        tn, fp, fn, tp = cm.ravel()
        
        # Identify error modes
        # False Positives: Predicted degradation but no actual degradation
        # False Negatives: Actual degradation but predicted no degradation
        error_mode = {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
            "total_errors": int(fp + fn),
            "fp_rate": float(fp / (tn + fp)) if (tn + fp) > 0 else 0.0,
            "fn_rate": float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0,
            "precision": float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0,
            "recall": float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        }
        
        results["per_label_confusion_matrices"][label_name] = {
            "matrix": cm.tolist(),
            "breakdown": {
                "TN": int(tn),
                "FP": int(fp),
                "FN": int(fn),
                "TP": int(tp)
            }
        }
        results["error_modes"][label_name] = error_mode
        
        # Log specific error modes
        if fp > 0:
            logger.info(f"Error mode for {label_name}: {fp} False Positives (predicted degradation when none present)")
        if fn > 0:
            logger.info(f"Error mode for {label_name}: {fn} False Negatives (missed actual degradation)")
    
    # Overall summary
    total_fp = sum(em["false_positives"] for em in results["error_modes"].values())
    total_fn = sum(em["false_negatives"] for em in results["error_modes"].values())
    results["summary"]["total_false_positives"] = total_fp
    results["summary"]["total_false_negatives"] = total_fn
    results["summary"]["overall_error_rate"] = (total_fp + total_fn) / (n_labels * len(y_true)) if n_labels > 0 else 0.0
    
    # Save to file if path provided
    if output_path:
        ensure_dir(output_path.parent)
        save_json(results, output_path)
        logger.info(f"Confusion matrix report saved to {output_path}")
    
    return results

def run_evaluation_pipeline(model_path: Path, data_path: Path, output_dir: Path = RESULTS_METRICS) -> Dict[str, Any]:
    """
    Run the full evaluation pipeline: load model, predict, calculate metrics,
    perform permutation test, and generate confusion matrices.
    
    Args:
        model_path: Path to the trained model artifact (pkl).
        data_path: Path to the test dataset (parquet).
        output_dir: Directory to save evaluation results.
        
    Returns:
        Dictionary containing all evaluation results.
    """
    logger.info(f"Starting evaluation pipeline with model: {model_path}, data: {data_path}")
    
    # Load model
    with open(model_path, 'rb') as f:
        model_artifact = pickle.load(f)
        
    model = model_artifact['model']
    label_names = model_artifact.get('label_names', [])
    
    if not label_names:
        # Fallback: try to infer from data or use generic names
        logger.warning("No label names found in model artifact. Attempting to infer from data.")
        try:
            df = pd.read_parquet(data_path)
            # Assume columns ending with '_label' or similar pattern are labels
            # This is a heuristic; adjust based on actual data schema
            label_cols = [col for col in df.columns if 'label' in col.lower()]
            if not label_cols:
                # Fallback to last N columns if we know N
                n_labels = model_artifact.get('n_labels', 5)
                label_cols = df.columns[-n_labels:].tolist()
            label_names = label_cols
        except Exception as e:
            logger.error(f"Failed to infer label names: {e}")
            raise
    
    # Load test data
    df_test = pd.read_parquet(data_path)
    
    # Separate features and labels
    # Assume all columns except features are labels, or use a specific schema
    # For this implementation, we'll assume the first N columns are features and rest are labels
    # This should be adjusted based on the actual preprocessing output schema
    feature_cols = [col for col in df_test.columns if not col.endswith('_label') and 'label' not in col.lower()]
    label_cols = [col for col in df_test.columns if col.endswith('_label') or 'label' in col.lower()]
    
    if not label_cols:
        # Fallback: assume last 5 columns are labels
        label_cols = df_test.columns[-5:].tolist()
        label_names = label_cols
        
    X_test = df_test[feature_cols].values
    y_true = df_test[label_cols].values
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate macro-F1
    macro_f1 = calculate_macro_f1(y_true, y_pred)
    logger.info(f"Macro-F1 Score: {macro_f1:.4f}")
    
    # Perform permutation test
    p_value = perform_permutation_test(y_true, y_pred, n_permutations=1000)
    
    # Generate confusion matrices
    cm_output_path = output_dir / "confusion_matrix_report.json"
    cm_results = generate_confusion_matrix(y_true, y_pred, label_names, cm_output_path)
    
    # Compile full report
    report = {
        "macro_f1": macro_f1,
        "permutation_test": {
            "n_permutations": 1000,
            "p_value": p_value,
            "significant": p_value < 0.05
        },
        "confusion_matrix_summary": cm_results["summary"],
        "error_modes": cm_results["error_modes"],
        "label_names": label_names,
        "sample_count": len(y_true),
        "feature_count": X_test.shape[1]
    }
    
    # Save full report
    report_path = output_dir / "evaluation_report.json"
    save_json(report, report_path)
    logger.info(f"Evaluation report saved to {report_path}")
    
    return report

def main():
    """Main entry point for evaluation script."""
    # Default paths
    model_path = Path("results/artifacts/model.pkl")
    test_data_path = Path("data/processed/test_ood_set.parquet")
    output_dir = RESULTS_METRICS
    
    # Check if files exist
    if not model_path.exists():
        logger.error(f"Model artifact not found at {model_path}")
        logger.error("Please run training first (T024) to generate the model.")
        return
        
    if not test_data_path.exists():
        logger.error(f"Test data not found at {test_data_path}")
        logger.error("Please run preprocessing first (T019) to generate the OOD split.")
        return
    
    # Run evaluation
    results = run_evaluation_pipeline(model_path, test_data_path, output_dir)
    
    # Print summary
    print("\n=== Evaluation Summary ===")
    print(f"Macro-F1 Score: {results['macro_f1']:.4f}")
    print(f"Permutation Test p-value: {results['permutation_test']['p_value']:.4f} ({'Significant' if results['permutation_test']['significant'] else 'Not Significant'})")
    print(f"Total Samples: {results['sample_count']}")
    print(f"Total Features: {results['feature_count']}")
    print(f"\nError Modes Identified:")
    for label, modes in results['error_modes'].items():
        print(f"  {label}: FP={modes['false_positives']}, FN={modes['false_negatives']}")
    print("=========================\n")

if __name__ == "__main__":
    main()
