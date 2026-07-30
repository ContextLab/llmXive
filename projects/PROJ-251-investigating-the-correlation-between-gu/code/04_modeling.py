import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any, Union
import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score
from utils.config import get_processed_path, get_output_path, get_random_seed
from utils.logging_config import get_logger, log_error_context
from utils.validators import validate_model_metrics_schema

logger = get_logger(__name__)

def load_processed_data() -> pd.DataFrame:
    """Load the preprocessed dataset."""
    path = get_processed_path("cleared_with_diversity.csv")
    if not path.exists():
        raise FileNotFoundError(f"Processed data not found at {path}")
    return pd.read_csv(path)

def calculate_seroconversion_status(df: pd.DataFrame, threshold: float = 4.0) -> pd.Series:
    """Calculate seroconversion status (post >= 4 * baseline)."""
    baseline = df['titer_baseline']
    post = df['titer_post']
    return post >= (threshold * baseline)

def calculate_absolute_titer_status(df: pd.DataFrame, threshold: float = 40.0) -> pd.Series:
    """Calculate absolute titer status (post >= 40)."""
    return df['titer_post'] >= threshold

def define_responder_labels(df: pd.DataFrame, mode: str = "seroconversion", 
                            sero_threshold: float = 4.0, 
                            absolute_threshold: float = 40.0) -> pd.Series:
    """Define responder labels based on mode."""
    if mode == "seroconversion":
        return calculate_seroconversion_status(df, sero_threshold)
    elif mode == "absolute":
        return calculate_absolute_titer_status(df, absolute_threshold)
    else:
        raise ValueError(f"Unknown mode: {mode}")

def save_responder_labels(df: pd.DataFrame, labels: pd.Series, output_path: Path):
    """Save responder labels to CSV."""
    result = pd.DataFrame({
        'subject_id': df['subject_id'],
        'responder_status': labels
    })
    result.to_csv(output_path, index=False)
    logger.info(f"Saved responder labels to {output_path}")

def run_responder_definition(df: pd.DataFrame, mode: str = "seroconversion") -> pd.DataFrame:
    """Run responder definition and return updated dataframe."""
    labels = define_responder_labels(df, mode)
    df = df.copy()
    df['responder_status'] = labels
    return df

def calculate_model_metrics(y_true: pd.Series, y_pred: pd.Series) -> Dict[str, Any]:
    """
    Calculate confusion matrix, precision, recall, and F1-score.
    
    Args:
        y_true: True labels (0 or 1)
        y_pred: Predicted labels (0 or 1)
        
    Returns:
        Dictionary containing metrics
    """
    # Ensure binary labels
    y_true = y_true.astype(int)
    y_pred = y_pred.astype(int)
    
    # Confusion Matrix
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    # Calculate metrics
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    accuracy = (tp + tn) / (tp + tn + fp + fn)
    
    metrics = {
        'confusion_matrix': {
            'true_negative': int(tn),
            'false_positive': int(fp),
            'false_negative': int(fn),
            'true_positive': int(tp)
        },
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'accuracy': float(accuracy)
    }
    
    logger.info(f"Model Metrics - Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}")
    return metrics

def save_model_metrics(metrics: Dict[str, Any], output_path: Path):
    """Save model metrics to JSON file."""
    import json
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved model metrics to {output_path}")

def main():
    """Main entry point for calculating model metrics."""
    try:
        # Load processed data (assumes T034d has run and added predictions)
        df = load_processed_data()
        
        # Check if predictions exist (added by T034d)
        if 'prediction' not in df.columns:
            logger.error("No predictions found in processed data. Run T034d first.")
            sys.exit(1)
        
        # Extract labels and predictions
        y_true = df['responder_status']
        y_pred = df['prediction']
        
        # Calculate metrics
        metrics = calculate_model_metrics(y_true, y_pred)
        
        # Save metrics
        output_path = get_output_path("model_metrics.json")
        save_model_metrics(metrics, output_path)
        
        # Validate output schema
        validate_model_metrics_schema(metrics)
        
        logger.info("T036a completed successfully")
        return metrics
        
    except Exception as e:
        log_error_context(logger, "T036a failed", e)
        raise

if __name__ == "__main__":
    main()
