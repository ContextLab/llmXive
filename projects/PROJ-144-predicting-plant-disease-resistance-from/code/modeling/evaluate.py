"""
Correlation Analysis and Model Evaluation for Plant Disease Resistance Prediction.

This module implements:
1. Correlation analysis (metabolite vs resistance) on training data only.
2. Benjamini-Hochberg FDR correction.
3. Model validation (Balanced Accuracy, ROC-AUC, Permutation testing, Sensitivity analysis).
4. Learning curve generation for small sample sizes.
"""

import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from scipy.stats import spearmanr, pearsonr
from scipy.stats import ttest_ind
from statsmodels.stats.multitest import multipletests
from sklearn.metrics import balanced_accuracy_score, roc_auc_score, precision_recall_curve, confusion_matrix
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import learning_curve
import matplotlib.pyplot as plt
import seaborn as sns

# Project root path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_model_and_indices() -> Tuple[Any, List[int], List[int]]:
    """Load the trained model and split indices from T020."""
    model_path = DATA_PROCESSED_DIR / "model.pkl"
    indices_path = DATA_PROCESSED_DIR / "split_indices.json"

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not indices_path.exists():
        raise FileNotFoundError(f"Split indices file not found: {indices_path}")

    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    with open(indices_path, 'r') as f:
        indices_data = json.load(f)

    train_indices = indices_data.get("train_indices", [])
    holdout_indices = indices_data.get("holdout_indices", [])

    return model, train_indices, holdout_indices

