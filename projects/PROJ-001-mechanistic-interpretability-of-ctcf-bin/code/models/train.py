"""
Training script for the CTCF binding predictor model.

This script implements Task T021 and T023. It loads the unified dataset,
trains the model, evaluates on a validation set, and saves the best model
weights (triggering T024 logic).
"""
import os
import sys
import json
import logging
import time
import random
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, random_split
import numpy as np
import pandas as pd

from models.predictor import CTCFPredictor
from models.save_model import save_model_weights

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SEED = 42
BATCH_SIZE = 64
NUM_EPOCHS = 20
LEARNING_RATE = 1e-3
# Threshold for fallback logic (T023)
MAX_TRAINING_TIME_SECONDS = 3600  # 1 hour limit for this task execution


def set_seed(seed: int = SEED) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_dataset(dataset_path: Path) -> pd.DataFrame:
    """
    Load the unified CTCF dataset from Parquet.
    
    Args:
        dataset_path: Path to the parquet file.
        
    Returns:
        DataFrame with sequence, chromatin, and label columns.
    """
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")
    
    logger.info(f"Loading dataset from {dataset_path}...")
    df = pd.read_parquet(dataset_path)
    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    return df


def prepare_features_targets(df: pd.DataFrame) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Prepare features (sequence + chromatin) and targets (binding label).
    
    Assumes columns: 'sequence_onehot', 'chromatin_signal', 'label'.
    """
    # Extract sequence (shape: N, 4, 1000)
    if 'sequence_onehot' not in df.columns:
        raise ValueError("Missing 'sequence_onehot' column in dataset")
    
    # Handle potential list-of-lists or numpy array storage in parquet
    seq_data = df['sequence_onehot'].values
    if isinstance(seq_data[0], list):
        seq_tensor = torch.tensor(np.array(seq_data), dtype=torch.float32)
    else:
        seq_tensor = torch.tensor(seq_data, dtype=torch.float32)

    # Extract chromatin (shape: N, num_chromatin_features)
    if 'chromatin_signal' not in df.columns:
        raise ValueError("Missing 'chromatin_signal' column in dataset")
    
    chrom_data = df['chromatin_signal'].values
    if isinstance(chrom_data[0], list):
        chrom_tensor = torch.tensor(np.array(chrom_data), dtype=torch.float32)
    else:
        chrom_tensor = torch.tensor(chrom_data, dtype=torch.float32)

    # Extract labels (shape: N,)
    if 'label' not in df.columns:
        raise ValueError("Missing 'label' column in dataset")
    
    label_tensor = torch.tensor(df['label'].values, dtype=torch.float32)

    # Concatenate features if the model expects a single input, 
    # or return as tuple if the model handles multi-modal input internally.
    # The CTCFPredictor expects (seq, chrom) as separate args in forward.
    # So we return them separately.
    return seq_tensor, chrom_tensor, label_tensor


def create_dataloaders(
    seq: torch.Tensor,
    chrom: torch.Tensor,
    labels: torch.Tensor,
    batch_size: int = BATCH_SIZE,
    val_ratio: float = 0.2
) -> Tuple[DataLoader, DataLoader]:
    """
    Split data into train and validation sets and create DataLoaders.
    
    Args:
        seq: Sequence tensor.
        chrom: Chromatin tensor.
        labels: Label tensor.
        batch_size: Batch size.
        val_ratio: Fraction of data for validation.
        
    Returns:
        train_loader, val_loader
    """
    dataset = TensorDataset(seq, chrom, labels)
    train_size = int((1 - val_ratio) * len(dataset))
    val_size = len(dataset) - train_size

    train_dataset, val_dataset = random_split(
        dataset, [train_size, val_size], generator=torch.Generator().manual_seed(SEED)
    )

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    logger.info(f"Train size: {train_size}, Val size: {val_size}")
    return train_loader, val_loader


def train_epoch(
    model: CTCFPredictor,
    loader: DataLoader,
    optimizer: optim.Optimizer,
    criterion: nn.Module,
    device: torch.device
) -> float:
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    
    for seq_batch, chrom_batch, label_batch in loader:
        seq_batch = seq_batch.to(device)
        chrom_batch = chrom_batch.to(device)
        label_batch = label_batch.to(device)

        optimizer.zero_grad()
        outputs = model(seq_batch, chrom_batch)
        loss = criterion(outputs.squeeze(), label_batch)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item() * len(label_batch)
    
    return total_loss / len(loader.dataset)


def validate_epoch(
    model: CTCFPredictor,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device
) -> Tuple[float, np.ndarray, np.ndarray]:
    """Validate for one epoch, returning loss and predictions."""
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for seq_batch, chrom_batch, label_batch in loader:
            seq_batch = seq_batch.to(device)
            chrom_batch = chrom_batch.to(device)
            label_batch = label_batch.to(device)

            outputs = model(seq_batch, chrom_batch)
            loss = criterion(outputs.squeeze(), label_batch)
            
            total_loss += loss.item() * len(label_batch)
            all_preds.extend(outputs.squeeze().cpu().numpy())
            all_labels.extend(label_batch.cpu().numpy())
    
    avg_loss = total_loss / len(loader.dataset)
    return avg_loss, np.array(all_preds), np.array(all_labels)


def calculate_auc(labels: np.ndarray, preds: np.ndarray) -> float:
    """Calculate AUC-ROC score."""
    from sklearn.metrics import roc_auc_score
    try:
        return roc_auc_score(labels, preds)
    except Exception as e:
        logger.warning(f"Could not calculate AUC: {e}. Returning 0.0")
        return 0.0


def train_model(
    model: CTCFPredictor,
    train_loader: DataLoader,
    val_loader: DataLoader,
    device: torch.device,
    num_epochs: int = NUM_EPOCHS,
    learning_rate: float = LEARNING_RATE,
    patience: int = 5
) -> CTCFPredictor:
    """
    Main training loop with early stopping and best model saving.
    
    Implements T021 (training) and triggers T024 (saving best model).
    """
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.BCEWithLogitsLoss()
    
    best_auc = 0.0
    patience_counter = 0
    start_time = time.time()

    logger.info(f"Starting training on {device}...")

    for epoch in range(num_epochs):
        # Check time constraint (T023)
        elapsed = time.time() - start_time
        if elapsed > MAX_TRAINING_TIME_SECONDS:
            logger.warning(f"Training time limit ({MAX_TRAINING_TIME_SECONDS}s) reached. Stopping early.")
            break

        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        val_loss, val_preds, val_labels = validate_epoch(model, val_loader, criterion, device)
        val_auc = calculate_auc(val_labels, val_preds)

        logger.info(f"Epoch {epoch+1}/{num_epochs} | "
                    f"Train Loss: {train_loss:.4f} | "
                    f"Val Loss: {val_loss:.4f} | "
                    f"Val AUC: {val_auc:.4f}")

        # Save best model (T024 trigger)
        if val_auc > best_auc:
            best_auc = val_auc
            patience_counter = 0
            logger.info(f"New best model found (AUC: {best_auc:.4f}). Saving...")
            # Save to the specific path required by T024
            output_path = Path(__file__).parent.parent / "data" / "models" / "best_ctcf_predictor.pth"
            save_model_weights(model, output_path, metadata={'epoch': epoch+1, 'auc': best_auc})
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(f"Early stopping triggered at epoch {epoch+1}")
                break

    logger.info(f"Training finished. Best AUC: {best_auc:.4f}")
    return model


def ensure_output_dir(output_path: Path) -> None:
    """Ensure directory exists (helper for T024)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """Main entry point for training."""
    set_seed()
    
    # Paths
    project_root = Path(__file__).parent.parent.parent
    dataset_path = project_root / "data" / "processed" / "unified_ctcf_dataset.parquet"
    
    if not dataset_path.exists():
        logger.error(f"Dataset not found at {dataset_path}. Please run T015 first.")
        sys.exit(1)

    # Load and prepare data
    df = load_dataset(dataset_path)
    seq, chrom, labels = prepare_features_targets(df)
    
    # Check for class imbalance and log (T017 style logging)
    pos_count = labels.sum().item()
    neg_count = len(labels) - pos_count
    logger.info(f"Class distribution: Positive={pos_count}, Negative={neg_count}")

    # Create loaders
    train_loader, val_loader = create_dataloaders(seq, chrom, labels)

    # Initialize model
    device = torch.device("cpu") # CPU-only as per spec
    model = CTCFPredictor()
    model = model.to(device)

    # Train
    trained_model = train_model(model, train_loader, val_loader, device)

    # Final evaluation (T022)
    _, final_preds, final_labels = validate_epoch(trained_model, val_loader, nn.BCEWithLogitsLoss(), device)
    final_auc = calculate_auc(final_labels, final_preds)
    
    if final_auc < 0.85:
        logger.warning(f"Final AUC ({final_auc:.4f}) is below target 0.85. Proceeding with warning.")
    else:
        logger.info(f"Final AUC ({final_auc:.4f}) meets target >= 0.85.")

    logger.info("Training pipeline complete.")


if __name__ == "__main__":
    main()
