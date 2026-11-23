"""
T034: Generate ROC curves, precision-recall curves, and feature importance bar plots.

This script consumes the evaluation metrics and model artifacts produced by 
code/03_model/evaluate.py and code/03_model/save_models.py to generate 
publication-ready figures.

Outputs:
  - figures/roc_curve.png
  - figures/precision_recall_curve.png
  - figures/feature_importance.png

Dependencies:
  - matplotlib, seaborn, pandas, numpy, scikit-learn
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_curve, precision_recall_curve, auc

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from utils.config import load_config, get_paths

# Setup logger
logger = get_logger(__name__)

def load_metrics(metrics_path: Path) -> Dict[str, Any]:
    """Load evaluation metrics from JSON file."""
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        return json.load(f)

def load_feature_importance(importance_path: Path) -> pd.DataFrame:
    """Load feature importance data from CSV file."""
    if not importance_path.exists():
        raise FileNotFoundError(f"Feature importance file not found: {importance_path}")
    
    return pd.read_csv(importance_path)

def load_test_predictions(predictions_path: Path) -> Dict[str, np.ndarray]:
    """Load test predictions (probabilities and labels) for plotting."""
    if not predictions_path.exists():
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")
    
    data = np.load(predictions_path, allow_pickle=True)
    return {
        'y_true': data['y_true'],
        'y_score': data['y_score']
    }

def plot_roc_curve(y_true: np.ndarray, y_score: np.ndarray, output_path: Path, title: str = "ROC Curve"):
    """Generate and save ROC curve plot."""
    logger.info(f"Generating ROC curve for {title}")
    
    fpr, tpr, thresholds = roc_curve(y_true, y_score)
    roc_auc = auc(fpr, tpr)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random Classifier')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(title)
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"ROC curve saved to {output_path}")

def plot_precision_recall_curve(y_true: np.ndarray, y_score: np.ndarray, output_path: Path, title: str = "Precision-Recall Curve"):
    """Generate and save Precision-Recall curve plot."""
    logger.info(f"Generating Precision-Recall curve for {title}")
    
    precision, recall, thresholds = precision_recall_curve(y_true, y_score)
    pr_auc = auc(recall, precision)
    
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, color='blue', lw=2, label=f'PR curve (AUC = {pr_auc:.2f})')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title(title)
    plt.legend(loc="lower left")
    plt.grid(alpha=0.3)
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Precision-Recall curve saved to {output_path}")

def plot_feature_importance(feature_df: pd.DataFrame, output_path: Path, top_n: int = 20):
    """Generate and save feature importance bar plot."""
    logger.info(f"Generating feature importance plot (top {top_n} features)")
    
    if feature_df.empty:
        logger.warning("Feature importance DataFrame is empty. Skipping plot.")
        return
    
    # Sort by importance and take top N
    df_sorted = feature_df.sort_values(by='importance', ascending=False).head(top_n)
    
    plt.figure(figsize=(10, 8))
    sns.barplot(data=df_sorted, x='importance', y='feature', palette='viridis')
    plt.xlabel('Importance Score')
    plt.ylabel('Feature')
    plt.title(f'Top {top_n} Genomic Features Predicting Antibiotic Resistance')
    plt.tight_layout()
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Feature importance plot saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate visualization plots from model evaluation results.")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to configuration file")
    parser.add_argument("--metrics", type=str, help="Path to evaluation metrics JSON (overrides config)")
    parser.add_argument("--importance", type=str, help="Path to feature importance CSV (overrides config)")
    parser.add_argument("--predictions", type=str, help="Path to test predictions NPZ (overrides config)")
    parser.add_argument("--output-dir", type=str, help="Output directory for figures (overrides config)")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    paths = get_paths(config)
    
    # Determine input paths (args override config)
    metrics_path = Path(args.metrics) if args.metrics else paths.get('metrics_file')
    importance_path = Path(args.importance) if args.importance else paths.get('feature_importance_file')
    predictions_path = Path(args.predictions) if args.predictions else paths.get('test_predictions_file')
    output_dir = Path(args.output_dir) if args.output_dir else paths.get('figures_dir', 'data/figures')
    
    # Validate input paths
    if not metrics_path:
        logger.error("Metrics file path not specified. Please provide via --metrics or config.")
        sys.exit(1)
    
    # Ensure output directory exists
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        metrics = load_metrics(metrics_path)
        feature_df = load_feature_importance(importance_path) if importance_path else pd.DataFrame()
        
        # Load predictions if available
        if predictions_path and predictions_path.exists():
            predictions = load_test_predictions(predictions_path)
            y_true = predictions['y_true']
            y_score = predictions['y_score']
            
            # Generate ROC and PR curves
            roc_path = output_dir / "roc_curve.png"
            pr_path = output_dir / "precision_recall_curve.png"
            
            # Use antibiotic class name from metrics if available, else default
            antibiotic_class = metrics.get('antibiotic_class', 'Resistance Prediction')
            title_suffix = f" - {antibiotic_class}"
            
            plot_roc_curve(y_true, y_score, roc_path, title=f"ROC Curve{title_suffix}")
            plot_precision_recall_curve(y_true, y_score, pr_path, title=f"Precision-Recall Curve{title_suffix}")
        else:
            logger.warning("Test predictions file not found. Skipping ROC and PR curve generation.")
        
        # Generate feature importance plot
        if not feature_df.empty:
            importance_path_out = output_dir / "feature_importance.png"
            plot_feature_importance(feature_df, importance_path_out)
        else:
            logger.warning("No feature importance data found. Skipping feature importance plot.")
        
        logger.info("All visualization plots generated successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Required input file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error generating plots: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
