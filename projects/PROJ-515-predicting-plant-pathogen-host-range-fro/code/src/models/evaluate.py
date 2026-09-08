"""
Evaluation module for k-fold cross-validation, metrics calculation, and statistical analysis.
Implements FR-005 (AUPRC, Precision, Calibrated Probabilities) and SC-001.
"""
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Union
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.metrics import precision_score, average_precision_score, brier_score_loss
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from loguru import logger

from src.utils.logging import get_logger
from src.models.train import train_l1_logistic_regression, run_vif_selection, calculate_vif, save_model

logger = get_logger()

def calculate_auprc(y_true: np.ndarray, y_scores: np.ndarray) -> float:
    """
    Calculate Area Under the Precision-Recall Curve (AUPRC).
    """
    if len(np.unique(y_true)) < 2:
        logger.warning("Only one class present in y_true. Returning 0.0 AUPRC.")
        return 0.0
    return average_precision_score(y_true, y_scores)

def calculate_precision(y_true: np.ndarray, y_pred: np.ndarray, average: str = 'weighted') -> float:
    """
    Calculate Precision score.
    """
    if len(np.unique(y_true)) < 2:
        logger.warning("Only one class present in y_true. Returning 0.0 Precision.")
        return 0.0
    return precision_score(y_true, y_pred, average=average, zero_division=0)

def run_kfold_cv(
    X: pd.DataFrame,
    y: np.ndarray,
    n_splits: int = 5,
    random_state: int = 42,
    vif_threshold: float = 5.0,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run k-fold cross-validation with L1-regularized Logistic Regression.
    Reports AUPRC, Precision, and calibrated probabilities.
    
    FR-005: Calculate AUPRC, Precision, and calibrated probabilities.
    SC-001: Ensure reproducibility with random_state.
    
    Args:
        X: Feature matrix (DataFrame).
        y: Labels (array).
        n_splits: Number of CV folds.
        random_state: Random seed for reproducibility.
        vif_threshold: Threshold for VIF feature selection.
        output_dir: Directory to save fold-specific artifacts.
        
    Returns:
        Dictionary containing metrics and results.
    """
    logger.info(f"Starting {n_splits}-fold Cross-Validation")
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Use StratifiedKFold for imbalanced classes
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    
    fold_metrics = []
    all_predictions = []
    all_true_labels = []
    all_calibrated_probs = []
    
    for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X, y)):
        logger.info(f"Processing Fold {fold_idx + 1}/{n_splits}")
        
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        # 1. VIF Selection on Training Fold ONLY
        if vif_threshold > 0:
            logger.debug(f"Running VIF selection on fold {fold_idx + 1} (threshold={vif_threshold})")
            X_train_filtered, selected_features = run_vif_selection(X_train, threshold=vif_threshold)
            # Apply same filter to validation set
            if len(selected_features) == 0:
                logger.warning(f"Fold {fold_idx + 1}: No features survived VIF filtering. Skipping fold.")
                continue
            
            X_val_filtered = X_val[selected_features]
        else:
            X_train_filtered = X_train
            X_val_filtered = X_val
            selected_features = list(X_train.columns)
        
        # 2. Train Model
        model = train_l1_logistic_regression(X_train_filtered, y_train)
        
        # 3. Calibrate Probabilities (Platt Scaling / Sigmoid)
        # We use the training fold to fit the calibrator to avoid data leakage from the val set
        # However, standard practice for CV metrics often uses raw scores or calibrates on train
        # to evaluate on val. Here we calibrate on the training fold and predict on val.
        calibrated_clf = CalibratedClassifierCV(model, method='sigmoid', cv='prefit')
        calibrated_clf.fit(X_train_filtered, y_train)
        
        # 4. Predict
        y_pred = calibrated_clf.predict(X_val_filtered)
        y_proba = calibrated_clf.predict_proba(X_val_filtered)[:, 1]
        
        # 5. Calculate Metrics
        auprc = calculate_auprc(y_val, y_proba)
        precision = calculate_precision(y_val, y_pred)
        
        fold_metrics.append({
            "fold": fold_idx + 1,
            "auprc": auprc,
            "precision": precision,
            "n_features_used": len(selected_features)
        })
        
        logger.info(f"Fold {fold_idx + 1} AUPRC: {auprc:.4f}, Precision: {precision:.4f}")
        
        all_predictions.extend(y_pred)
        all_true_labels.extend(y_val)
        all_calibrated_probs.extend(y_proba)
        
        # Save fold-specific model/features if requested
        if output_dir:
            save_model(model, output_dir / f"model_fold_{fold_idx + 1}.pkl")
            pd.DataFrame(selected_features, columns=['feature_name']).to_csv(
                output_dir / f"features_fold_{fold_idx + 1}.csv", index=False
            )
    
    # Aggregate Results
    avg_auprc = np.mean([m['auprc'] for m in fold_metrics])
    avg_precision = np.mean([m['precision'] for m in fold_metrics])
    
    final_metrics = {
        "mean_auprc": avg_auprc,
        "mean_precision": avg_precision,
        "std_auprc": np.std([m['auprc'] for m in fold_metrics]),
        "std_precision": np.std([m['precision'] for m in fold_metrics]),
        "fold_metrics": fold_metrics
    }
    
    # Print Summary
    print_summary(final_metrics)
    
    return {
        "metrics": final_metrics,
        "predictions": np.array(all_predictions),
        "true_labels": np.array(all_true_labels),
        "calibrated_probabilities": np.array(all_calibrated_probs),
        "kfolds": n_splits
    }

def print_summary(metrics: Dict[str, Any]) -> None:
    """
    Print a summary of the cross-validation results to console.
    """
    logger.info("=== Cross-Validation Summary ===")
    logger.info(f"Mean AUPRC: {metrics['mean_auprc']:.4f} (+/- {metrics['std_auprc']:.4f})")
    logger.info(f"Mean Precision: {metrics['mean_precision']:.4f} (+/- {metrics['std_precision']:.4f})")
    logger.info(f"Number of Folds: {len(metrics['fold_metrics'])}")
    logger.info("==============================")

def main():
    """
    Entry point for running evaluation if executed as a script.
    Expects data to be loaded from data/processed/ by default.
    """
    logger.info("Running Evaluation Module (K-Fold CV)")
    
    # Example usage (requires actual data paths to be configured)
    # In a real pipeline, these paths come from config
    data_path = Path("data/processed/features_matrix.csv")
    labels_path = Path("data/processed/labels_vector.npy")
    
    if not data_path.exists() or not labels_path.exists():
        logger.error("Required data files not found. Ensure preprocessing is complete.")
        return
        
    X = pd.read_csv(data_path)
    y = np.load(labels_path)
    
    results = run_kfold_cv(X, y, n_splits=5, output_dir=Path("data/reports/kfold_results"))
    
    # Save results
    results_path = Path("data/reports/cv_results.json")
    with open(results_path, 'w') as f:
        json.dump(results['metrics'], f, indent=2)
    
    logger.info(f"Results saved to {results_path}")

if __name__ == "__main__":
    main()
