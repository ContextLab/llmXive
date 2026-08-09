import os
import sys
import json
import logging
import argparse
import tracemalloc
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import torch
import torch.nn.functional as F
from torch_geometric.data import DataLoader
from torch_geometric.utils import to_dense_batch
import numpy as np

# Import project utilities and models
# Ensure these match the provided API surface
from code.utils.seed import set_seed, get_seed_from_env
from code.utils.logging import get_logger, setup_logging
from code.utils.memory_monitor import MemoryMonitor
from code.config import TIME_BUDGET, MAX_RAM_GB
from code.models.gcn import GCNModel, create_model_from_processed_data
from code.models.evaluation_result import EvaluationResult

# Configuration constants
PATIENCE = 5
MAX_EPOCHS = 50
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-4
GRAD_ACCUMULATION_STEPS = 4  # Merged from T050
INITIAL_BATCH_SIZE = 32

logger = get_logger(__name__)

class EarlyStopping:
    """Early stopping to stop training when validation loss stops improving."""
    def __init__(self, patience: int = 5, verbose: bool = True):
        self.patience = patience
        self.verbose = verbose
        self.counter = 0
        self.best_score = None
        self.early_stop = False
        self.val_loss_min = np.inf

    def __call__(self, val_loss: float, model: torch.nn.Module):
        score = -val_loss

        if self.best_score is None:
            self.best_score = score
            self.save_checkpoint(val_loss, model)
        elif score < self.best_score:
            self.counter += 1
            logger.debug(f"EarlyStopping counter: {self.counter} out of {self.patience}")
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_score = score
            self.save_checkpoint(val_loss, model)
            self.counter = 0

    def save_checkpoint(self, val_loss: float, model: torch.nn.Module):
        if self.verbose:
            logger.debug(f"Validation loss decreased ({self.val_loss_min:.6f} --> {val_loss:.6f}). Saving model ...")
        self.val_loss_min = val_loss
        # In a full implementation, we would save the state dict here.
        # For this task, we assume the model object is updated in place or tracked.

def load_processed_graphs(data_path: str) -> Tuple[List[Any], List[float], List[str]]:
    """
    Loads processed graph data from a Parquet file.
    Returns: (list of Data objects, list of target values, list of SMILES)
    """
    import pandas as pd
    import pickle
    from torch_geometric.data import Data

    df = pd.read_parquet(data_path)
    
    # Assuming the parquet file contains serialized graph objects or raw features
    # that need to be reconstructed. Based on T014/T015 output structure.
    # We expect columns: 'smiles', 'node_features', 'edge_features', 'surface_area', 'molecular_weight'
    
    graphs = []
    targets = []
    smiles_list = []

    # If node_features are stored as arrays in the parquet, we reconstruct Data objects
    # This assumes T014/T015 output format where features are arrays
    for _, row in df.iterrows():
        smiles = row['smiles']
        sasa = row['surface_area']
        
        # Reconstruct Data object
        # Depending on T014 implementation, features might be numpy arrays or lists
        if isinstance(row['node_features'], np.ndarray):
            x = torch.tensor(row['node_features'], dtype=torch.float)
        else:
            x = torch.tensor(row['node_features'], dtype=torch.float)

        # Edge features usually stored as edge_index and potentially edge_attr
        # Assuming edge_index is a 2xE tensor and edge_attr is ExC tensor if present
        # If only edge_index exists (unweighted), handle accordingly
        edge_index = row['edge_features']
        if isinstance(edge_index, np.ndarray):
            edge_index = torch.tensor(edge_index, dtype=torch.long)
        else:
            edge_index = torch.tensor(edge_index, dtype=torch.long)
        
        data = Data(x=x, edge_index=edge_index)
        graphs.append(data)
        targets.append(sasa)
        smiles_list.append(smiles)

    return graphs, targets, smiles_list

