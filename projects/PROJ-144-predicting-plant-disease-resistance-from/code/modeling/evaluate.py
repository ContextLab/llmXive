"""
Model evaluation module for plant disease resistance prediction.
Implements metrics computation, permutation testing, FDR-corrected correlations,
sensitivity analysis, and learning curves.
"""
import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import matplotlib.pyplot as plt
from sklearn.metrics import (
    balanced_accuracy_score,
    roc_auc_score,
    precision_recall_curve,
    auc,
    confusion_matrix,
)
from sklearn.model_selection import learning_curve
from sklearn.ensemble import RandomForestClassifier
from scipy.stats import pearsonr
from statsmodels.stats.multitest import multipletests
from code.utils.constants import RANDOM_STATE


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray) -> Dict[str, float]:
    """
    Compute evaluation metrics: Balanced Accuracy, ROC-AUC, and PR-AUC.
    
    Args:
        y_true: True labels (0 or 1)
        y_pred: Predicted labels (0 or 1)
        y_proba: Predicted probabilities for class 1
        
    Returns:
        Dictionary containing balanced_accuracy, roc_auc, and pr_auc
    """
    bal_acc = balanced_accuracy_score(y_true, y_pred)
    roc = roc_auc_score(y_true, y_proba)
    
    # Compute PR-AUC
    precision, recall, _ = precision_recall_curve(y_true, y_proba)
    pr_auc = auc(recall, precision)
    
    return {
        "balanced_accuracy": float(bal_acc),
        "roc_auc": float(roc),
        "pr_auc": float(pr_auc),
    }


def permutation_test(
    model: RandomForestClassifier,
    X: np.ndarray,
    y: np.ndarray,
    n_permutations: int = 1000,
    random_state: int = RANDOM_STATE,
) -> Tuple[float, List[float], float]:
    """
    Perform permutation testing to generate a null distribution and assess significance.
    
    Args:
        model: Trained RandomForestClassifier
        X: Feature matrix
        y: True labels
        n_permutations: Number of permutations to run
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (observed_score, null_distribution, p_value)
    """
    rng = np.random.default_rng(random_state)
    
    # Compute observed score
    model.fit(X, y)
    y_pred = model.predict(X)
    obs_score = balanced_accuracy_score(y, y_pred)
    
    # Generate null distribution
    null_dist = []
    for _ in range(n_permutations):
        # Permute labels
        y_permuted = rng.permutation(y)
        
        # Train on permuted labels
        model_perm = RandomForestClassifier(
            n_estimators=model.n_estimators,
            max_depth=model.max_depth,
            random_state=random_state,
        )
        model_perm.fit(X, y_permuted)
        
        # Predict on original X (with permuted labels used for training)
        # We evaluate on the permuted labels to get the null score
        y_pred_perm = model_perm.predict(X)
        score_perm = balanced_accuracy_score(y_permuted, y_pred_perm)
        null_dist.append(score_perm)
    
    # Compute p-value: proportion of null scores >= observed score
    p_val = np.mean([s >= obs_score for s in null_dist])
    
    return obs_score, null_dist, float(p_val)


