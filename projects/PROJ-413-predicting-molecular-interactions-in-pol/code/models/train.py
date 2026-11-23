import os
import sys
import json
import time
import signal
import logging
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Local imports based on project API surface
from utils.exceptions import DataError, TrainingTimeoutError
from utils.seed_utils import set_seed
from models.gat import GATModel, create_gat_model
from utils.logger import PerformanceLogger, log_performance

# Configuration
SEED = 42
SET_SEED = True
DATA_PATH = Path("data/processed/graphs.pt")
MODEL_PATH = Path("results/model.pt")
CHECKPOINT_DIR = Path("results")
LOG_PATH = Path("results/performance.json")

# Training Hyperparameters
EPOCHS = 100
BATCH_SIZE = 32
LEARNING_RATE = 0.001
WEIGHT_DECAY = 1e-4
HIDDEN_DIM = 64
NUM_HEADS = 4
DROPOUT = 0.5
TRAIN_RATIO = 0.8
VALID_RATIO = 0.1
TEST_RATIO = 0.1

# Timeout Constraints (in seconds)
HARD_TIMEOUT = 6 * 3600  # 6 hours
SOFT_TIMEOUT = 4.5 * 3600  # 4.5 hours
CHECKPOINT_INTERVAL_EPOCHS = 10

logger = logging.getLogger(__name__)

def timeout_handler(signum, frame):
    """Signal handler for hard timeout."""
    raise TrainingTimeoutError(f"Training exceeded hard timeout of {HARD_TIMEOUT} seconds.")

def check_timeout_elapsed(start_time: float) -> bool:
    """Check if hard timeout has elapsed."""
    elapsed = time.time() - start_time
    if elapsed > HARD_TIMEOUT:
        raise TrainingTimeoutError(f"Training exceeded hard timeout of {HARD_TIMEOUT} seconds.")
    return False

def check_soft_timeout_and_checkpoint(start_time: float, epoch: int, model: nn.Module, optimizer: optim.Optimizer) -> bool:
    """
    Check if soft timeout (4.5h) has been reached.
    If so, save a checkpoint and return True to indicate we should stop training.
    """
    elapsed = time.time() - start_time
    if elapsed > SOFT_TIMEOUT:
        checkpoint_path = CHECKPOINT_DIR / f"checkpoint_{epoch}.pt"
        save_checkpoint(model, optimizer, epoch, checkpoint_path)
        logger.warning(f"Soft timeout ({SOFT_TIMEOUT}s) reached at epoch {epoch}. Checkpoint saved to {checkpoint_path}. Stopping training.")
        return True
    return False

def load_graphs_and_targets() -> Tuple[List[torch.Tensor], torch.Tensor]:
    """
    Load processed graphs and target adhesion energies.
    """
    if not DATA_PATH.exists():
        raise DataError(f"Processed graphs not found at {DATA_PATH}. Run graph_build.py first.")
    
    logger.info(f"Loading graphs from {DATA_PATH}...")
    try:
        data = torch.load(DATA_PATH, weights_only=False)
        # Expecting a list of Data objects or a Batch object with targets
        # Assuming data is a dict or object with 'graphs' and 'targets' or similar structure
        # Based on T024 output: PyG Data objects. 
        # We assume the saved file contains a list of (graph, target) or a structured dataset.
        # For robustness, we handle the common case of a list of Data objects where y is the target.
        
        if isinstance(data, dict):
            graphs = data.get('graphs', data.get('data', []))
            targets = data.get('targets', data.get('y', None))
        elif isinstance(data, list):
            # If it's a list of Data objects, we need to separate them
            # Assuming each Data object has a 'y' attribute for target
            graphs = []
            targets = []
            for item in data:
                if hasattr(item, 'y'):
                    targets.append(item.y)
                    # Create a new Data object without y for the graph list if needed, 
                    # or keep the full object. For training, we usually pass the full batch.
                    # Here we assume we need to reconstruct a dataset.
                    graphs.append(item)
            if targets:
                targets = torch.cat(targets, dim=0)
        else:
            # Fallback: assume it's a Batch object or similar
            graphs = data
            targets = data.y if hasattr(data, 'y') else None

        if targets is None:
            raise DataError("Targets (adhesion energy) not found in processed graphs file.")
        
        logger.info(f"Loaded {len(graphs) if isinstance(graphs, list) else 'batch'} graphs with targets.")
        return graphs, targets
    except Exception as e:
        raise DataError(f"Failed to load graphs: {e}")

def prepare_data(graphs: List[Any], targets: torch.Tensor) -> Tuple[torch.utils.data.DataLoader, torch.utils.data.DataLoader, torch.utils.data.DataLoader]:
    """
    Split data into train, validation, and test sets.
    """
    n = len(graphs)
    indices = list(range(n))
    
    # Simple deterministic split
    train_end = int(n * TRAIN_RATIO)
    val_end = train_end + int(n * VALID_RATIO)
    
    train_indices = indices[:train_end]
    val_indices = indices[train_end:val_end]
    test_indices = indices[val_end:]
    
    # Create subsets
    # Assuming graphs is a list of Data objects and targets is a tensor
    # We need to create a custom dataset or use Subset
    from torch.utils.data import TensorDataset, DataLoader, Subset
    
    # Reconstruct tensors for Subset if necessary, or just index
    # If graphs is a list, we can use Subset with a custom dataset wrapper
    class GraphDataset:
        def __init__(self, graphs_list, targets_tensor):
            self.graphs = graphs_list
            self.targets = targets_tensor
        def __len__(self):
            return len(self.graphs)
        def __getitem__(self, idx):
            return self.graphs[idx], self.targets[idx]

    dataset = GraphDataset(graphs, targets)
    
    train_dataset = Subset(dataset, train_indices)
    val_dataset = Subset(dataset, val_indices)
    test_dataset = Subset(dataset, test_indices)
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)
    
    return train_loader, val_loader, test_loader

