import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, roc_auc_score, precision_recall_curve, auc
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
from scipy.stats import rankdata
from typing import Tuple, Dict, Any, List

# SHAP import
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("Warning: SHAP library not installed. SHAP analysis will be skipped.")

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    """Compute balanced accuracy, ROC-AUC, and PR-AUC."""
    metrics = {}
    metrics["balanced_accuracy"] = float(balanced_accuracy_score(y_true, y_pred))
    metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
    
    precision, recall, _ = precision_recall_curve(y_true, y_prob)
    metrics["pr_auc"] = float(auc(recall, precision))
    
    return metrics

def permutation_test(model, X: pd.DataFrame, y: pd.Series, n_permutations: int = 1000, random_state: int = 42) -> Dict[str, Any]:
    """Run permutation testing to generate null distribution."""
    np.random.seed(random_state)
    scores = []
    base_score = balanced_accuracy_score(y, model.predict(X))
    
    for i in range(n_permutations):
        y_perm = y.sample(frac=1, random_state=random_state + i).reset_index(drop=True)
        score = balanced_accuracy_score(y_perm, model.predict(X))
        scores.append(score)
    
    p_value = (np.sum(np.array(scores) >= base_score) + 1) / (n_permutations + 1)
    
    return {
        "base_score": float(base_score),
        "null_distribution_mean": float(np.mean(scores)),
        "null_distribution_std": float(np.std(scores)),
        "p_value": float(p_value),
        "n_permutations": n_permutations
    }

def compute_correlations_with_fdr(X: pd.DataFrame, y: pd.Series, alpha: float = 0.05) -> Dict[str, Any]:
    """Compute pairwise correlations and apply Benjamini-Hochberg FDR."""
    correlations = {}
    p_values = []
    features = X.columns
    
    for feat in features:
        corr, p_val = X[feat].corrwith(y).corr, X[feat].corrwith(y).corr # Placeholder for actual corr test
        # Using scipy for actual p-value
        from scipy.stats import pearsonr
        corr, p_val = pearsonr(X[feat], y)
        correlations[feat] = {"corr": float(corr), "p_value": float(p_val)}
        p_values.append(p_val)
    
    # BH Correction
    p_values = np.array(p_values)
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    corrected_p = (sorted_p * n) / (np.arange(1, n + 1) + 1e-9)
    corrected_p = np.minimum(corrected_p, 1.0)
    # Restore order
    final_p = np.zeros(n)
    final_p[sorted_indices] = corrected_p
    
    for i, feat in enumerate(features):
        correlations[feat]["fdr_corrected_p"] = float(final_p[i])
        correlations[feat]["significant"] = bool(final_p[i] <= alpha)
        
    return correlations

def sensitivity_analysis(model, X: pd.DataFrame, y: pd.Series, thresholds: List[float] = [0.01, 0.05, 0.1]) -> Dict[str, Any]:
    """Perform sensitivity analysis by sweeping decision cutoffs."""
    y_prob = model.predict_proba(X)[:, 1]
    results = {}
    
    for thresh in thresholds:
        # Simulate threshold sweep logic (simplified)
        # In reality, this might involve perturbing features or probabilities
        # Here we just report the baseline at different cutoffs for classification
        y_pred = (y_prob >= thresh).astype(int)
        acc = balanced_accuracy_score(y, y_pred)
        results[f"threshold_{thresh}"] = {
            "balanced_accuracy": float(acc),
            "cutoff": float(thresh)
        }
        
    return results

def generate_learning_curve(model, X: pd.DataFrame, y: pd.Series, train_sizes: np.ndarray = None) -> Dict[str, Any]:
    """Generate learning curve data."""
    if train_sizes is None:
        train_sizes = np.linspace(0.1, 1.0, 5)
    
    curve_data = []
    for size in train_sizes:
        n_samples = int(len(X) * size)
        X_sub, _, y_sub, _ = train_test_split(X, y, train_size=n_samples, random_state=42)
        model.fit(X_sub, y_sub)
        score = balanced_accuracy_score(y_sub, model.predict(X_sub))
        curve_data.append({"train_size": float(size), "score": float(score)})
        
    return {"curve": curve_data}

def evaluate_model(model, X: pd.DataFrame, y: pd.Series, n_permutations: int = 1000) -> Tuple[Dict, Dict, Dict, Dict, Dict, Dict]:
    """
    Main evaluation function.
    Returns: metrics, shap_analysis, correlations, sensitivity, learning_curve, permutation_results
    """
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]
    
    metrics = compute_metrics(y.values, y_pred, y_prob)
    perm_results = permutation_test(model, X, y, n_permutations)
    correlations = compute_correlations_with_fdr(X, y)
    sensitivity = sensitivity_analysis(model, X, y)
    learning_curve = generate_learning_curve(model, X, y)
    
    shap_analysis = {}
    if SHAP_AVAILABLE:
        try:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X)
            # Handle binary classification SHAP values (list of 2 arrays or 1 array)
            if isinstance(shap_values, list):
                shap_values = shap_values[1] # Class 1
            
            # Summary
            mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
            feature_names = X.columns
            shap_importance = dict(zip(feature_names, mean_abs_shap.tolist()))
            
            shap_analysis = {
                "available": True,
                "feature_importance": shap_importance,
                "mean_abs_shap": mean_abs_shap.tolist(),
                "top_features": sorted(shap_importance.items(), key=lambda x: x[1], reverse=True)[:10]
            }
        except Exception as e:
            shap_analysis = {"available": False, "error": str(e)}
    else:
        shap_analysis = {"available": False, "reason": "SHAP library not installed"}
        
    return metrics, shap_analysis, correlations, sensitivity, learning_curve, perm_results