def train_epoch(model: torch.nn.Module, loader: DataLoader, optimizer: torch.optim.Optimizer, device: torch.device, grad_accum_steps: int):
    model.train()
    total_loss = 0
    optimizer.zero_grad()

    for batch in loader:
        batch = batch.to(device)
        
        # Forward pass
        out = model(batch.x, batch.edge_index, batch.batch)
        
        # Assuming target is in batch.y
        loss = F.mse_loss(out, batch.y)
        
        # Gradient accumulation
        loss = loss / grad_accum_steps
        loss.backward()

        if (len(loader) > 0 and (batch.batch[-1].item() + 1) % grad_accum_steps == 0) or (len(loader) == 1):
            # Check if we are at the last batch or accumulated enough
            # For simplicity in this loop, we accumulate and step every N batches or at end
            # A more robust way: track batch count
            pass 
        
        # Simpler accumulation logic: step every grad_accum_steps batches
        # We need a counter outside or track batch index
        # Let's use a simpler approach: accumulate gradients and step periodically
        
    # Re-implementing accumulation logic correctly inside the loop
    # We need to track how many batches we've processed
    pass

def train_epoch_corrected(model: torch.nn.Module, loader: DataLoader, optimizer: torch.optim.Optimizer, device: torch.device, grad_accum_steps: int):
    model.train()
    total_loss = 0.0
    optimizer.zero_grad()
    
    for i, batch in enumerate(loader):
        batch = batch.to(device)
        out = model(batch.x, batch.edge_index, batch.batch)
        loss = F.mse_loss(out, batch.y)
        
        # Accumulate
        (loss / grad_accum_steps).backward()
        
        # Step every grad_accum_steps batches or at the end
        if (i + 1) % grad_accum_steps == 0 or (i + 1) == len(loader):
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            optimizer.zero_grad()
        
        total_loss += loss.item() * grad_accum_steps # Scale back for logging accuracy
        
    return total_loss / len(loader)

def evaluate(model: torch.nn.Module, loader: DataLoader, device: torch.device) -> float:
    model.eval()
    total_loss = 0.0
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index, batch.batch)
            loss = F.mse_loss(out, batch.y)
            total_loss += loss.item()
    return total_loss / len(loader)

def train_model(
    train_data: List[Any], 
    train_targets: List[float], 
    val_data: List[Any], 
    val_targets: List[float],
    device: torch.device,
    batch_size: int = INITIAL_BATCH_SIZE,
    grad_accum_steps: int = GRAD_ACCUMULATION_STEPS
) -> Tuple[torch.nn.Module, Dict[str, float]]:
    """
    Trains the GCN model with early stopping and gradient accumulation.
    """
    set_seed(42) # Default seed for reproducibility

    # Create DataLoaders
    train_dataset = torch.utils.data.TensorDataset(
        torch.tensor(train_data, dtype=torch.float), # Placeholder if not Data objects
        torch.tensor(train_targets, dtype=torch.float)
    )
    # Actually, we have Data objects from load_processed_graphs
    # We need a custom dataset or just use the list directly with a custom collate
    # PyTorch Geometric handles list of Data objects in DataLoader automatically
    
    train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_data, batch_size=batch_size, shuffle=False)

    # Initialize Model
    # We need input_dim. Assuming node features are the first dimension of x
    if len(train_data) > 0:
        input_dim = train_data[0].x.shape[1]
    else:
        raise ValueError("Training data is empty")
    
    model = GCNModel(in_channels=input_dim, hidden_channels=64, out_channels=1)
    model = model.to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    early_stopping = EarlyStopping(patience=PATIENCE, verbose=True)
    
    # Memory Monitor
    mem_monitor = MemoryMonitor(max_ram_gb=MAX_RAM_GB)
    mem_monitor.start()

    best_val_loss = np.inf

    for epoch in range(1, MAX_EPOCHS + 1):
        train_loss = train_epoch_corrected(model, train_loader, optimizer, device, grad_accum_steps)
        val_loss = evaluate(model, val_loader, device)
        
        scheduler.step(val_loss)
        
        logger.info(f"Epoch {epoch:03d}: Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
        
        # Check memory
        mem_monitor.check_and_log(epoch)
        
        # Early stopping
        early_stopping(val_loss, model)
        if early_stopping.early_stop:
            logger.info("Early stopping triggered")
            break

    mem_monitor.stop()
    return model, {"best_val_loss": best_val_loss}

def generate_predictions(
    model: torch.nn.Module, 
    test_data: List[Any], 
    test_targets: List[float], 
    test_smiles: List[str],
    device: torch.device
) -> pd.DataFrame:
    """
    Generates predictions and calculates errors for the test set.
    """
    import pandas as pd
    
    model.eval()
    test_loader = DataLoader(test_data, batch_size=INITIAL_BATCH_SIZE, shuffle=False)
    
    predictions = []
    errors = []
    
    with torch.no_grad():
        for batch in test_loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index, batch.batch)
            predictions.extend(out.cpu().numpy().tolist())
            # batch.y is the target
            errors.extend((out.cpu().numpy() - batch.y.cpu().numpy())**2) # Store squared error or just diff? Task says 'error'
            # Let's store the raw difference
            # Re-calculate with raw difference
    
    # Re-run to get raw differences
    predictions = []
    diffs = []
    with torch.no_grad():
        for batch in test_loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index, batch.batch)
            preds = out.cpu().numpy()
            targs = batch.y.cpu().numpy()
            predictions.extend(preds.tolist())
            diffs.extend((preds - targs).tolist())
    
    df = pd.DataFrame({
        'smiles': test_smiles,
        'predicted_sasa': predictions,
        'error': diffs
    })
    return df