def train_epoch(model: GATModel, loader: torch.utils.data.DataLoader, optimizer: optim.Optimizer, device: torch.device) -> float:
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    for batch_graphs, batch_targets in loader:
        optimizer.zero_grad()
        # Handle device transfer
        if isinstance(batch_graphs, list):
            # If it's a list of Data objects, we need to collate them properly
            # PyG's default collate function expects a list of Data objects
            # We assume the DataLoader handles this via collate_fn if passed, 
            # otherwise we might need to stack or batch manually.
            # For simplicity, assuming batch_graphs is already a Batch object or compatible
            # If batch_graphs is a list, we might need to use pyg.loader.DataLoader or similar
            # Here we assume the DataLoader's default collate works or we pass a Batch object.
            # If batch_graphs is a list of Data, we might need to stack them if possible or use a custom collate.
            # Let's assume batch_graphs is a Batch object or a list that PyG can handle.
            # If it fails, we might need to use torch_geometric.data.Batch.from_data_list
            from torch_geometric.data import Batch
            if isinstance(batch_graphs[0], torch_geometric.data.Data):
                batch_graphs = Batch.from_data_list(batch_graphs)
        
        batch_graphs = batch_graphs.to(device)
        batch_targets = batch_targets.to(device)
        
        outputs = model(batch_graphs)
        loss = nn.MSELoss()(outputs, batch_targets)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    
    return total_loss / len(loader)

def evaluate(model: GATModel, loader: torch.utils.data.DataLoader, device: torch.device) -> float:
    """Evaluate model on a dataset."""
    model.eval()
    total_loss = 0.0
    with torch.no_grad():
        for batch_graphs, batch_targets in loader:
            if isinstance(batch_graphs, list):
                from torch_geometric.data import Batch
                if isinstance(batch_graphs[0], torch_geometric.data.Data):
                    batch_graphs = Batch.from_data_list(batch_graphs)
            
            batch_graphs = batch_graphs.to(device)
            batch_targets = batch_targets.to(device)
            
            outputs = model(batch_graphs)
            loss = nn.MSELoss()(outputs, batch_targets)
            total_loss += loss.item()
    
    return total_loss / len(loader)

def save_checkpoint(model: nn.Module, optimizer: optim.Optimizer, epoch: int, path: Path):
    """Save a training checkpoint."""
    path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
    }
    torch.save(checkpoint, path)
    logger.info(f"Checkpoint saved to {path}")

def main():
    """Main training loop with checkpointing and timeout logic."""
    set_seed(SEED)
    device = torch.device('cpu') # CPU-only constraint
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Load data
    graphs, targets = load_graphs_and_targets()
    train_loader, val_loader, test_loader = prepare_data(graphs, targets)
    
    # Initialize model
    model = create_gat_model(
        in_channels=6, # Assuming 6 features (atom type, bond order, etc.) - adjust if needed
        hidden_channels=HIDDEN_DIM,
        out_channels=1,
        num_layers=3,
        num_heads=NUM_HEADS,
        dropout=DROPOUT
    ).to(device)
    
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    # Training setup
    start_time = time.time()
    best_val_loss = float('inf')
    best_model_state = None
    
    # Set signal handler for hard timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(HARD_TIMEOUT)
    
    try:
        logger.info(f"Starting training for {EPOCHS} epochs...")
        for epoch in range(1, EPOCHS + 1):
            check_timeout_elapsed(start_time)
            
            train_loss = train_epoch(model, train_loader, optimizer, device)
            val_loss = evaluate(model, val_loader, device)
            
            scheduler.step(val_loss)
            
            logger.info(f"Epoch {epoch}/{EPOCHS} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
            
            # Save best model
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_model_state = model.state_dict().copy()
                logger.info(f"New best model saved with Val Loss: {best_val_loss:.4f}")
            
            # Checkpointing logic (T027)
            # 1. Periodic checkpointing every N epochs
            if epoch % CHECKPOINT_INTERVAL_EPOCHS == 0:
                checkpoint_path = CHECKPOINT_DIR / f"checkpoint_{epoch}.pt"
                save_checkpoint(model, optimizer, epoch, checkpoint_path)
            
            # 2. Soft timeout checkpointing (T027/T029)
            if check_soft_timeout_and_checkpoint(start_time, epoch, model, optimizer):
                break
        
        # Final save
        if best_model_state is not None:
            model.load_state_dict(best_model_state)
            MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), MODEL_PATH)
            logger.info(f"Best model saved to {MODEL_PATH}")
        
        # Log performance
        log_performance(LOG_PATH, start_time)
        
    except TrainingTimeoutError as e:
        logger.error(str(e))
        # Ensure we have a checkpoint if we timed out
        checkpoint_path = CHECKPOINT_DIR / f"checkpoint_{epoch}.pt"
        save_checkpoint(model, optimizer, epoch, checkpoint_path)
        raise
    finally:
        signal.alarm(0) # Cancel the alarm

if __name__ == "__main__":
    main()