import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score, accuracy_score, precision_recall_curve, auc
from sklearn.model_selection import train_test_split

# Import existing model architecture and loader
from models.predictor import CTCFPredictor, load_model

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_dataset(dataset_path: str) -> pd.DataFrame:
    """Load the unified dataset from parquet."""
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")
    logger.info(f"Loading dataset from {dataset_path}")
    return pd.read_parquet(dataset_path)

def prepare_features_targets(df: pd.DataFrame, device: torch.device) -> tuple:
    """
    Prepare features and targets from the dataframe.
    Expects columns: 'sequence_one_hot', 'chromatin_signals', 'label'
    Returns tensors on the specified device.
    """
    # Convert sequence one-hot (assuming stored as list of lists or numpy array)
    if isinstance(df['sequence_one_hot'].iloc[0], list):
        sequences = np.array(df['sequence_one_hot'].tolist(), dtype=np.float32)
    else:
        sequences = np.array(df['sequence_one_hot'].values, dtype=np.float32)
    
    # Convert chromatin signals
    if isinstance(df['chromatin_signals'].iloc[0], list):
        chromatin = np.array(df['chromatin_signals'].tolist(), dtype=np.float32)
    else:
        chromatin = np.array(df['chromatin_signals'].values, dtype=np.float32)
    
    # Convert labels
    labels = np.array(df['label'].values, dtype=np.float32)

    # Stack features: (N, 4, L) for sequence, (N, M) for chromatin
    # Note: The model expects specific input shapes. Adjust if necessary based on predictor.py
    # Assuming predictor expects (N, 4, L) and (N, M)
    X_seq = torch.tensor(sequences, device=device)
    X_chrom = torch.tensor(chromatin, device=device)
    y = torch.tensor(labels, device=device)

    return X_seq, X_chrom, y

def evaluate_model(
    model: nn.Module,
    X_seq: torch.Tensor,
    X_chrom: torch.Tensor,
    y: torch.Tensor,
    batch_size: int = 32,
    device: torch.device = torch.device('cpu')
) -> Dict[str, float]:
    """
    Evaluate the model on the provided data.
    Returns a dictionary with metrics: auc_roc, accuracy, precision, recall, f1
    """
    model.eval()
    dataset = TensorDataset(X_seq, X_chrom, y)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

    all_preds = []
    all_labels = []

    with torch.no_grad():
        for batch_seq, batch_chrom, batch_y in dataloader:
            # Forward pass
            outputs = model(batch_seq, batch_chrom)
            probs = torch.sigmoid(outputs)
            
            all_preds.append(probs.cpu().numpy())
            all_labels.append(batch_y.cpu().numpy())

    all_preds = np.concatenate(all_preds)
    all_labels = np.concatenate(all_labels)

    # Calculate metrics
    auc_roc = roc_auc_score(all_labels, all_preds)
    # Threshold for binary classification
    threshold = 0.5
    binary_preds = (all_preds >= threshold).astype(int)
    
    accuracy = accuracy_score(all_labels, binary_preds)
    
    # Precision and Recall
    tp = np.sum((all_labels == 1) & (binary_preds == 1))
    fp = np.sum((all_labels == 0) & (binary_preds == 1))
    fn = np.sum((all_labels == 1) & (binary_preds == 0))
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        'auc_roc': float(auc_roc),
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1)
    }

def main():
    """
    Main entry point for evaluation.
    Loads the trained model and dataset, computes AUC-ROC on validation set,
    and logs a warning if AUC-ROC < 0.85.
    """
    # Configuration
    # Assuming the dataset is the processed unified dataset
    # In a real pipeline, we might need to load a specific validation split or the whole dataset if already split
    # For this task, we assume the dataset contains the validation data or we split it here
    dataset_path = os.getenv('UNIFIED_DATASET_PATH', 'data/processed/unified_ctcf_dataset.parquet')
    model_path = os.getenv('MODEL_PATH', 'data/models/best_ctcf_predictor.pth')
    output_metrics_path = os.getenv('METRICS_PATH', 'data/processed/evaluation_metrics.json')
    
    # Check for file existence
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset not found at {dataset_path}. Please ensure T015 has completed.")
        sys.exit(1)
    
    if not os.path.exists(model_path):
        logger.error(f"Model not found at {model_path}. Please ensure T021 has completed.")
        sys.exit(1)

    device = torch.device('cpu') # CPU-only as per spec
    logger.info(f"Using device: {device}")

    # Load dataset
    try:
        df = load_dataset(dataset_path)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)

    # Split into train/val if not already split (assuming the dataset is full)
    # The task says "compute AUC-ROC on the validation set"
    # If the dataset is already split, we might need a flag or specific columns.
    # For robustness, we'll do a split here if 'is_validation' column doesn't exist.
    if 'is_validation' not in df.columns:
        logger.info("No 'is_validation' column found. Splitting dataset 80/20.")
        train_df, val_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['label'])
        logger.info(f"Validation set size: {len(val_df)}")
        eval_df = val_df
    else:
        eval_df = df[df['is_validation'] == True]
        logger.info(f"Using validation set from 'is_validation' column. Size: {len(eval_df)}")

    if len(eval_df) == 0:
        logger.error("Validation set is empty.")
        sys.exit(1)

    # Prepare data
    try:
        X_seq, X_chrom, y = prepare_features_targets(eval_df, device)
    except Exception as e:
        logger.error(f"Failed to prepare features and targets: {e}")
        sys.exit(1)

    # Load model
    try:
        model = load_model(model_path, device=device)
        logger.info("Model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)

    # Evaluate
    metrics = evaluate_model(model, X_seq, X_chrom, y, device=device)
    
    logger.info("-" * 40)
    logger.info("Evaluation Results:")
    for key, value in metrics.items():
        logger.info(f"  {key}: {value:.4f}")
    logger.info("-" * 40)

    # Check threshold
    threshold = 0.85
    if metrics['auc_roc'] < threshold:
        logger.warning(f"AUC-ROC ({metrics['auc_roc']:.4f}) is below the threshold of {threshold}. Continuing execution.")
    else:
        logger.info(f"AUC-ROC ({metrics['auc_roc']:.4f}) meets or exceeds the threshold of {threshold}.")

    # Save metrics
    try:
        os.makedirs(os.path.dirname(output_metrics_path), exist_ok=True)
        with open(output_metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Metrics saved to {output_metrics_path}")
    except Exception as e:
        logger.error(f"Failed to save metrics: {e}")
        sys.exit(1)

    logger.info("Evaluation completed successfully.")

if __name__ == '__main__':
    main()