def load_processed_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load the preprocessed metabolite matrix and labels."""
    matrix_path = DATA_PROCESSED_DIR / "batch_corrected_matrix.csv"
    labels_path = DATA_PROCESSED_DIR / "labels.csv"

    if not matrix_path.exists():
        raise FileNotFoundError(f"Processed matrix not found: {matrix_path}")
    if not labels_path.exists():
        raise FileNotFoundError(f"Labels file not found: {labels_path}")

    X = pd.read_csv(matrix_path, index_col=0)
    y = pd.read_csv(labels_path, index_col=0)

    return X, y

def evaluate_model(X_train: pd.DataFrame, y_train: pd.Series, X_test: pd.DataFrame, y_test: pd.Series, model: RandomForestClassifier) -> Dict[str, float]:
    """Compute metrics on the hold-out set."""
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    bal_acc = balanced_accuracy_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_prob)

    # Precision-Recall
    precision, recall, _ = precision_recall_curve(y_test, y_prob)
    pr_auc = -np.trapz(precision, recall) # Approximate AUC-PR

    return {
        "balanced_accuracy": float(bal_acc),
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc)
    }

def permutation_test(model: RandomForestClassifier, X_train: pd.DataFrame, y_train: pd.Series, n_permutations: int = 1000, random_state: int = 42) -> Dict[str, Any]:
    """
    Perform permutation testing to assess significance.
    Returns the p-value based on the null distribution of scores.
    """
    rng = np.random.RandomState(random_state)
    original_score = balanced_accuracy_score(y_train, model.predict(X_train))

    null_scores = []
    for i in range(n_permutations):
        y_perm = y_train.sample(frac=1, random_state=rng.randint(0, 2**31)).reset_index(drop=True)
        # Retrain on permuted data (simplified: we assume the model structure is fixed but we need to refit to get a score for that specific permutation)
        # To save time, we might just shuffle labels and predict with the existing model if we assume the model is fixed?
        # Standard practice: Refit the model on permuted data.
        # Given constraints, we will refit a small RF for the null distribution.
        perm_model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=rng.randint(0, 2**31))
        perm_model.fit(X_train, y_perm)
        score = balanced_accuracy_score(y_perm, perm_model.predict(X_train))
        null_scores.append(score)

    null_scores = np.array(null_scores)
    p_value = (np.sum(null_scores >= original_score) + 1) / (n_permutations + 1)

    return {
        "original_score": float(original_score),
        "p_value": float(p_value),
        "null_distribution_mean": float(np.mean(null_scores)),
        "null_distribution_std": float(np.std(null_scores)),
        "n_permutations": n_permutations
    }

def sensitivity_analysis(model: RandomForestClassifier, X_test: pd.DataFrame, y_test: pd.Series, thresholds: List[float]) -> Dict[str, List[Dict[str, float]]]:
    """
    Sweep decision thresholds to analyze FPR and FNR.
    """
    y_prob = model.predict_proba(X_test)[:, 1]
    results = []

    for thresh in thresholds:
        y_pred = (y_prob >= thresh).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
        
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

        results.append({
            "threshold": thresh,
            "fpr": float(fpr),
            "fnr": float(fnr),
            "tp": int(tp),
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn)
        })

    return {"sensitivity_analysis": results}

def generate_learning_curve(model: RandomForestClassifier, X: pd.DataFrame, y: pd.Series, cv: int = 5) -> str:
    """
    Generate a learning curve plot if sample size is small.
    Returns the path to the saved plot.
    """
    train_sizes, train_scores, test_scores = learning_curve(
        model, X, y, cv=cv, scoring='balanced_accuracy', random_state=42, n_jobs=1
    )

    train_mean = np.mean(train_scores, axis=1)
    train_std = np.std(train_scores, axis=1)
    test_mean = np.mean(test_scores, axis=1)
    test_std = np.std(test_scores, axis=1)

    plt.figure(figsize=(8, 6))
    plt.plot(train_sizes, train_mean, 'o-', color='blue', label='Training score')
    plt.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.1, color='blue')
    plt.plot(train_sizes, test_mean, 'o-', color='green', label='Cross-validation score')
    plt.fill_between(train_sizes, test_mean - test_std, test_mean + test_std, alpha=0.1, color='green')
    plt.xlabel('Number of training examples')
    plt.ylabel('Balanced Accuracy')
    plt.title('Learning Curve (Sample Size < 50)')
    plt.legend(loc='lower right')
    plt.grid(True)

    plot_path = RESULTS_DIR / "learning_curve.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()

    return str(plot_path)

def compute_correlations(X_train: pd.DataFrame, y_train: pd.Series, fdr_threshold: float = 0.05) -> Dict[str, Any]:
    """
    Compute pairwise correlations (metabolite vs resistance) on training data.
    Apply Benjamini-Hochberg FDR correction.
    Filter for |r| > 0.4 and p < 0.01 (FDR corrected).
    """
    correlations = []
    p_values = []
    features = X_train.columns

    # Calculate Spearman correlations
    for feature in features:
        r, p = spearmanr(X_train[feature], y_train)
        correlations.append(r)
        p_values.append(p)

    correlations = np.array(correlations)
    p_values = np.array(p_values)

    # FDR Correction
    reject, p_corrected, _, _ = multipletests(p_values, alpha=fdr_threshold, method='fdr_bh')

    # Filter results
    significant_indices = np.where((np.abs(correlations) > 0.4) & (p_corrected < 0.01))[0]

    results = []
    for idx in significant_indices:
        results.append({
            "feature_name": features[idx],
            "correlation": float(correlations[idx]),
            "p_value_raw": float(p_values[idx]),
            "p_value_fdr": float(p_corrected[idx]),
            "significant": True
        })

    return {
        "top_features": results,
        "total_features_tested": len(features),
        "significant_features_count": len(results),
        "fdr_threshold": fdr_threshold
    }

def main():
    """Main entry point for T021a: Correlation Analysis."""
    print("Starting T021a: Correlation Analysis...")

    # 1. Load Data
    try:
        model, train_indices, holdout_indices = load_model_and_indices()
        X, y = load_processed_data()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # 2. Filter to Training Data only
    X_train = X.iloc[train_indices]
    y_train = y.iloc[train_indices].squeeze() # Ensure it's a Series

    # 3. Compute Correlations (T021a requirement)
    print("Computing correlations on training data...")
    corr_results = compute_correlations(X_train, y_train)

    # Save partial shap_analysis.json
    shap_output_path = RESULTS_DIR / "shap_analysis.json"
    with open(shap_output_path, 'w') as f:
        json.dump(corr_results, f, indent=2)
    print(f"Saved correlation results to {shap_output_path}")

    # 4. Prepare for T021b (Model Validation) - only if N >= 50
    N = len(X_train)
    print(f"Training sample size: {N}")

    if N < 50:
        print("Sample size < 50. Generating learning curve.")
        curve_path = generate_learning_curve(model, X_train, y_train)
        print(f"Learning curve saved to {curve_path}")
    else:
        print("Sample size >= 50. Proceeding with hold-out evaluation.")
        
        X_test = X.iloc[holdout_indices]
        y_test = y.iloc[holdout_indices].squeeze()

        # Evaluate Model
        metrics = evaluate_model(X_train, y_train, X_test, y_test, model)
        
        # Permutation Test
        perm_results = permutation_test(model, X_train, y_train, n_permutations=1000)
        
        # Sensitivity Analysis
        sens_results = sensitivity_analysis(model, X_test, y_test, thresholds=[0.01, 0.05, 0.1])

        # Aggregate results for T024
        final_metrics = {
            "balanced_accuracy": metrics["balanced_accuracy"],
            "roc_auc": metrics["roc_auc"],
            "permutation_p_value": perm_results["p_value"],
            "shap_analysis": corr_results,
            "permutation_details": perm_results,
            "sensitivity_analysis": sens_results,
            "framing": "associational"
        }

        metrics_path = RESULTS_DIR / "metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(final_metrics, f, indent=2)
        print(f"Saved metrics to {metrics_path}")

    print("T021a completed successfully.")

if __name__ == "__main__":
    main()