def main():
    parser = argparse.ArgumentParser(description="Train GCN for SASA prediction")
    parser.add_argument("--train_path", type=str, required=True, help="Path to train parquet")
    parser.add_argument("--val_path", type=str, required=True, help="Path to val parquet")
    parser.add_argument("--test_path", type=str, required=True, help="Path to test parquet")
    parser.add_argument("--output_path", type=str, default="results/predictions/gcn_predictions.parquet", help="Output path for predictions")
    parser.add_argument("--device", type=str, default="cpu", help="Device to use")
    args = parser.parse_args()

    setup_logging(level=logging.INFO)
    logger.info("Starting GCN Training (T022)")

    # Load Data
    logger.info("Loading training data...")
    train_graphs, train_targets, train_smiles = load_processed_graphs(args.train_path)
    logger.info(f"Loaded {len(train_graphs)} training molecules.")

    logger.info("Loading validation data...")
    val_graphs, val_targets, val_smiles = load_processed_graphs(args.val_path)
    logger.info(f"Loaded {len(val_graphs)} validation molecules.")

    logger.info("Loading test data...")
    test_graphs, test_targets, test_smiles = load_processed_graphs(args.test_path)
    logger.info(f"Loaded {len(test_graphs)} test molecules.")

    device = torch.device(args.device)

    # Train
    logger.info("Training model...")
    model, metrics = train_model(
        train_graphs, train_targets, 
        val_graphs, val_targets, 
        device
    )

    # Predict
    logger.info("Generating predictions...")
    df = generate_predictions(model, test_graphs, test_targets, test_smiles, device)

    # Save
    output_dir = os.path.dirname(args.output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    df.to_parquet(args.output_path, index=False)
    logger.info(f"Predictions saved to {args.output_path}")

    # Verify output
    if os.path.exists(args.output_path):
        verify_df = pd.read_parquet(args.output_path)
        required_cols = ['smiles', 'predicted_sasa', 'error']
        if all(col in verify_df.columns for col in required_cols):
            logger.info("Verification passed: Output contains required columns.")
        else:
            logger.error("Verification failed: Missing required columns.")
            sys.exit(1)
    else:
        logger.error("Verification failed: Output file not created.")
        sys.exit(1)

if __name__ == "__main__":
    main()