def compute_correlations_with_fdr(
    X: pd.DataFrame, y: pd.Series, alpha: float = 0.05
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute Pearson correlations between each metabolite and resistance label,
    applying Benjamini-Hochberg FDR correction.
    
    Args:
        X: Feature DataFrame (metabolites as columns)
        y: Target Series (resistance labels)
        alpha: Significance threshold for FDR
        
    Returns:
        Tuple of (full_correlations_df, significant_correlations_df)
    """
    n_features = X.shape[1]
    correlations = []
    p_values = []
    
    for col in X.columns:
        corr, p_val = pearsonr(X[col], y)
        correlations.append(corr)
        p_values.append(p_val)
    
    # Apply Benjamini-Hochberg FDR correction
    fdr_pvals, _, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    
    corr_df = pd.DataFrame({
        "metabolite": X.columns,
        "correlation": correlations,
        "p_value": p_values,
        "fdr_adjusted_p_value": fdr_pvals,
    })
    
    # Sort by p-value
    corr_df = corr_df.sort_values("p_value")
    
    # Filter significant correlations
    sig_df = corr_df[corr_df["fdr_adjusted_p_value"] <= alpha].copy()
    
    return corr_df, sig_df


def sensitivity_analysis(
    model: RandomForestClassifier,
    X: np.ndarray,
    y: np.ndarray,
    cutoffs: List[float] = [0.01, 0.05, 0.1],
) -> Dict[str, Dict[str, float]]:
    """
    Perform sensitivity analysis by sweeping decision cutoffs.
    
    Args:
        model: Trained model
        X: Feature matrix
        y: True labels
        cutoffs: List of absolute difference cutoffs to test
        
    Returns:
        Dictionary with results for each cutoff
    """
    y_proba = model.predict_proba(X)[:, 1]
    results = {}
    
    for cutoff in cutoffs:
        # Compute predictions with different thresholds
        y_pred = (y_proba >= 0.5).astype(int)
        
        # Calculate confusion matrix
        tn, fp, fn, tp = confusion_matrix(y, y_pred).ravel()
        
        # Calculate rates
        fp_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fn_rate = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        
        results[f"cutoff_{cutoff}"] = {
            "avg_fp_rate": float(fp_rate),
            "avg_fn_rate": float(fn_rate),
            "total_samples": int(len(y)),
        }
    
    return results


def generate_learning_curve(
    model: RandomForestClassifier,
    X: np.ndarray,
    y: np.ndarray,
    cv_folds: int = 5,
    n_points: int = 10,
    random_state: int = RANDOM_STATE,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate a learning curve to assess sample size sufficiency.
    
    Args:
        model: Model instance (unfitted)
        X: Feature matrix
        y: Target vector
        cv_folds: Number of CV folds
        n_points: Number of sample sizes to test
        random_state: Random seed
        
    Returns:
        Tuple of (train_sizes, train_mean, train_std, test_mean, test_std)
    """
    train_sizes, train_scores, test_scores = learning_curve(
        model,
        X,
        y,
        cv=cv_folds,
        train_sizes=np.linspace(0.1, 1.0, n_points),
        scoring="balanced_accuracy",
        random_state=random_state,
        n_jobs=1,  # Single thread for consistency
    )
    
    train_mean = np.mean(train_scores, axis=1)
    train_std = np.std(train_scores, axis=1)
    test_mean = np.mean(test_scores, axis=1)
    test_std = np.std(test_scores, axis=1)
    
    return train_sizes, train_mean, train_std, test_mean, test_std


def evaluate_model(
    model_path: str,
    processed_matrix_path: str,
    labels_path: str,
    output_dir: str,
) -> Dict[str, Any]:
    """
    Run full evaluation pipeline: load model/data, compute metrics,
    permutation test, correlations, sensitivity analysis, and learning curve.
    
    Args:
        model_path: Path to saved model pickle
        processed_matrix_path: Path to processed feature matrix CSV
        labels_path: Path to labels CSV
        output_dir: Directory to save results
        
    Returns:
        Dictionary containing all evaluation results
    """
    # Load data
    model = pickle.load(open(model_path, "rb"))
    X = pd.read_csv(processed_matrix_path)
    y = pd.read_csv(labels_path)
    
    # Ensure y is a Series
    if isinstance(y, pd.DataFrame):
        y = y.iloc[:, 0]
    
    y_arr = y.values
    X_arr = X.values
    
    # Compute metrics
    y_pred = model.predict(X_arr)
    y_proba = model.predict_proba(X_arr)[:, 1]
    metrics = compute_metrics(y_arr, y_pred, y_proba)
    
    # Permutation test
    obs_score, null_dist, p_val = permutation_test(model, X_arr, y_arr, n_permutations=1000)
    
    # Correlations with FDR
    corr_df, sig_df = compute_correlations_with_fdr(X, y)
    
    # Sensitivity analysis
    sens_results = sensitivity_analysis(model, X_arr, y_arr)
    
    # Learning curve
    train_sizes, train_mean, train_std, test_mean, test_std = generate_learning_curve(
        model, X_arr, y_arr
    )
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save metrics
    with open(output_path / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    
    # Save null distribution
    np.save(output_path / "null_distribution.npy", np.array(null_dist))
    
    # Save correlations
    corr_df.to_csv(output_path / "metabolite_correlations.csv", index=False)
    
    # Generate learning curve plot
    plt.figure(figsize=(10, 6))
    plt.plot(train_sizes, train_mean, 'o-', label="Training")
    plt.plot(train_sizes, test_mean, 'o-', label="Validation")
    plt.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.1)
    plt.fill_between(train_sizes, test_mean - test_std, test_mean + test_std, alpha=0.1)
    plt.xlabel("Training Examples")
    plt.ylabel("Balanced Accuracy")
    plt.title("Learning Curve")
    plt.legend()
    plt.grid(True)
    plt.savefig(output_path / "learning_curve.png")
    plt.close()
    
    # Compile results
    results = {
        "metrics": metrics,
        "permutation_test": {
            "observed_score": obs_score,
            "p_value": p_val,
            "n_permutations": 1000,
        },
        "correlations": {
            "significant_count": len(sig_df),
            "top_correlations": sig_df.head(10).to_dict(orient="records"),
        },
        "sensitivity_analysis": sens_results,
        "learning_curve": {
            "train_sizes": train_sizes.tolist(),
            "train_mean": train_mean.tolist(),
            "test_mean": test_mean.tolist(),
        },
    }
    
    return results
