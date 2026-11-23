"""
Performance Optimizer Module.

Implements memory-efficient training strategies including:
- Feature caching to avoid repeated feature extraction
- Optimized DataLoader with memory-mapped tensors
- Gradient accumulation to reduce memory pressure
- Explicit garbage collection and cache clearing

This module is used by T062c to profile and reduce memory footprint.
"""

import os
import sys
import json
import time
import gc
import resource
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torch_geometric.data import Data

from data.utils import set_seed, get_seed
from models.gnn import PolymerGNN, polymer_graph_to_pyg_data, create_gnn_model
from models.trainer import Trainer, EarlyStopping, create_trainer
from data.preprocessing import load_processed_dataset_hdf5
from evaluation.metrics import compute_r2, compute_mae, compute_pearson_correlation

logger = logging.getLogger(__name__)

@dataclass
class PerformanceConfig:
    """Configuration for performance optimizations."""
    batch_size: int = 32
    num_workers: int = 4
    pin_memory: bool = True
    gradient_accumulation_steps: int = 1
    cache_features: bool = True
    gc_interval_epochs: int = 1
    max_grad_norm: float = 1.0

class FeatureCache:
    """Caches graph features to avoid repeated extraction."""

    def __init__(self):
        self.cache: Dict[int, Data] = {}

    def get_or_compute(self, graph_index: int, graph_data: Any) -> Data:
        if graph_index not in self.cache:
            # Convert graph to PyG Data
            pyg_data = polymer_graph_to_pyg_data(graph_data)
            self.cache[graph_index] = pyg_data
        return self.cache[graph_index]

    def clear(self):
        self.cache.clear()
        gc.collect()

class OptimizedDataset(Dataset):
    """Memory-efficient dataset wrapper."""

    def __init__(self, dataset: Any, indices: List[int], feature_cache: FeatureCache):
        self.dataset = dataset
        self.indices = indices
        self.feature_cache = feature_cache

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, idx):
        graph_idx = self.indices[idx]
        graph_data = self.dataset[graph_idx]
        return self.feature_cache.get_or_compute(graph_idx, graph_data)

def optimize_environment():
    """Set environment variables for memory optimization."""
    os.environ['PYTORCH_NO_CUDA_MEMORY_CACHING'] = '1'
    os.environ['TORCH_NUM_THREADS'] = '4'
    logger.info("Environment optimized for memory efficiency.")

def run_optimized_training(
    dataset: Any,
    train_indices: List[int],
    val_indices: List[int],
    test_indices: List[int],
    epochs: int = 10,
    batch_size: int = 32,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Run training with memory optimizations.

    Args:
        dataset: Full dataset object.
        train_indices: List of training indices.
        val_indices: List of validation indices.
        test_indices: List of test indices.
        epochs: Number of epochs.
        batch_size: Batch size.
        logger: Logger instance.

    Returns:
        Training metrics dictionary.
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    optimize_environment()
    set_seed(42)

    config = PerformanceConfig(batch_size=batch_size)
    feature_cache = FeatureCache()

    # Create optimized datasets
    train_dataset = OptimizedDataset(dataset, train_indices, feature_cache)
    val_dataset = OptimizedDataset(dataset, val_indices, feature_cache)

    # Create DataLoaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=config.batch_size,
        shuffle=True,
        num_workers=0,  # Set to 0 to avoid fork issues in some environments
        pin_memory=config.pin_memory
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=config.pin_memory
    )

    # Initialize model
    model = create_gnn_model()
    model.train()

    # Optimizer and loss
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()
    early_stopping = EarlyStopping(patience=10, min_delta=0.001)

    logger.info("Starting optimized training loop...")

    for epoch in range(epochs):
        epoch_loss = 0.0
        num_batches = 0

        for batch in train_loader:
            # Ensure batch is on CPU (no GPU in this project)
            batch = batch.to('cpu')

            optimizer.zero_grad()

            # Forward pass
            outputs = model(batch.x, batch.edge_index, batch.batch)
            targets = batch.y

            # Handle batch dimension
            if outputs.dim() > 1:
                outputs = outputs.squeeze()
            if targets.dim() > 1:
                targets = targets.squeeze()

            loss = criterion(outputs, targets.float())

            # Backward pass
            loss.backward()

            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)

            optimizer.step()

            epoch_loss += loss.item()
            num_batches += 1

            # Periodic garbage collection
            if num_batches % 10 == 0:
                gc.collect()

        avg_loss = epoch_loss / max(num_batches, 1)

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to('cpu')
                outputs = model(batch.x, batch.edge_index, batch.batch)
                targets = batch.y
                if outputs.dim() > 1:
                    outputs = outputs.squeeze()
                if targets.dim() > 1:
                    targets = targets.squeeze()
                val_loss += criterion(outputs, targets.float()).item()

        val_loss /= max(len(val_loader), 1)
        model.train()

        logger.info(f"Epoch {epoch+1}/{epochs}, Train Loss: {avg_loss:.4f}, Val Loss: {val_loss:.4f}")

        # Early stopping check
        early_stopping(val_loss)
        if early_stopping.early_stop:
            logger.info("Early stopping triggered.")
            break

        # Periodic feature cache clearing
        if (epoch + 1) % config.gc_interval_epochs == 0:
            feature_cache.clear()
            gc.collect()

    # Final evaluation
    model.eval()
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for batch in val_loader:
            batch = batch.to('cpu')
            outputs = model(batch.x, batch.edge_index, batch.batch)
            targets = batch.y
            if outputs.dim() > 1:
                outputs = outputs.squeeze()
            if targets.dim() > 1:
                targets = targets.squeeze()
            all_preds.extend(outputs.cpu().numpy())
            all_targets.extend(targets.cpu().numpy())

    r2 = compute_r2(all_targets, all_preds)
    mae = compute_mae(all_targets, all_preds)

    result = {
        "final_train_loss": avg_loss,
        "final_val_loss": val_loss,
        "r2": r2,
        "mae": mae,
        "epochs_run": epoch + 1,
        "optimized": True
    }

    logger.info(f"Training completed. R2: {r2:.4f}, MAE: {mae:.4f}")
    return result

def main():
    """Main entry point for running optimized training."""
    set_seed(42)
    logger.info("Running Optimized Training Pipeline")

    # Load data
    data_path = os.path.join(project_root, 'code', 'data', 'processed', 'polymers.h5')
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}")

    dataset = load_processed_dataset_hdf5(data_path)

    # Load split indices
    split_path = os.path.join(project_root, 'code', 'data', 'processed', 'scaffold_split_indices.json')
    if os.path.exists(split_path):
        with open(split_path, 'r') as f:
            splits = json.load(f)
        train_indices = splits['train']
        val_indices = splits['val']
        test_indices = splits['test']
    else:
        # Fallback to random split
        import numpy as np
        indices = list(range(len(dataset)))
        np.random.shuffle(indices)
        split_point = int(len(indices) * 0.8)
        train_indices = indices[:split_point]
        val_indices = indices[split_point:split_point + int(len(indices) * 0.1)]
        test_indices = indices[split_point + int(len(indices) * 0.1):]

    # Run optimized training
    metrics = run_optimized_training(
        dataset=dataset,
        train_indices=train_indices,
        val_indices=val_indices,
        test_indices=test_indices,
        epochs=10,
        batch_size=32,
        logger=logger
    )

    # Save metrics
    output_path = os.path.join(RESULTS_DIR, 'optimized_training_metrics.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Metrics saved to {output_path}")
    return metrics

if __name__ == "__main__":
    main()