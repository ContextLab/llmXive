import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

# Import from project API surface
from utils.logging import DataPipelineLog
from utils.stats import delong_test_auc, calculate_roc_auc
from config import get_config, ensure_directories
from models.entities import ModelResult

def load_test_data() -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Load the processed test data from the split phase.
    Returns: (X_test, y_test, y_test_labels)
    """
    config = get_config()
    data_path = Path(config["data"]["processed_dir"]) / "split_data" / "test_set.parquet"
    
    if not data_path.exists():
        # Fallback for legacy CSV if parquet not generated yet
        csv_path = Path(config["data"]["processed_dir"]) / "split_data" / "test_set.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
        else:
            raise FileNotFoundError(f"Test data not found at {data_path} or {csv_path}. Run data/split.py first.")
    else:
        df = pd.read_parquet(data_path)
    
    # Expect columns: features (all except label), label
    # Assuming the split script saved 'features' as columns and 'label' as target
    # If the split script saved separate files, we need to load them. 
    # Based on typical pipeline: split.py saves X_train, y_train, X_test, y_test.
    # Let's assume a unified dataframe with a 'label' column for simplicity if not separated.
    # However, standard practice in this pipeline (T015) likely saves separate files or a structured dict.
    # Let's implement a robust loader that checks for standard split outputs.
    
    # Check for standard split outputs
    test_features_path = Path(config["data"]["processed_dir"]) / "split_data" / "X_test.parquet"
    test_labels_path = Path(config["data"]["processed_dir"]) / "split_data" / "y_test.parquet"
    
    if test_features_path.exists() and test_labels_path.exists():
        X_test = pd.read_parquet(test_features_path)
        y_test = pd.read_parquet(test_labels_path)
    else:
        # Fallback to single file or CSV
        if data_path.exists():
            df = pd.read_parquet(data_path)
            if 'label' in df.columns:
                y_test = df['label']
                X_test = df.drop(columns=['label'])
            else:
                raise ValueError("Test data file does not contain 'label' column and separate files not found.")
        else:
            raise FileNotFoundError("Split data files not found.")
    
    return X_test, y_test, y_test

def load_models() -> Dict[str, Any]:
    """
    Load all trained models from the training phase.
    Returns: Dict mapping model_name -> (model_object, metrics_dict)
    """
    config = get_config()
    model_dir = Path(config["models"]["output_dir"])
    
    models = {}
    # Expected files: rf_model.joblib, xgb_model.joblib, knn_model.joblib, plus their metrics
    model_files = {
        "RandomForest": "rf_model.joblib",
        "XGBoost": "xgb_model.joblib",
        "KNN_Baseline": "knn_model.joblib"
    }
    
    metrics_file = model_dir / "model_metrics.json"
    if not metrics_file.exists():
        raise FileNotFoundError(f"Model metrics file not found at {metrics_file}. Run train.py first.")
    
    with open(metrics_file, 'r') as f:
        all_metrics = json.load(f)
    
    for name, filename in model_files.items():
        model_path = model_dir / filename
        if model_path.exists():
            model_obj = joblib.load(model_path)
            # Retrieve metrics for this model
            model_metrics = all_metrics.get(name, {})
            models[name] = {
                "model": model_obj,
                "metrics": model_metrics
            }
        else:
            print(f"Warning: Model file {filename} not found.")
    
    return models

def evaluate_model(model: Any, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """
    Evaluate a single model on the test set.
    Returns: Dict of metrics (ROC-AUC, Precision, Recall, F1)
    """
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)
    
    auc = calculate_roc_auc(y_test, y_pred_proba)
    
    # Calculate other metrics manually if not in stats.py
    tp = ((y_test == 1) & (y_pred == 1)).sum()
    fp = ((y_test == 0) & (y_pred == 1)).sum()
    fn = ((y_test == 1) & (y_pred == 0)).sum()
    tn = ((y_test == 0) & (y_pred == 0)).sum()
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "roc_auc": float(auc),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1)
    }

def select_best_model(models: Dict[str, Dict]) -> Tuple[str, Dict]:
    """
    Select the best model based on ROC-AUC from the test set evaluation.
    If metrics are already available from training (cross-validation), use those.
    Otherwise, re-evaluate on test set.
    """
    best_name = None
    best_score = -1.0
    best_info = None
    
    # First, check if we have pre-computed test metrics or CV metrics
    # For this task, we assume we need to run DeLong on the TEST set AUCs
    # So we must evaluate on test set if not already done.
    
    for name, info in models.items():
        model_obj = info["model"]
        # We need to evaluate on test set to get the specific AUC for DeLong comparison
        # Note: In a real pipeline, we might cache these, but for T023 we ensure calculation.
        # However, the task says "comparing best model AUC vs Baseline AUC".
        # We need to identify the best model first.
        # Let's assume the "best" model is the one with highest CV score from training,
        # but for DeLong we need the specific test AUCs.
        # Strategy: Evaluate all models on test set, pick best by test AUC for the "Best" label,
        # then compare that best vs Baseline.
        
        # We will return the evaluation function to be called in main or here
        pass
    
    return best_name, best_info

def save_metrics(metrics: Dict[str, Any], output_path: Path):
    """Save metrics to JSON."""
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

def main():
    """
    Main entry point for T023: DeLong's Test Evaluation.
    1. Load test data.
    2. Load trained models (RF, XGBoost, KNN Baseline).
    3. Evaluate all models to get Test AUCs.
    4. Identify Best Model (highest AUC).
    5. Perform DeLong's Test: Best Model vs Baseline (KNN).
    6. Verify p < 0.05 AND AUC diff > 0.05.
    7. Log results and save to data/processed/evaluation_results.json.
    """
    logger = DataPipelineLog()
    logger.start_task("T023_Delong_Evaluation")
    
    try:
        # 1. Load Data
        X_test, y_test, _ = load_test_data()
        logger.record_info("Data", f"Loaded test set with {len(y_test)} samples")
        
        # 2. Load Models
        models_data = load_models()
        if len(models_data) < 2:
            raise ValueError("Need at least two models (Best + Baseline) for DeLong's test.")
        
        # 3. Evaluate all models to get Test AUCs
        results = {}
        auc_scores = {}
        
        for name, info in models_data.items():
            model_obj = info["model"]
            metrics = evaluate_model(model_obj, X_test, y_test)
            results[name] = metrics
            auc_scores[name] = metrics['roc_auc']
            logger.record_info("Evaluation", f"{name} Test AUC: {metrics['roc_auc']:.4f}")
        
        # 4. Identify Best Model and Baseline
        # Baseline is explicitly KNN_Baseline
        baseline_name = "KNN_Baseline"
        if baseline_name not in auc_scores:
            raise ValueError(f"Baseline model {baseline_name} not found in results.")
        
        baseline_auc = auc_scores[baseline_name]
        
        # Find best model (excluding baseline if we want to compare against it, 
        # but usually we compare the winner against the baseline)
        # Best model is the one with max AUC among all
        best_model_name = max(auc_scores, key=auc_scores.get)
        best_model_auc = auc_scores[best_model_name]
        
        logger.record_info("Selection", f"Best Model: {best_model_name} (AUC: {best_model_auc:.4f})")
        logger.record_info("Selection", f"Baseline Model: {baseline_name} (AUC: {baseline_auc:.4f})")
        
        # 5. Perform DeLong's Test
        # We need the probability predictions for DeLong's test
        best_model_obj = models_data[best_model_name]["model"]
        baseline_model_obj = models_data[baseline_name]["model"]
        
        y_pred_best = best_model_obj.predict_proba(X_test)[:, 1]
        y_pred_baseline = baseline_model_obj.predict_proba(X_test)[:, 1]
        
        # Convert to numpy arrays
        y_true_arr = y_test.values
        y_pred_best_arr = np.array(y_pred_best)
        y_pred_baseline_arr = np.array(y_pred_baseline)
        
        # Run DeLong's test
        # delong_test_auc returns (auc1, auc2, p_value) or similar
        # Based on stats.py API: delong_test_auc(y_true, y_pred1, y_pred2)
        try:
            auc1, auc2, p_value = delong_test_auc(y_true_arr, y_pred_best_arr, y_pred_baseline_arr)
        except Exception as e:
            logger.record_error("DeLong", f"DeLong test failed: {str(e)}")
            raise
        
        logger.record_info("DeLong", f"p-value: {p_value:.6f}")
        
        # 6. Verification
        auc_diff = abs(auc1 - auc2)
        is_significant = p_value < 0.05
        is_diff_large = auc_diff > 0.05
        
        verification_result = {
            "best_model": best_model_name,
            "best_auc": float(best_model_auc),
            "baseline_model": baseline_name,
            "baseline_auc": float(baseline_auc),
            "auc_difference": float(auc_diff),
            "p_value": float(p_value),
            "p_less_005": is_significant,
            "diff_greater_005": is_diff_large,
            "passed_validation": is_significant and is_diff_large
        }
        
        logger.record_info("Verification", f"p < 0.05: {is_significant}, |Diff| > 0.05: {is_diff_large}")
        logger.record_info("Verification", f"Overall Validation: {'PASSED' if verification_result['passed_validation'] else 'FAILED'}")
        
        # 7. Save Results
        config = get_config()
        output_dir = Path(config["data"]["processed_dir"])
        output_file = output_dir / "delong_evaluation_results.json"
        ensure_directories([output_dir])
        
        # Combine all results
        final_report = {
            "task_id": "T023",
            "timestamp": str(pd.Timestamp.now()),
            "test_samples": len(y_test),
            "model_results": results,
            "delong_test": verification_result
        }
        
        save_metrics(final_report, output_file)
        logger.record_info("Output", f"Results saved to {output_file}")
        
        # Exit with appropriate code if validation fails (optional, but good for CI)
        if not verification_result["passed_validation"]:
            logger.record_warning("Validation", "DeLong test verification failed (p>=0.05 or diff<=0.05).")
            # Do not crash, just log. The task is implemented, the result is what it is.
        
        print(f"DeLong Test Complete. Best: {best_model_name}, Baseline: {baseline_name}")
        print(f"P-value: {p_value:.6f}, AUC Diff: {auc_diff:.4f}")
        print(f"Validation Status: {'PASSED' if verification_result['passed_validation'] else 'FAILED'}")
        
    except Exception as e:
        logger.record_error("T023", str(e))
        print(f"Error in T023: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()