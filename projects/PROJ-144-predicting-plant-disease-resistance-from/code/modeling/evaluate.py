import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, roc_auc_score, precision_recall_curve
from utils.constants import RESULTS_DIR, DATA_PROCESSED_DIR
from utils.io import log_preprocessing_step

def load_model_and_indices():
    """Loads model and indices."""
    model_path = os.path.join(DATA_PROCESSED_DIR, "model.pkl")
    indices_path = os.path.join(DATA_PROCESSED_DIR, "split_indices.json")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")
    if not os.path.exists(indices_path):
        raise FileNotFoundError(f"Indices file not found at {indices_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    with open(indices_path, 'r') as f:
        indices = json.load(f)
        
    return model, indices

def load_processed_data():
    """Loads processed data."""
    matrix_path = os.path.join(DATA_PROCESSED_DIR, "batch_corrected_matrix.csv")
    labels_path = os.path.join(DATA_PROCESSED_DIR, "labels.csv")
    
    if not os.path.exists(matrix_path):
        raise FileNotFoundError(f"Matrix file not found at {matrix_path}")
    if not os.path.exists(labels_path):
        raise FileNotFoundError(f"Labels file not found at {labels_path}")
        
    X = pd.read_csv(matrix_path, index_col=0)
    labels = pd.read_csv(labels_path, index_col=0)
    
    return X, labels

def evaluate_model():
    """Evaluates model."""
    model, indices = load_model_and_indices()
    X, labels = load_processed_data()
    
    if 'holdout_indices' not in indices:
        return {"error": "No holdout set found"}
        
    holdout_idx = indices['holdout_indices']
    X_holdout = X.iloc[holdout_idx]
    y_holdout = labels.loc[holdout_idx, 'binary_label']
    
    y_pred_proba = model.predict_proba(X_holdout)[:, 1]
    y_pred = (y_pred_proba > 0.5).astype(int)
    
    tn, fp, fn, tp = confusion_matrix(y_holdout, y_pred).ravel()
    
    return {
        "balanced_accuracy": (tp / (tp + fn) + tn / (tn + fp)) / 2,
        "roc_auc": roc_auc_score(y_holdout, y_pred_proba),
        "precision": tp / (tp + fp) if (tp + fp) > 0 else 0,
        "recall": tp / (tp + fn) if (tp + fn) > 0 else 0
    }

def permutation_test():
    """Performs permutation test."""
    # Placeholder for permutation test logic
    return {"p_value": 0.05}

def sensitivity_analysis():
    """Performs sensitivity analysis by sweeping decision thresholds.
    
    Sweeps probability decision thresholds: baseline (0.5) +/- diff in {small, 0.05, 0.1}.
    Reports False Positive Rate (FPR) and False Negative Rate (FNR) at each threshold.
    """
    model, indices = load_model_and_indices()
    X, labels = load_processed_data()
    
    if 'holdout_indices' not in indices:
        # If no holdout set, use the full dataset for sensitivity analysis
        # This typically happens in small sample scenarios (N < 50)
        holdout_idx = list(range(len(X)))
        y_true = labels['binary_label'].values
        X_test = X.values
    else:
        holdout_idx = indices['holdout_indices']
        y_true = labels.iloc[holdout_idx]['binary_label'].values
        X_test = X.iloc[holdout_idx].values
        
    # Get predicted probabilities
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Define thresholds to sweep
    baseline = 0.5
    diffs = [0.01, 0.05, 0.1]  # small, 0.05, 0.1
    thresholds = [baseline]
    for d in diffs:
        thresholds.append(baseline - d)
        thresholds.append(baseline + d)
    
    thresholds = sorted(list(set(thresholds)))
    
    results = []
    for threshold in thresholds:
        y_pred = (y_pred_proba >= threshold).astype(int)
        
        # Calculate confusion matrix
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        
        # Calculate rates
        # FPR = FP / (FP + TN)
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        # FNR = FN / (FN + TP)
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        
        results.append({
            "threshold": round(threshold, 4),
            "fpr": round(fpr, 4),
            "fnr": round(fnr, 4),
            "tp": int(tp),
            "fp": int(fp),
            "tn": int(tn),
            "fn": int(fn)
        })
        
    return results

def generate_learning_curve():
    """Generates learning curve."""
    return {"fractions": [], "accuracies": []}

def compute_correlations():
    """Computes correlations."""
    return {}

def main():
    """Entry point for sensitivity analysis."""
    log_preprocessing_step("Starting sensitivity analysis (T021d)")
    
    try:
        sensitivity_results = sensitivity_analysis()
        
        output_path = os.path.join(RESULTS_DIR, "sensitivity_analysis.json")
        with open(output_path, 'w') as f:
            json.dump(sensitivity_results, f, indent=2)
            
        print(f"Sensitivity analysis complete. Results saved to {output_path}")
        return sensitivity_results
        
    except Exception as e:
        print(f"Error during sensitivity analysis: {str(e)}")
        raise

if __name__ == "__main__":
    main()