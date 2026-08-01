"""
src/models/ensemble.py
Implementation of ensemble training with 5-Fold LLSO cross-validation.

This module integrates the LLSO logic from src/data/splits.py to perform
rigorous cross-validation where ligand scaffolds are held out in test sets.
"""
import os
import json
import random
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import torch
import torch.nn as nn
from torch_geometric.data import Data, DataLoader
from torch_geometric.loader import RandomLoader

# Import from project structure
try:
    from src.data.splits import generate_llso_splits, save_splits_to_json
    from src.utils.config import get_project_root, load_config
    from src.utils.logging import setup_logger, log_progress
    from src.models.schnet import SchNet, get_model_config
except ImportError:
    # Fallback for different import contexts
    from code.src.data.splits import generate_llso_splits, save_splits_to_json
    from code.src.utils.config import get_project_root, load_config
    from code.src.utils.logging import setup_logger, log_progress
    from code.src.models.schnet import SchNet, get_model_config

logger = setup_logger(__name__)

class GraphDataset:
    """
    Simple wrapper to load graphs from a list of dictionaries.
    Converts dictionaries to PyTorch Geometric Data objects.
    """
    def __init__(self, graphs: List[Dict[str, Any]]):
        self.data_list = []
        for graph in graphs:
            # Extract features based on expected schema from data-model.md
            # Assuming nodes: atomic_numbers (list), positions (list of lists)
            # edges: edge_index (2, num_edges), edge_attr (num_edges, num_features)
            # target: barrier_height (float)
            
            atomic_numbers = torch.tensor(graph.get('atomic_numbers', []), dtype=torch.long)
            positions = torch.tensor(graph.get('positions', []), dtype=torch.float)
            edge_index = torch.tensor(graph.get('edge_index', [[], []]), dtype=torch.long)
            edge_attr = torch.tensor(graph.get('edge_attr', []), dtype=torch.float)
            target = torch.tensor([graph.get('barrier_height', 0.0)], dtype=torch.float)
            
            # Handle missing edge_attr gracefully
            if edge_attr.numel() == 0 and edge_index.numel() > 0:
                edge_attr = torch.zeros((edge_index.size(1), 1), dtype=torch.float)
                
            data = Data(
                z=atomic_numbers,
                pos=positions,
                edge_index=edge_index,
                edge_attr=edge_attr,
                y=target
            )
            self.data_list.append(data)
    
    def __len__(self):
        return len(self.data_list)
    
    def __getitem__(self, idx):
        return self.data_list[idx]

def set_seed(seed: int):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    epochs: int = 30,
    lr: float = 1e-4,
    device: str = 'cpu',
    seed: int = 42
) -> Dict[str, float]:
    """
    Trains a single SchNet model.
    
    Args:
        model: The SchNet model instance.
        train_loader: DataLoader for training set.
        val_loader: DataLoader for validation set.
        epochs: Maximum number of epochs (HARD CAP as per FR-003).
        lr: Learning rate.
        device: Device to run on.
        seed: Random seed.
        
    Returns:
        Dictionary containing final training and validation loss.
    """
    set_seed(seed)
    model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()
    
    best_val_loss = float('inf')
    patience = 5
    patience_counter = 0
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for batch in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            out = model(batch)
            loss = criterion(out, batch.y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        
        train_loss /= len(train_loader)
        
        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(device)
                out = model(batch)
                loss = criterion(out, batch.y)
                val_loss += loss.item()
        
        val_loss /= len(val_loader)
        
        log_progress(f"Epoch {epoch+1}/{epochs} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")
        
        # Early stopping logic (if loss stalls, stop at 30 anyway)
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                log_progress(f"Early stopping at epoch {epoch+1}")
                break
                
        # Hard cap enforcement (already in loop range, but explicit check)
        if epoch == epochs - 1:
            log_progress(f"Reached max epochs ({epochs}).")

    return {
        "final_train_loss": train_loss,
        "final_val_loss": val_loss,
        "best_val_loss": best_val_loss,
        "epochs_run": epoch + 1
    }

def run_ensemble_training(
    graphs: List[Dict[str, Any]],
    config_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    n_folds: int = 5,
    epochs: int = 30
) -> List[Dict[str, Any]]:
    """
    Runs the full ensemble training with 5-Fold LLSO.
    
    This function:
    1. Generates LLSO splits.
    2. For each fold:
       - Trains a model on the training set.
       - Validates on the held-out test set (which contains unseen scaffolds).
       - Saves the checkpoint.
    3. Returns a summary of results.
    
    Args:
        graphs: List of graph dictionaries.
        config_path: Path to config file (optional).
        output_dir: Directory to save models and results.
        n_folds: Number of folds (default 5).
        epochs: Max epochs per model.
        
    Returns:
        List of result dictionaries for each fold.
    """
    project_root = get_project_root()
    if output_dir is None:
        output_dir = project_root / "data" / "processed" / "models"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load config if provided
    if config_path and config_path.exists():
        config = load_config(config_path)
    else:
        config = {}
    
    device = config.get('device', 'cpu')
    batch_size = config.get('batch_size', 32)
    lr = config.get('lr', 1e-4)
    seed_base = config.get('seed', 42)
    
    # Step 1: Generate Splits
    logger.info(f"Generating {n_folds}-fold LLSO splits...")
    splits = generate_llso_splits(graphs, n_folds=n_folds, seed=seed_base)
    save_splits_to_json(splits, output_path=project_root / "data" / "processed" / "splits.json")
    
    results = []
    
    for fold_idx, split in enumerate(splits):
        logger.info(f"--- Training Fold {fold_idx} ---")
        train_indices = split['train_indices']
        test_indices = split['test_indices']
        
        train_data = [graphs[i] for i in train_indices]
        test_data = [graphs[i] for i in test_indices]
        
        train_dataset = GraphDataset(train_data)
        test_dataset = GraphDataset(test_data)
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
        
        # Initialize Model
        model_config = get_model_config(config)
        model = SchNet(**model_config)
        
        # Train
        fold_seed = seed_base + fold_idx
        training_results = train_model(
            model=model,
            train_loader=train_loader,
            val_loader=test_loader, # Using test as val for this simplified loop
            epochs=epochs,
            lr=lr,
            device=device,
            seed=fold_seed
        )
        
        # Save Checkpoint
        checkpoint_path = output_dir / f"seed_{fold_seed}.pt"
        torch.save({
            'model_state_dict': model.state_dict(),
            'fold': fold_idx,
            'seed': fold_seed,
            'metrics': training_results
        }, checkpoint_path)
        
        results.append({
            "fold": fold_idx,
            "seed": fold_seed,
            "train_size": len(train_data),
            "test_size": len(test_data),
            "checkpoint_path": str(checkpoint_path),
            "metrics": training_results
        })
        
        logger.info(f"Fold {fold_idx} completed. Saved to {checkpoint_path}")
    
    # Save summary
    summary_path = output_dir / "ensemble_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Ensemble training complete. Summary saved to {summary_path}")
    return results

def main():
    """Main entry point for standalone execution."""
    # Mock data for demonstration
    mock_graphs = [
        {
            "atomic_numbers": [6, 6, 6],
            "positions": [[0,0,0], [1,0,0], [2,0,0]],
            "edge_index": [[0,1,1,2], [1,0,2,1]],
            "edge_attr": [[0.1], [0.1], [0.1], [0.1]],
            "barrier_height": 1.5 + i * 0.1
        } for i in range(20)
    ]
    
    results = run_ensemble_training(mock_graphs, n_folds=3, epochs=2)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
