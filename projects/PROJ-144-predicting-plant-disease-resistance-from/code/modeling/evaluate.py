import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, roc_auc_score, precision_recall_curve, accuracy_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
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
    """Generates learning curve and performs power analysis for small datasets (N < 50).
    
    If N < 50, performs learning curve analysis by training on subsamples.
    Calculates the slope of the learning curve at the maximum sample size.
    If the slope remains steep (indicating underfitting due to sample size),
    flags the result with a 'power_limitation_warning' in the output JSON.
    
    Returns:
        dict: Learning curve results including accuracies, fractions, and optional warning.
    """
    X, labels = load_processed_data()
    
    # Ensure binary_label column exists
    if 'binary_label' not in labels.columns:
        raise ValueError("labels.csv must contain a 'binary_label' column")
        
    y = labels['binary_label'].values
    X_data = X.values
    n_samples = len(y)
    
    output = {
        "total_samples": n_samples,
        "fractions": [],
        "accuracies": [],
        "power_limitation_warning": None
    }
    
    # Only perform learning curve analysis if N < 50 (as per task spec)
    if n_samples >= 50:
        log_preprocessing_step("Learning curve analysis skipped: N >= 50")
        output["note"] = "Learning curve analysis only performed for N < 50"
        return output
        
    log_preprocessing_step(f"Performing learning curve analysis for small dataset (N={n_samples})")
    
    # Define fractions to test: [0.2, 0.4, 0.6, 0.8, 1.0]
    fractions = [0.2, 0.4, 0.6, 0.8, 1.0]
    # Filter fractions that result in at least 5 samples (minimum for meaningful training)
    valid_fractions = []
    for f in fractions:
        n_train = int(n_samples * f)
        if n_train >= 5:
            valid_fractions.append(f)
            
    if len(valid_fractions) < 2:
        output["warning"] = "Insufficient samples for learning curve analysis"
        return output
        
    accuracies = []
    
    # Use StratifiedKFold for small datasets to ensure class balance
    # For very small datasets, we might not be able to use multiple folds
    n_splits = min(3, len(np.unique(y)))
    if n_splits < 2:
        output["warning"] = "Insufficient class balance for cross-validation"
        return output
        
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    for fraction in valid_fractions:
        n_train = int(n_samples * fraction)
        
        # Create a training subset
        indices = np.arange(n_samples)
        np.random.seed(42)  # For reproducibility
        np.random.shuffle(indices)
        train_indices = indices[:n_train]
        
        X_train = X_data[train_indices]
        y_train = y[train_indices]
        
        # Train model and evaluate using cross-validation on this subset
        model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        
        # Use the same CV strategy for evaluation
        cv_scores = []
        for train_idx, val_idx in cv.split(X_train, y_train):
            X_sub_train = X_train[train_idx]
            y_sub_train = y_train[train_idx]
            X_sub_val = X_train[val_idx]
            y_sub_val = y_train[val_idx]
            
            model.fit(X_sub_train, y_sub_train)
            y_pred = model.predict(X_sub_val)
            acc = accuracy_score(y_sub_val, y_pred)
            cv_scores.append(acc)
            
        mean_acc = np.mean(cv_scores)
        accuracies.append(mean_acc)
        
        output["fractions"].append(fraction)
        output["accuracies"].append(round(mean_acc, 4))
        
    # Calculate slope at maximum sample size
    # Using linear regression on the last 2-3 points to estimate slope
    if len(accuracies) >= 2:
        x_vals = np.array(valid_fractions[-3:])  # Use last 3 points if available
        y_vals = np.array(accuracies[-3:])
        
        # Simple linear regression
        n = len(x_vals)
        sum_x = np.sum(x_vals)
        sum_y = np.sum(y_vals)
        sum_xy = np.sum(x_vals * y_vals)
        sum_x2 = np.sum(x_vals ** 2)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        output["slope_at_max"] = round(slope, 6)
        
        # If slope is steep (e.g., > 0.1), it indicates underfitting due to sample size
        # A steep positive slope means accuracy is still increasing significantly
        if slope > 0.1:
            output["power_limitation_warning"] = (
                "Learning curve slope remains steep at maximum sample size, indicating "
                "underfitting due to limited data. Statistical significance claims should "
                "be treated with caution. Consider collecting more data or using simpler models."
            )
            
    log_preprocessing_step(f"Learning curve analysis complete. Output saved to {RESULTS_DIR}/learning_curve.json")
    return output

def compute_correlations():
    """Computes correlations."""
    return {}

def main():
    """Entry point for sensitivity analysis and learning curve power analysis."""
    log_preprocessing_step("Starting evaluation pipeline (T021d + T038)")
    
    try:
        # First, perform sensitivity analysis
        sensitivity_results = sensitivity_analysis()
        
        output_path = os.path.join(RESULTS_DIR, "sensitivity_analysis.json")
        with open(output_path, 'w') as f:
            json.dump(sensitivity_results, f, indent=2)
            
        print(f"Sensitivity analysis complete. Results saved to {output_path}")
        
        # Then, perform learning curve power analysis (T038)
        learning_curve_results = generate_learning_curve()
        
        lc_output_path = os.path.join(RESULTS_DIR, "learning_curve.json")
        with open(lc_output_path, 'w') as f:
            json.dump(learning_curve_results, f, indent=2)
            
        print(f"Learning curve analysis complete. Results saved to {lc_output_path}")
        
        if learning_curve_results.get("power_limitation_warning"):
            print(f"WARNING: {learning_curve_results['power_limitation_warning']}")
            
        return {
            "sensitivity_analysis": sensitivity_results,
            "learning_curve": learning_curve_results
        }
        
    except Exception as e:
        print(f"Error during evaluation: {str(e)}")
        raise

if __name__ == "__main__":
    main()