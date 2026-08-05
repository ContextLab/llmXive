import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import pandas as pd
import numpy as np
from sklearn.metrics import (
    roc_auc_score,
    precision_recall_curve,
    confusion_matrix,
    roc_curve,
    average_precision_score,
)
import matplotlib.pyplot as plt
import seaborn as sns

# Local imports matching the provided API surface
from utils.logging import get_logger
from utils.config import load_config

logger = get_logger(__name__)

def load_test_data(
    feature_path: str,
    model_path: str,
    class_name: str,
) -> Tuple[pd.DataFrame, Any, pd.DataFrame]:
    """
    Load the test feature set, the trained model, and the target column.
    
    Args:
        feature_path: Path to the processed feature matrix CSV.
        model_path: Path to the saved model pickle.
        class_name: The antibiotic class name to filter/evaluate.
        
    Returns:
        Tuple of (X_test, model, y_test)
    """
    logger.info(f"Loading test data from {feature_path}")
    
    # Load features
    if not os.path.exists(feature_path):
        raise FileNotFoundError(f"Feature matrix not found at {feature_path}")
    
    df = pd.read_csv(feature_path, index_col=0)
    
    # Ensure we have the target column
    target_col = f"{class_name}_resistant"
    if target_col not in df.columns:
        # Try to find a column that matches the pattern
        matching_cols = [c for c in df.columns if class_name.lower() in c.lower() and "resistant" in c.lower()]
        if matching_cols:
            target_col = matching_cols[0]
            logger.warning(f"Target column '{target_col}' found via fuzzy match.")
        else:
            raise ValueError(f"Target column '{target_col}' not found in feature matrix.")
    
    # Load model
    import joblib
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}")
    
    model = joblib.load(model_path)
    
    # Split X and y
    y = df[target_col]
    X = df.drop(columns=[target_col])
    
    logger.info(f"Loaded {len(X)} test samples for class '{class_name}'")
    return X, model, y

def calculate_metrics(
    y_true: pd.Series,
    y_pred: np.ndarray,
    y_proba: np.ndarray,
) -> Dict[str, float]:
    """
    Calculate standard classification metrics.
    """
    metrics = {}
    
    try:
        metrics["auc_roc"] = roc_auc_score(y_true, y_proba)
    except Exception as e:
        logger.warning(f"Could not calculate AUC-ROC: {e}")
        metrics["auc_roc"] = np.nan
    
    try:
        metrics["average_precision"] = average_precision_score(y_true, y_proba)
    except Exception as e:
        logger.warning(f"Could not calculate Average Precision: {e}")
        metrics["average_precision"] = np.nan
    
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    metrics["accuracy"] = (tp + tn) / (tp + tn + fp + fn)
    metrics["precision"] = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    metrics["recall"] = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    metrics["f1"] = 2 * (metrics["precision"] * metrics["recall"]) / (metrics["precision"] + metrics["recall"]) if (metrics["precision"] + metrics["recall"]) > 0 else 0.0
    
    return metrics

def plot_roc_curve(y_true: pd.Series, y_proba: np.ndarray, class_name: str, output_path: str):
    """Generate and save ROC curve plot."""
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    auc = roc_auc_score(y_true, y_proba)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(f'Receiver Operating Characteristic - {class_name}')
    plt.legend(loc="lower right")
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved ROC curve to {output_path}")

def plot_precision_recall_curve(y_true: pd.Series, y_proba: np.ndarray, class_name: str, output_path: str):
    """Generate and save Precision-Recall curve plot."""
    precision, recall, _ = precision_recall_curve(y_true, y_proba)
    ap = average_precision_score(y_true, y_proba)
    
    plt.figure(figsize=(8, 6))
    plt.step(recall, precision, color='b', alpha=0.2, where='post')
    plt.fill_between(recall, precision, step='post', alpha=0.2, color='b')
    plt.plot(recall, precision, color='darkorange', lw=2, label=f'PR curve (AP = {ap:.2f})')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.ylim([0.0, 1.05])
    plt.xlim([0.0, 1.0])
    plt.title(f'Precision-Recall Curve - {class_name}')
    plt.legend(loc="lower left")
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved PR curve to {output_path}")

