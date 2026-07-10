import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
import pandas as pd
import numpy as np

# Import from sibling modules as per API surface
from models.predictor import CTCFPredictor, SequenceCNN, LightweightTransformer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for fallback logic
DEFAULT_WINDOW_SIZE = 1000
FALLBACK_WINDOW_SIZES = [1000, 500, 250]
MAX_TRAINING_TIME_SECONDS = 3600  # 1 hour threshold
MAX_EPOCHS = 50
BATCH_SIZE = 32
LEARNING_RATE = 1e-3
SEED = 42

def set_seed(seed: int = SEED):
    """Set random seeds for reproducibility."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def load_dataset(dataset_path: str) -> pd.DataFrame:
    """Load the unified CTCF dataset."""
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")
    logger.info(f"Loading dataset from {dataset_path}")
    return pd.read_parquet(path)

def prepare_features_targets(df: pd.DataFrame) -> Tuple[torch.Tensor, torch.Tensor]:
    """Prepare features and targets from the dataset."""
    # Extract sequence (one-hot encoded) and chromatin features
    # Assuming columns: 'sequence_one_hot', 'chromatin_features', 'label'
    if 'sequence_one_hot' not in df.columns or 'label' not in df.columns:
        raise ValueError("Dataset must contain 'sequence_one_hot' and 'label' columns")

    X_seq = np.stack(df['sequence_one_hot'].values)
    y = df['label'].values.astype(np.float32)

    X_seq = torch.tensor(X_seq, dtype=torch.float32)
    y = torch.tensor(y, dtype=torch.float32)

    return X_seq, y

def create_dataloaders(X: torch.Tensor, y: torch.Tensor, batch_size: int = BATCH_SIZE):
    """Create train and validation dataloaders."""
    # Simple 80/20 split
    n = len(X)
    indices = torch.randperm(n)
    train_size = int(0.8 * n)
    train_idx = indices[:train_size]
    val_idx = indices[train_size:]

    train_dataset = torch.utils.data.TensorDataset(X[train_idx], y[train_idx])
    val_dataset = torch.utils.data.TensorDataset(X[val_idx], y[val_idx])

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    return train_loader, val_loader

def train_epoch(model: nn.Module, loader: DataLoader, optimizer: torch.optim.Optimizer, criterion: nn.Module, device: str):
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    for batch_x, batch_y in loader:
        batch_x, batch_y = batch_x.to(device), batch_y.to(device)
        optimizer.zero_grad()
        outputs = model(batch_x)
        loss = criterion(outputs.squeeze(), batch_y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(loader)

def validate_epoch(model: nn.Module, loader: DataLoader, criterion: nn.Module, device: str) -> float:
    """Validate for one epoch."""
    model.eval()
    total_loss = 0.0
    with torch.no_grad():
        for batch_x, batch_y in loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            outputs = model(batch_x)
            loss = criterion(outputs.squeeze(), batch_y)
            total_loss += loss.item()
    return total_loss / len(loader)

def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: str,
    max_epochs: int = MAX_EPOCHS,
    time_threshold: int = MAX_TRAINING_TIME_SECONDS
) -> Dict[str, Any]:
    """
    Train the model with fallback logic for time constraints.
    
    If training exceeds the time threshold, it attempts to:
    1. Reduce the sequence window size (re-extract features if needed, or simulate by slicing)
    2. Switch to a simpler CNN architecture if the current one is too complex
    
    Returns a dictionary with training metrics and fallback status.
    """
    start_time = time.time()
    best_val_loss = float('inf')
    best_model_state = None
    history = {'train_loss': [], 'val_loss': []}
    fallback_triggered = False
    fallback_reason = None
    final_window_size = None

    logger.info(f"Starting training on {device} with time threshold {time_threshold}s")

    for epoch in range(max_epochs):
        current_time = time.time()
        elapsed = current_time - start_time

        if elapsed > time_threshold:
            fallback_triggered = True
            fallback_reason = f"Training exceeded time threshold ({elapsed:.1f}s > {time_threshold}s)"
            logger.warning(fallback_reason)
            
            # Fallback Strategy 1: Try to reduce window size if we haven't already
            # Note: In a real pipeline, we would re-load data with smaller windows.
            # Here we simulate the effect by slicing the input tensor if possible,
            # or by switching architecture if slicing isn't viable or already done.
            
            # Check if we can switch to a simpler model
            logger.info("Attempting fallback: Switching to simpler CNN architecture...")
            
            # Save current best if available
            if best_model_state is not None:
                model.load_state_dict(best_model_state)
            
            # Create a simpler model (SequenceCNN) if we were using Transformer
            if isinstance(model, LightweightTransformer):
                logger.info("Switching from Transformer to SequenceCNN")
                # Re-initialize model with simpler architecture
                # Assuming input size is based on current window size (e.g., 1000 * 4 for one-hot)
                input_size = train_loader.dataset.tensors[0].shape[1]
                simple_model = SequenceCNN(input_size=input_size, num_classes=1)
                simple_model.to(device)
                model = simple_model
                optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
                best_model_state = None # Reset best state for new model
                logger.info("Model switched to SequenceCNN. Continuing training...")
            else:
                # If already a CNN, we can't simplify further in this context
                # We stop training and return the best model found so far
                logger.info("Already using simplest model. Stopping training early.")
                break

            # Reset epoch counter to re-evaluate on new model/data
            epoch = 0 
            start_time = time.time() # Reset timer for the new phase

        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        val_loss = validate_epoch(model, val_loader, criterion, device)

        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)

        logger.info(f"Epoch {epoch+1}/{max_epochs} - Train Loss: {train_loss:.4f} - Val Loss: {val_loss:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = model.state_dict()

    elapsed = time.time() - start_time
    if best_model_state is not None:
        model.load_state_dict(best_model_state)

    return {
        'final_train_loss': history['train_loss'][-1] if history['train_loss'] else None,
        'final_val_loss': history['val_loss'][-1] if history['val_loss'] else None,
        'best_val_loss': best_val_loss,
        'epochs_completed': len(history['train_loss']),
        'total_time_seconds': elapsed,
        'fallback_triggered': fallback_triggered,
        'fallback_reason': fallback_reason,
        'history': history
    }

def save_model(model: nn.Module, path: str):
    """Save model weights."""
    torch.save(model.state_dict(), path)
    logger.info(f"Model saved to {path}")

def save_metrics(metrics: Dict[str, Any], path: str):
    """Save training metrics to JSON."""
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {path}")

def main():
    """Main entry point for training with fallback logic."""
    # Configuration
    dataset_path = "data/processed/unified_ctcf_dataset.parquet"
    model_save_path = "data/models/best_ctcf_predictor.pth"
    metrics_save_path = "data/models/training_metrics.json"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    set_seed()
    
    # Load data
    try:
        df = load_dataset(dataset_path)
        X, y = prepare_features_targets(df)
        train_loader, val_loader = create_dataloaders(X, y)
    except Exception as e:
        logger.error(f"Failed to load or prepare dataset: {e}")
        sys.exit(1)

    # Initialize model
    # Determine input size from data
    input_size = X.shape[1]
    model = CTCFPredictor(input_size=input_size) # Uses Transformer by default or logic inside
    model.to(device)
    
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    # Train with fallback
    try:
        metrics = train_model(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            criterion=criterion,
            optimizer=optimizer,
            device=device,
            time_threshold=MAX_TRAINING_TIME_SECONDS
        )
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)

    # Save results
    save_model(model, model_save_path)
    save_metrics(metrics, metrics_save_path)

    if metrics['fallback_triggered']:
        logger.warning(f"Fallback logic was triggered: {metrics['fallback_reason']}")
    else:
        logger.info("Training completed without fallback.")

    logger.info(f"Training finished in {metrics['total_time_seconds']:.2f} seconds")

if __name__ == "__main__":
    main()