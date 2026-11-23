import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import roc_auc_score, mean_squared_error, mean_absolute_error

from config import ensure_directories
from utils.logging import get_logger, log_info, log_error, log_warning

logger = get_logger(__name__)

def load_projected_embeddings(embedding_path: Path) -> pd.DataFrame:
    """
    Load projected embeddings and associated metadata from a Parquet file.
    Expected columns: dataset_id, run_id, embedding_vector (list/array), labels (list/array), task_type
    """
    if not embedding_path.exists():
        raise FileNotFoundError(f"Projected embeddings file not found: {embedding_path}")
    
    logger.info(f"Loading projected embeddings from {embedding_path}")
    df = pd.read_parquet(embedding_path)
    
    # Ensure necessary columns exist
    required_cols = ['dataset_id', 'run_id', 'labels', 'task_type']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in embeddings file: {missing_cols}")
    
    return df

def compute_metrics(predictions: np.ndarray, labels: np.ndarray, task_type: str) -> Dict[str, float]:
    """
    Compute performance metrics (AUC for classification, RMSE/MAE for regression).
    
    Args:
        predictions: Array of predicted scores/probabilities
        labels: Array of ground truth labels
        task_type: 'classification' or 'regression'
    
    Returns:
        Dictionary of metric names and values
    """
    metrics = {}
    
    if task_type == 'classification':
        # Ensure binary classification for AUC
        if len(np.unique(labels)) > 2:
            log_warning(f"Multi-class classification detected ({len(np.unique(labels))} classes). "
                        "Computing macro-average AUC.")
            # For multi-class, we need one-vs-rest or macro average
            # Simple approach: use roc_auc_score with multi_class='macro'
            try:
                metrics['auc_macro'] = roc_auc_score(labels, predictions, multi_class='macro', average='macro')
            except ValueError as e:
                log_error(f"Could not compute AUC for {task_type}: {e}")
                metrics['auc_macro'] = float('nan')
        else:
            try:
                metrics['auc'] = roc_auc_score(labels, predictions)
            except ValueError as e:
                log_error(f"Could not compute AUC: {e}")
                metrics['auc'] = float('nan')
    
    elif task_type == 'regression':
        try:
            metrics['rmse'] = float(np.sqrt(mean_squared_error(labels, predictions)))
            metrics['mae'] = float(mean_absolute_error(labels, predictions))
        except Exception as e:
            log_error(f"Could not compute regression metrics: {e}")
            metrics['rmse'] = float('nan')
            metrics['mae'] = float('nan')
    
    return metrics

def evaluate_dataset(df: pd.DataFrame, dataset_id: str, task_type: str) -> Optional[Dict[str, Any]]:
    """
    Evaluate a single dataset's predictions against labels.
    
    Args:
        df: DataFrame containing predictions and labels for the dataset
        dataset_id: Identifier for the dataset
        task_type: Type of task (classification/regression)
    
    Returns:
        Dictionary with dataset_id, task_type, and computed metrics, or None if evaluation fails
    """
    try:
        # Extract labels and predictions
        # Assuming 'labels' column contains ground truth and we need to generate predictions
        # from embeddings. For this task, we assume the 'embedding_vector' is used to predict.
        # In a real scenario, a classifier would be trained on train set and evaluated on test set.
        # Here we simulate by using the last column or a simple projection if labels are provided.
        
        if 'predictions' not in df.columns:
            # If predictions are not pre-computed, we might need to derive them.
            # For this implementation, we assume the task expects us to evaluate
            # based on existing 'predictions' column or generate a simple baseline.
            # Given the context of "held-out test sets", we assume the data loader
            # or previous step provided 'predictions' or we compute them from embeddings.
            # To keep it real and runnable without a full training loop here:
            # We will assume the 'labels' are the target and we need to predict.
            # Since we don't have a trained model in this specific function context,
            # and the task is about *recording* metrics, we assume the input DF
            # should have a 'predictions' column. If not, we raise an error or
            # compute a trivial baseline (e.g., mean) which is not ideal for real research.
            
            # REAL DATA CONSTRAINT: We must not fabricate. If predictions are missing,
            # we cannot compute real metrics. However, the task implies the pipeline
            # (T025) produced projected embeddings. We assume T025 also generated predictions.
            # If the column is missing, we check for a way to derive it or fail.
            raise KeyError("Column 'predictions' not found in dataset. "
                           "The projection pipeline (T025) must output predictions.")
        
        labels = df['labels'].values
        predictions = df['predictions'].values
        
        # Handle NaNs
        valid_mask = ~(np.isnan(labels) | np.isnan(predictions))
        if np.sum(valid_mask) < 10:
            log_warning(f"Insufficient valid data points for {dataset_id}. Skipping.")
            return None
        
        labels = labels[valid_mask]
        predictions = predictions[valid_mask]
        
        metrics = compute_metrics(predictions, labels, task_type)
        
        return {
            "dataset_id": dataset_id,
            "task_type": task_type,
            "num_samples": int(len(labels)),
            "metrics": metrics
        }
        
    except Exception as e:
        log_error(f"Failed to evaluate dataset {dataset_id}: {e}")
        return None

def load_dataset_list(config_path: Path) -> List[Dict[str, Any]]:
    """
    Load the list of datasets to process from the project configuration.
    """
    if not config_path.exists():
        # Fallback to a default list if config is missing, but log warning
        log_warning(f"Config file {config_path} not found. Using default dataset list.")
        return [
            {"dataset_id": "multabench_sample_1", "task_type": "classification"},
            {"dataset_id": "multabench_sample_2", "task_type": "regression"}
        ]
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    return config.get("datasets", [])

def save_metrics_to_json(metrics_list: List[Dict[str, Any]], output_path: Path, run_id: str) -> None:
    """
    Save all metrics to a JSON file with run_id linkage.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    result = {
        "run_id": run_id,
        "generated_at": datetime.now().isoformat(),
        "metrics": metrics_list
    }
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Saved evaluation metrics to {output_path}")

def main():
    """
    Main entry point for T027: Evaluate performance metrics for held-out test sets.
    Loads projected embeddings, computes AUC/RMSE, and saves to JSON.
    """
    ensure_directories()
    
    # Configuration
    run_id = os.getenv("RUN_ID", datetime.now().strftime("%Y%m%d_%H%M%S"))
    embeddings_path = Path("data/processed") / f"embeddings_{run_id}.parquet"
    config_path = Path("code/config.json") # Assuming a config file exists
    output_path = Path("data/artifacts") / f"metrics_conditioned_{run_id}.json"
    
    log_info(f"Starting evaluation for run_id: {run_id}")
    
    # Load embeddings
    try:
        df = load_projected_embeddings(embeddings_path)
    except FileNotFoundError:
        log_error(f"Embeddings file {embeddings_path} not found. "
                  "Please run T025 (run_conditioned) first.")
        sys.exit(1)
    
    # Group by dataset
    dataset_groups = df.groupby('dataset_id')
    
    all_metrics = []
    
    for dataset_id, group in dataset_groups:
        task_type = group['task_type'].iloc[0]
        log_info(f"Evaluating dataset: {dataset_id} (Task: {task_type})")
        
        result = evaluate_dataset(group, dataset_id, task_type)
        if result:
            all_metrics.append(result)
    
    if not all_metrics:
        log_warning("No datasets were successfully evaluated.")
    
    # Save results
    save_metrics_to_json(all_metrics, output_path, run_id)
    
    log_info("Evaluation completed successfully.")

if __name__ == "__main__":
    main()
