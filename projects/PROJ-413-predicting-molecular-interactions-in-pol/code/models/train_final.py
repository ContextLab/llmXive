"""
T028: Train final model and save to results/model.pt.

This script loads the curated graphs, initializes the GAT model,
runs the full training loop (handling timeouts and checkpoints as per T026/T027),
and saves the final trained model to results/model.pt.
"""
import os
import sys
import time
import signal
import json
import logging
from pathlib import Path
from typing import Tuple, Dict, Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from torch.utils.data import DataLoader, TensorDataset

# Import project utilities and models
from utils.seed_utils import set_seed
from utils.exceptions import DataError, TrainingTimeoutError
from utils.logger import PerformanceLogger, log_performance
from models.gat import GATModel, create_gat_model
from data.graph_build import save_graphs  # Re-use if needed, though we load .pt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SEED = 42
HIDDEN_DIM = 64
NUM_LAYERS = 3
DROPOUT = 0.5
LEARNING_RATE = 0.01
BATCH_SIZE = 32
NUM_EPOCHS = 100  # Maximum epochs, actual stop depends on convergence/timeout
SOFT_TIMEOUT_HOURS = 4.5
HARD_TIMEOUT_HOURS = 6.0
CHECKPOINT_INTERVAL = 10

def timeout_handler(signum, frame):
    """Signal handler for hard timeout."""
    raise TrainingTimeoutError(f"Hard timeout of {HARD_TIMEOUT_HOURS} hours exceeded.")

def check_timeout_elapsed(start_time: float) -> bool:
    """Check if hard timeout has been reached."""
    elapsed = time.time() - start_time
    return elapsed > (HARD_TIMEOUT_HOURS * 3600)

def check_soft_timeout_and_checkpoint(start_time: float, epoch: int, model: GATModel, checkpoint_path: Path) -> bool:
    """
    Check if soft timeout is reached.
    If 4.5h < elapsed <= 6h, save checkpoint and continue (or stop if > 6h handled by hard timeout).
    Returns True if we should stop training (soft limit reached and saved checkpoint).
    """
    elapsed = time.time() - start_time
    if elapsed > (SOFT_TIMEOUT_HOURS * 3600):
        logger.warning(f"Soft timeout ({SOFT_TIMEOUT_HOURS}h) reached at epoch {epoch}. Saving checkpoint.")
        # Save checkpoint before potentially hitting hard timeout
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': None, # Simplified for this script
            'loss': None
        }, checkpoint_path)
        # If we are already past hard timeout, the hard timeout handler will catch it next
        # But per T027, if > 4.5h we checkpoint. If > 6h we fail.
        # We return False to let the loop continue until hard timeout catches us,
        # unless we want to stop immediately at soft timeout. T027 says "trigger checkpointing if 4.5h < runtime <= 6h".
        # It implies we keep going until 6h.
    return False

def load_graphs_and_targets(graphs_path: Path) -> Tuple[DataLoader, DataLoader]:
    """Load graphs and targets from data/processed/graphs.pt."""
    if not graphs_path.exists():
        raise DataError(f"Graphs file not found: {graphs_path}")

    # Assuming graphs.pt contains a list of Data objects and a separate targets list or they are embedded
    # Based on T024/T026 context, we expect a structured load.
    # Let's assume the file saves a dict: {'graphs': [...], 'targets': [...]}
    try:
        checkpoint = torch.load(graphs_path, map_location='cpu')
        graphs = checkpoint.get('graphs', [])
        targets = checkpoint.get('targets', [])
    except Exception as e:
        logger.error(f"Failed to load graphs: {e}")
        raise DataError(f"Invalid graphs file format: {e}")

    if not graphs or not targets:
        raise DataError("Empty graphs or targets loaded.")

    # Convert to tensors if necessary (assuming targets are float)
    # Assuming graphs are already Data objects
    # Split 80/20
    n = len(graphs)
    indices = list(range(n))
    # Simple deterministic shuffle based on seed
    set_seed(SEED)
    import random
    random.shuffle(indices)

    split_idx = int(0.8 * n)
    train_indices = indices[:split_idx]
    test_indices = indices[split_idx:]

    train_graphs = [graphs[i] for i in train_indices]
    train_targets = [targets[i] for i in train_indices]
    test_graphs = [graphs[i] for i in test_indices]
    test_targets = [targets[i] for i in test_indices]

    # Create DataLoader-compatible datasets
    # Since Data objects are custom, we might need a custom collate or just list iteration
    # For simplicity in this script, we'll iterate manually or use a simple wrapper
    # Let's create a simple dataset class
    class SimpleGraphDataset(torch.utils.data.Dataset):
        def __init__(self, graphs, targets):
            self.graphs = graphs
            self.targets = torch.tensor(targets, dtype=torch.float32)
        def __len__(self):
            return len(self.graphs)
        def __getitem__(self, idx):
            return self.graphs[idx], self.targets[idx]

    train_dataset = SimpleGraphDataset(train_graphs, train_targets)
    test_dataset = SimpleGraphDataset(test_graphs, test_targets)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

    return train_loader, test_loader

