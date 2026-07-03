import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score, confusion_matrix, classification_report

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import load_config
from classification.ground_truth import load_search_time_data, label_by_median_split

logger = logging.getLogger(__name__)

def load_held_out_data(file_path: str) -> pd.DataFrame:
    """
    Load the held-out dataset containing predictions and ground truth labels.
    Expected columns: 'predicted_prob', 'label' (and potentially 'status').
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Held-out data file not found: {file_path}")
    
    df = pd.read_csv(path)
    
    required_cols = ['predicted_prob', 'label']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Held-out data missing required columns: {missing_cols}")
    
    # Ensure label is numeric (0/1)
    if df['label'].dtype not in [np.int64, np.float64, int, float]:
        # Attempt to convert if it's string '0'/'1' or similar
        try:
            df['label'] = pd.to_numeric(df['label'], errors='raise')
        except ValueError:
            raise ValueError(f"Cannot convert 'label' column to numeric in {file_path}")
    
    # Filter out rows where status is UNVALIDABLE if necessary, 
    # though for evaluation we usually need the labels present.
    # We proceed with all rows that have valid labels.
    return df

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> dict:
    """
    Compute standard classification metrics: Accuracy, Precision, Recall, ROC-AUC.
    """
    metrics = {}
    
    # Accuracy
    metrics['accuracy'] = accuracy_score(y_true, y_pred)
    
    # Precision (binary classification, average='binary')
    # If only one class is present, precision might be undefined, handle carefully
    try:
        metrics['precision'] = precision_score(y_true, y_pred, zero_division=0)
    except Exception as e:
        logger.warning(f"Could not compute precision: {e}")
        metrics['precision'] = np.nan
    
    # Recall
    try:
        metrics['recall'] = recall_score(y_true, y_pred, zero_division=0)
    except Exception as e:
        logger.warning(f"Could not compute recall: {e}")
        metrics['recall'] = np.nan
    
    # ROC-AUC
    # Requires at least two classes in y_true to compute
    if len(np.unique(y_true)) > 1:
        try:
            metrics['roc_auc'] = roc_auc_score(y_true, y_prob)
        except Exception as e:
            logger.warning(f"Could not compute ROC-AUC: {e}")
            metrics['roc_auc'] = np.nan
    else:
        logger.warning("Only one class present in y_true; ROC-AUC is undefined.")
        metrics['roc_auc'] = np.nan
    
    return metrics

def evaluate_held_out(held_out_path: str, output_path: str) -> None:
    """
    Main evaluation routine: load data, compute metrics, save results.
    """
    logger.info(f"Loading held-out data from {held_out_path}")
    df = load_held_out_data(held_out_path)
    
    logger.info(f"Computing metrics on {len(df)} samples")
    
    # Prepare arrays
    y_true = df['label'].values
    y_prob = df['predicted_prob'].values
    
    # Convert probabilities to binary predictions (threshold 0.5)
    y_pred = (y_prob >= 0.5).astype(int)
    
    # Compute metrics
    metrics = compute_metrics(y_true, y_pred, y_prob)
    
    # Add confusion matrix details
    cm = confusion_matrix(y_true, y_pred)
    metrics['confusion_matrix'] = cm.tolist()
    
    # Generate classification report string for logging
    report = classification_report(y_true, y_pred, output_dict=True)
    metrics['classification_report'] = report
    
    # Log results
    logger.info(f"Evaluation Results: Accuracy={metrics['accuracy']:.4f}, "
                f"Precision={metrics['precision']:.4f}, "
                f"Recall={metrics['recall']:.4f}, "
                f"ROC-AUC={metrics['roc_auc']:.4f}")
    
    # Save to CSV
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Flatten metrics for CSV output
    row_data = {
        'metric': 'accuracy',
        'value': metrics['accuracy']
    }
    # We will save a summary row, but usually we want a table.
    # Let's create a wide-format row or a long-format table.
    # Given the requirement "output full metric tables", let's do a wide format for the summary.
    
    summary_df = pd.DataFrame([{
        'dataset': 'held_out',
        'accuracy': metrics['accuracy'],
        'precision': metrics['precision'],
        'recall': metrics['recall'],
        'roc_auc': metrics['roc_auc']
    }])
    
    summary_df.to_csv(output_file, index=False)
    logger.info(f"Saved metrics to {output_file}")
    
    # Also save detailed report if needed, but the CSV is the primary artifact
    return metrics

def main():
    parser = argparse.ArgumentParser(description="Evaluate classification performance on held-out set")
    parser.add_argument('--input', type=str, required=True, 
                        help='Path to the held-out dataset CSV (with predicted_prob and label)')
    parser.add_argument('--output', type=str, default='results/classification_metrics.csv',
                        help='Path to save the evaluation metrics CSV')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    try:
        evaluate_held_out(args.input, args.output)
        logger.info("Evaluation completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Data error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during evaluation: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
