import os
import sys
import json
import time
import signal
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

import torch
import torch.nn as nn
import torch.optim as optim
from torch_geometric.data import DataLoader
import numpy as np

# Local imports matching the API surface
from models.gat import create_gat_model, GATModel
from utils.exceptions import TrainingTimeoutError, DataError
from utils.logger import PerformanceLogger, log_performance
from utils.seed_utils import set_seed

# Constants for timeout logic (from task description)
SOFT_TIMEOUT_SECONDS = 4.5 * 3600  # 4.5 hours
HARD_TIMEOUT_SECONDS = 6.0 * 3600  # 6 hours

# Paths
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = Path("results")
CHECKPOINT_DIR = RESULTS_DIR
MODEL_OUTPUT = RESULTS_DIR / "model.pt"

# Global start time for timeout checks
_start_time: Optional[float] = None

def _timeout_handler(signum: int, frame: Any) -> None:
    """Signal handler for timeout. Raises TrainingTimeoutError."""
    raise TrainingTimeoutError("Training exceeded the 6-hour hard limit.")

def timeout_handler() -> None:
    """
    Initialize the timeout signal handler for the training process.
    This sets up a SIGALRM handler that will raise TrainingTimeoutError
    if the process runs longer than HARD_TIMEOUT_SECONDS.
    """
    global _start_time
    _start_time = time.time()
    
    # Only set signal handler on Unix-like systems
    if sys.platform != "win32":
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(int(HARD_TIMEOUT_SECONDS))
    else:
        # On Windows, we rely on manual checks in the loop
        pass

def check_timeout_elapsed() -> None:
    """
    Check if the hard timeout has been exceeded.
    Raises TrainingTimeoutError if so.
    """
    if _start_time is None:
        return
    
    elapsed = time.time() - _start_time
    if elapsed > HARD_TIMEOUT_SECONDS:
        raise TrainingTimeoutError(f"Training exceeded hard limit ({HARD_TIMEOUT_SECONDS}s). Elapsed: {elapsed:.1f}s")

def check_soft_timeout_and_checkpoint(
    epoch: int,
    model: GATModel,
    optimizer: optim.Optimizer,
    scheduler: Optional[optim.lr_scheduler._LRScheduler] = None
) -> bool:
    """
    Check if the soft timeout (4.5h) has been exceeded but hard limit (6h) not yet.
    If so, triggers checkpointing and returns True to indicate a checkpoint was saved.
    Returns False if no checkpoint was needed.
    """
    if _start_time is None:
        return False
    
    elapsed = time.time() - _start_time
    
    if SOFT_TIMEOUT_SECONDS < elapsed <= HARD_TIMEOUT_SECONDS:
        # Trigger checkpointing logic (T025)
        checkpoint_path = CHECKPOINT_DIR / f"checkpoint_{epoch}.pt"
        save_checkpoint(model, optimizer, epoch, scheduler, str(checkpoint_path))
        return True
    
    return False