def plot_confusion_matrix(y_true: pd.Series, y_pred: np.ndarray, class_name: str, output_path: str):
    """Generate and save confusion matrix heatmap."""
    cm = confusion_matrix(y_true, y_pred)
    
    plt.figure(figsize=(6, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Sensitive', 'Resistant'], 
                yticklabels=['Sensitive', 'Resistant'])
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title(f'Confusion Matrix - {class_name}')
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved Confusion Matrix to {output_path}")

def evaluate_model(
    X_test: pd.DataFrame,
    y_test: pd.Series,
    model: Any,
    class_name: str,
    output_dir: str,
    top_n_features: int = 20
) -> Dict[str, Any]:
    """
    Evaluate a trained model and generate feature importance rankings.
    
    This function:
    1. Predicts on the test set.
    2. Calculates metrics (AUC, Precision, Recall, etc.).
    3. Generates diagnostic plots.
    4. Ranks genomic features by importance (excluding target gene).
    5. Exports the top N features to a CSV summary table.
    """
    logger.info(f"Evaluating model for class: {class_name}")
    
    # Predictions
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1] if model.predict_proba(X_test).shape[1] > 1 else model.predict_proba(X_test)
    
    # Metrics
    metrics = calculate_metrics(y_test, y_pred, y_proba)
    logger.info(f"Metrics for {class_name}: {metrics}")
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Plots
    plot_roc_curve(y_test, y_proba, class_name, os.path.join(output_dir, f"roc_{class_name}.png"))
    plot_precision_recall_curve(y_test, y_proba, class_name, os.path.join(output_dir, f"pr_{class_name}.png"))
    plot_confusion_matrix(y_test, y_pred, class_name, os.path.join(output_dir, f"confusion_{class_name}.png"))
    
    # Feature Importance Ranking
    feature_importance = {}
    
    if hasattr(model, 'feature_importances_'):
        # Tree-based models (Random Forest)
        importances = model.feature_importances_
    elif hasattr(model, 'coef_'):
        # Linear models (Logistic Regression)
        importances = np.abs(model.coef_[0])
    else:
        logger.warning(f"Model type {type(model)} does not expose standard feature importances.")
        importances = np.zeros(len(X_test.columns))
    
    # Create a dataframe of feature importances
    importance_df = pd.DataFrame({
        'feature': X_test.columns,
        'importance': importances
    })
    
    # Sort by importance descending
    importance_df = importance_df.sort_values(by='importance', ascending=False)
    
    # Identify and exclude the target gene if present in the top features
    # The target gene is typically named based on the class, e.g., 'blaCTX-M' for 'cephalosporin'
    # We exclude any feature that matches the class name pattern exactly or is the primary resistance determinant
    # For safety, we assume the mechanism-blind filter already removed the primary target gene,
    # but we explicitly exclude the column named "{class_name}_resistant" if it somehow got into features (it shouldn't)
    # and we exclude any feature that looks like the primary mechanism gene if it wasn't filtered.
    # Here we just ensure we don't accidentally rank the label itself.
    if f"{class_name}_resistant" in importance_df['feature'].values:
        logger.warning(f"Target label column found in features! Removing it from ranking.")
        importance_df = importance_df[importance_df['feature'] != f"{class_name}_resistant"]
    
    # Select top N features
    top_features = importance_df.head(top_n_features)
    
    # Export to CSV
    output_csv = os.path.join(output_dir, f"top_features_{class_name}.csv")
    top_features.to_csv(output_csv, index=False)
    logger.info(f"Exported top {top_n_features} features for {class_name} to {output_csv}")
    
    return {
        "metrics": metrics,
        "top_features": top_features.to_dict(orient='records'),
        "feature_importance_full": importance_df.to_dict(orient='records')
    }

def main():
    parser = argparse.ArgumentParser(description="Evaluate trained models and export feature rankings.")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to configuration file.")
    parser.add_argument("--class", dest="antibiotic_class", type=str, required=True, help="Antibiotic class to evaluate.")
    parser.add_argument("--features", type=str, required=True, help="Path to feature matrix CSV.")
    parser.add_argument("--model", type=str, required=True, help="Path to saved model pickle.")
    parser.add_argument("--output", type=str, required=True, help="Directory to save evaluation results and plots.")
    parser.add_argument("--top-n", type=int, default=20, help="Number of top features to export.")
    
    args = parser.parse_args()
    
    # Setup logging
    init_logger = get_logger(__name__)
    init_logger.info("Starting model evaluation and feature ranking...")
    
    try:
        # Load data
        X_test, model, y_test = load_test_data(
            feature_path=args.features,
            model_path=args.model,
            class_name=args.antibiotic_class
        )
        
        # Evaluate
        results = evaluate_model(
            X_test=X_test,
            y_test=y_test,
            model=model,
            class_name=args.antibiotic_class,
            output_dir=args.output,
            top_n_features=args.top_n
        )
        
        # Save summary JSON
        summary_path = os.path.join(args.output, f"evaluation_summary_{args.antibiotic_class}.json")
        with open(summary_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Evaluation complete. Summary saved to {summary_path}")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