def train_epoch(model: GATModel, loader: DataLoader, optimizer: torch.optim.Optimizer, device: torch.device) -> float:
    model.train()
    total_loss = 0.0
    for batch_graphs, batch_targets in loader:
        # batch_graphs is a list of Data objects
        # We need to batch them properly for PyG
        # If they are already batched Data objects, fine. If list, use Batch.from_data_list
        from torch_geometric.data import Batch
        if isinstance(batch_graphs, list):
            batch = Batch.from_data_list(batch_graphs)
        else:
            batch = batch_graphs

        batch_targets = batch_targets.to(device)

        optimizer.zero_grad()
        out = model(batch)
        loss = F.mse_loss(out, batch_targets)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * len(batch_targets)

    return total_loss / len(loader.dataset)

def evaluate(model: GATModel, loader: DataLoader, device: torch.device) -> float:
    model.eval()
    total_loss = 0.0
    with torch.no_grad():
        for batch_graphs, batch_targets in loader:
            from torch_geometric.data import Batch
            if isinstance(batch_graphs, list):
                batch = Batch.from_data_list(batch_graphs)
            else:
                batch = batch_graphs

            batch_targets = batch_targets.to(device)
            out = model(batch)
            loss = F.mse_loss(out, batch_targets)
            total_loss += loss.item() * len(batch_targets)
    return total_loss / len(loader.dataset)

def save_checkpoint(epoch: int, model: GATModel, path: Path):
    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
    }, path)
    logger.info(f"Checkpoint saved to {path}")

def main():
    logger.info("Starting T028: Final Model Training")

    # Setup paths
    graphs_path = PROJECT_ROOT / "data" / "processed" / "graphs.pt"
    output_path = PROJECT_ROOT / "results" / "model.pt"
    checkpoint_dir = PROJECT_ROOT / "results"

    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Setup device
    device = torch.device('cpu') # CPU-only constraint
    logger.info(f"Using device: {device}")

    # Setup seed
    set_seed(SEED)

    # Setup model
    # Determine input dim from data if possible, otherwise assume a standard (e.g., 64 or derived from graph_build)
    # Since we don't have the exact input dim here, we'll assume the GATModel constructor handles it or we pass a default.
    # Looking at T021, GATModel is created with create_gat_model.
    # Let's assume input_dim is 64 (common default) or we try to infer from the first graph.
    try:
        # Quick peek to get input dim
        checkpoint = torch.load(graphs_path, map_location='cpu')
        first_graph = checkpoint['graphs'][0]
        input_dim = first_graph.x.shape[1] if hasattr(first_graph, 'x') and first_graph.x is not None else 64
        logger.info(f"Inferred input dimension: {input_dim}")
    except Exception as e:
        logger.warning(f"Could not infer input dim, defaulting to 64. Error: {e}")
        input_dim = 64

    model = create_gat_model(input_dim=input_dim, hidden_dim=HIDDEN_DIM, num_layers=NUM_LAYERS, dropout=DROPOUT)
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    # Load data
    try:
        train_loader, test_loader = load_graphs_and_targets(graphs_path)
        logger.info(f"Loaded data. Train size: {len(train_loader.dataset)}, Test size: {len(test_loader.dataset)}")
    except DataError as e:
        logger.error(f"Data loading failed: {e}")
        raise

    # Training Loop
    start_time = time.time()
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(HARD_TIMEOUT_HOURS * 3600)) # Set hard alarm

    best_loss = float('inf')

    try:
        for epoch in range(1, NUM_EPOCHS + 1):
            if check_timeout_elapsed(start_time):
                raise TrainingTimeoutError("Hard timeout exceeded.")

            # Soft timeout check
            check_soft_timeout_and_checkpoint(start_time, epoch, model, checkpoint_dir / f"checkpoint_{epoch}.pt")

            train_loss = train_epoch(model, train_loader, optimizer, device)
            test_loss = evaluate(model, test_loader, device)

            logger.info(f"Epoch {epoch}: Train Loss: {train_loss:.4f}, Test Loss: {test_loss:.4f}")

            if test_loss < best_loss:
                best_loss = test_loss
                # Save best model state separately if needed, but we save final at end
                pass

            # Periodic checkpoint
            if epoch % CHECKPOINT_INTERVAL == 0:
                save_checkpoint(epoch, model, checkpoint_dir / f"checkpoint_{epoch}.pt")

    except TrainingTimeoutError as e:
        logger.error(f"Training stopped due to timeout: {e}")
        # Ensure we have a checkpoint if we stopped early
        save_checkpoint(epoch, model, checkpoint_dir / "checkpoint_final_timeout.pt")
        raise
    finally:
        signal.alarm(0) # Cancel alarm

    # Save final model
    torch.save(model.state_dict(), output_path)
    logger.info(f"Final model saved to {output_path}")

    # Log performance
    elapsed = time.time() - start_time
    log_performance({
        "task": "T028",
        "total_time_seconds": elapsed,
        "final_test_loss": test_loss,
        "best_test_loss": best_loss
    })

    logger.info("T028 completed successfully.")

if __name__ == "__main__":
    main()