def load_graphs_and_targets(graphs_path: Path) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Load processed graphs and target adhesion energies.
    Returns: (edge_index, edge_attr, x, y) or similar structure depending on graphs.pt format.
    For this implementation, we assume graphs.pt contains a list of Data objects.
    """
    if not graphs_path.exists():
        raise FileNotFoundError(f"Graphs file not found: {graphs_path}")
    
    data_list = torch.load(graphs_path)
    # Assuming data_list is a list of torch_geometric.data.Data objects
    # We need to separate features and targets
    # For simplicity, we assume the target 'y' is stored in each Data object
    # and features are in 'x', edge_index in 'edge_index'
    
    # This is a simplified loader; in reality, we might need to collate
    # For now, we return the list of data objects and assume the DataLoader handles it
    return data_list

def prepare_data(data_list: List, batch_size: int = 32) -> Tuple[DataLoader, DataLoader]:
    """
    Split data into train and test sets (80/20) and create DataLoaders.
    """
    np.random.seed(42) # Ensure reproducibility
    indices = np.random.permutation(len(data_list))
    split_idx = int(0.8 * len(data_list))
    
    train_indices = indices[:split_idx]
    test_indices = indices[split_idx:]
    
    train_data = [data_list[i] for i in train_indices]
    test_data = [data_list[i] for i in test_indices]
    
    train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_data, batch_size=batch_size, shuffle=False)
    
    return train_loader, test_loader

def train_epoch(
    model: GATModel,
    loader: DataLoader,
    optimizer: optim.Optimizer,
    device: torch.device
) -> float:
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        
        # Forward pass
        out = model(batch.x, batch.edge_index, batch.edge_attr)
        loss = nn.MSELoss()(out.squeeze(), batch.y)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item() * batch.num_graphs
    
    return total_loss / len(loader.dataset)

def evaluate(
    model: GATModel,
    loader: DataLoader,
    device: torch.device
) -> float:
    """Evaluate model on a loader."""
    model.eval()
    total_loss = 0.0
    
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index, batch.edge_attr)
            loss = nn.MSELoss()(out.squeeze(), batch.y)
            total_loss += loss.item() * batch.num_graphs
    
    return total_loss / len(loader.dataset)

def save_checkpoint(
    model: GATModel,
    optimizer: optim.Optimizer,
    epoch: int,
    scheduler: Optional[optim.lr_scheduler._LRScheduler],
    path: str
) -> None:
    """Save training state to a checkpoint file (T025)."""
    state = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'scheduler_state_dict': scheduler.state_dict() if scheduler else None,
    }
    torch.save(state, path)
    print(f"Checkpoint saved to {path}")

def main():
    """
    Main training loop with timeout logic.
    Implements T026 (training loop) and T027 (timeout logic).
    """
    global _start_time
    set_seed(42)
    
    device = torch.device("cpu") # CPU-only constraint
    
    # Paths
    graphs_path = PROCESSED_DIR / "graphs.pt"
    if not graphs_path.exists():
        raise DataError(f"Processed graphs not found at {graphs_path}. Run graph_build.py first.")
    
    # Load data
    print("Loading graphs and targets...")
    data_list = load_graphs_and_targets(graphs_path)
    
    if len(data_list) < 100:
        raise DataError(f"Insufficient data for training: {len(data_list)} rows. Minimum 100 required.")
    
    # Prepare loaders
    train_loader, test_loader = prepare_data(data_list, batch_size=32)
    
    # Initialize model
    model = create_gat_model(input_dim=data_list[0].x.shape[1], hidden_dim=64, output_dim=1)
    model = model.to(device)
    
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.1)
    
    # Setup logging
    logger = PerformanceLogger()
    logger.start()
    
    # Initialize timeout logic (T027)
    timeout_handler()
    
    # Training parameters
    epochs = 100 # Default, might be cut short by timeout
    best_loss = float('inf')
    
    print(f"Starting training on {device}...")
    print(f"Soft timeout: {SOFT_TIMEOUT_SECONDS/3600:.1f}h, Hard timeout: {HARD_TIMEOUT_SECONDS/3600:.1f}h")
    
    try:
        for epoch in range(epochs):
            # Check hard timeout at start of each epoch
            check_timeout_elapsed()
            
            # Train one epoch
            train_loss = train_epoch(model, train_loader, optimizer, device)
            test_loss = evaluate(model, test_loader, device)
            
            # Log performance
            log_performance(
                logger,
                {"epoch": epoch, "train_loss": train_loss, "test_loss": test_loss}
            )
            
            # Check soft timeout and checkpoint if needed (T027 -> T025)
            if check_soft_timeout_and_checkpoint(epoch, model, optimizer, scheduler):
                print(f"Soft timeout reached at epoch {epoch}. Checkpoint saved. Stopping training.")
                break
            
            # Update scheduler
            scheduler.step()
            
            # Save best model
            if test_loss < best_loss:
                best_loss = test_loss
                torch.save(model.state_dict(), str(MODEL_OUTPUT))
                print(f"New best model saved with loss: {best_loss:.4f}")
            
            print(f"Epoch {epoch}: Train Loss: {train_loss:.4f}, Test Loss: {test_loss:.4f}")
            
    except TrainingTimeoutError as e:
        print(f"TIMEOUT ERROR: {e}")
        # Ensure final checkpoint is saved before failing
        final_checkpoint = CHECKPOINT_DIR / "checkpoint_final_timeout.pt"
        save_checkpoint(model, optimizer, epoch, scheduler, str(final_checkpoint))
        raise
    finally:
        # Stop logging
        logger.stop()
        log_performance(logger, {"status": "finished", "best_test_loss": best_loss})
        
        # Final checkpoint if not already saved
        if not MODEL_OUTPUT.exists():
            torch.save(model.state_dict(), str(MODEL_OUTPUT))
        
        print("Training complete.")

if __name__ == "__main__":
    main()