import os
import json
import random
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
from torch_geometric.data import DataLoader
from torch_geometric.data import Data

from src.models.schnet import SchNet, get_model_config
from src.utils.logging import setup_logger, log_progress, log_metric, log_error_summary
from src.utils.config import get_project_root, load_yaml_config

# Configure logging
logger = setup_logger(__name__, level=logging.INFO)

class GraphDataset(torch.utils.data.Dataset):
    """
    PyTorch Dataset wrapper for graph data loaded from parquet or similar.
    Expects a list of dicts or Data objects.
    """
    def __init__(self, graphs: List[Data]):
        self.graphs = graphs

    def __len__(self):
        return len(self.graphs)

    def __getitem__(self, idx):
        return self.graphs[idx]

def set_seed(seed: int):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    logger.info(f"Seed set to {seed}")

def train_model(
    model: SchNet,
    train_loader: DataLoader,
    val_loader: DataLoader,
    seed: int,
    max_epochs: int = 30,
    lr: float = 1e-4,
    device: str = "cpu",
    checkpoint_dir: Optional[Path] = None
) -> Dict[str, float]:
    """
    Train a single SchNet model with a HARD CAP on epochs.
    
    Args:
        model: The SchNet model instance.
        train_loader: DataLoader for training set.
        val_loader: DataLoader for validation set.
        seed: Random seed for this run.
        max_epochs: Maximum number of epochs (HARD CAP).
        lr: Learning rate.
        device: Device to train on.
        checkpoint_dir: Directory to save checkpoints.
    
    Returns:
        Dictionary containing final metrics.
    """
    set_seed(seed)
    
    model = model.to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)

    best_val_loss = float('inf')
    final_metrics = {}

    logger.info(f"Starting training for seed {seed} with hard cap of {max_epochs} epochs.")
    
    for epoch in range(1, max_epochs + 1):
        model.train()
        total_train_loss = 0.0
        num_batches = 0

        for batch in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            
            # Predict energy (assuming target is 'y' in Data object)
            out = model(batch)
            loss = criterion(out, batch.y)
            
            loss.backward()
            optimizer.step()
            
            total_train_loss += loss.item()
            num_batches += 1

        avg_train_loss = total_train_loss / num_batches if num_batches > 0 else 0.0

        # Validation
        model.eval()
        total_val_loss = 0.0
        val_num_batches = 0
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(device)
                out = model(batch)
                loss = criterion(out, batch.y)
                total_val_loss += loss.item()
                val_num_batches += 1

        avg_val_loss = total_val_loss / val_num_batches if val_num_batches > 0 else 0.0
        
        scheduler.step(avg_val_loss)

        log_metric(logger, f"Epoch {epoch}/{max_epochs}", {
            "train_loss": avg_train_loss,
            "val_loss": avg_val_loss,
            "lr": optimizer.param_groups[0]['lr']
        })

        # Save best model checkpoint
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            if checkpoint_dir:
                checkpoint_path = checkpoint_dir / f"seed_{seed}_best.pt"
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'val_loss': avg_val_loss,
                    'seed': seed
                }, checkpoint_path)
                logger.info(f"Saved new best checkpoint to {checkpoint_path}")

        # Log progress
        log_progress(logger, f"Epoch {epoch}/{max_epochs}", avg_val_loss)

    # Final checkpoint (last epoch)
    if checkpoint_dir:
        final_path = checkpoint_dir / f"seed_{seed}.pt"
        torch.save({
            'epoch': max_epochs,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'val_loss': avg_val_loss,
            'seed': seed
        }, final_path)
        logger.info(f"Saved final checkpoint to {final_path}")

    final_metrics = {
        "seed": seed,
        "final_train_loss": avg_train_loss,
        "final_val_loss": avg_val_loss,
        "best_val_loss": best_val_loss,
        "epochs_run": max_epochs
    }

    return final_metrics

def run_ensemble_training(
    config_path: Optional[Path] = None,
    data_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Orchestrates the training of the 5-model ensemble.
    
    Args:
        config_path: Path to YAML config file.
        data_path: Path to processed graphs data.
    
    Returns:
        Aggregated training results.
    """
    project_root = get_project_root()
    if config_path is None:
        config_path = project_root / "specs" / "model_config.yaml"
    
    # Load config
    if config_path.exists():
        config = load_yaml_config(config_path)
    else:
        logger.warning(f"Config not found at {config_path}, using defaults.")
        config = {
            "max_epochs": 30,
            "learning_rate": 1e-4,
            "batch_size": 32,
            "num_ensembles": 5,
            "device": "cpu"
        }

    max_epochs = config.get("max_epochs", 30)
    lr = config.get("learning_rate", 1e-4)
    batch_size = config.get("batch_size", 32)
    num_ensembles = config.get("num_ensembles", 5)
    device = config.get("device", "cpu")

    # Ensure data path is set (fallback to default if not provided)
    if data_path is None:
        data_path = project_root / "data" / "processed" / "graphs.parquet"
    
    # In a real scenario, we would load the graphs from parquet here.
    # Since T014/T016 are prerequisites, we assume the data exists or is simulated
    # for the purpose of this specific task's code structure.
    # However, per constraints, we must implement the logic to load REAL data.
    # We will implement the loading logic assuming the parquet exists.
    
    try:
        import pandas as pd
        import numpy as np
        from torch_geometric.data import Data
        
        df = pd.read_parquet(data_path)
        logger.info(f"Loaded {len(df)} graphs from {data_path}")
        
        # Convert DataFrame to PyTorch Geometric Data objects
        # This assumes specific column naming from T016 graph_construction
        graphs = []
        for _, row in df.iterrows():
            # Reconstruct Data object from row data
            # This is a simplified reconstruction; real implementation depends on T016 schema
            x = torch.tensor(row.get('node_features', []), dtype=torch.float)
            edge_index = torch.tensor(row.get('edge_index', []), dtype=torch.long)
            edge_attr = torch.tensor(row.get('edge_features', []), dtype=torch.float)
            y = torch.tensor([row['energy_dft']], dtype=torch.float)
            
            graph = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)
            graphs.append(graph)
            
    except Exception as e:
        logger.error(f"Failed to load data from {data_path}: {e}")
        # If data is missing, we cannot proceed with training.
        # We raise an error to satisfy "Fail loudly" constraint.
        raise RuntimeError(f"Data loading failed. Ensure {data_path} exists and is valid.") from e

    # Split data (assuming splits are already generated by T028)
    splits_path = project_root / "data" / "processed" / "splits.json"
    if splits_path.exists():
        with open(splits_path, 'r') as f:
            splits_data = json.load(f)
        # Assuming splits_data has 'train_indices' and 'val_indices' for the first fold
        train_indices = splits_data[0]['train_indices']
        val_indices = splits_data[0]['val_indices']
    else:
        logger.warning("Splits file not found. Creating a random split.")
        indices = list(range(len(graphs)))
        random.shuffle(indices)
        split_idx = int(0.8 * len(indices))
        train_indices = indices[:split_idx]
        val_indices = indices[split_idx:]

    train_graphs = [graphs[i] for i in train_indices]
    val_graphs = [graphs[i] for i in val_indices]

    train_loader = DataLoader(train_graphs, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_graphs, batch_size=batch_size, shuffle=False)

    # Create checkpoint directory
    checkpoint_dir = project_root / "data" / "processed" / "models"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    ensemble_results = []

    for i in range(num_ensembles):
        seed = 42 + i  # Distinct seeds
        logger.info(f"Training model {i+1}/{num_ensembles} with seed {seed}")
        
        model = SchNet(**get_model_config())
        
        metrics = train_model(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            seed=seed,
            max_epochs=max_epochs,
            lr=lr,
            device=device,
            checkpoint_dir=checkpoint_dir
        )
        
        ensemble_results.append(metrics)
        log_metric(logger, f"Model {i+1} Finished", metrics)

    # Save ensemble summary
    summary_path = project_root / "data" / "processed" / "training_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(ensemble_results, f, indent=2)
    
    logger.info(f"Ensemble training complete. Summary saved to {summary_path}")
    return ensemble_results

def main():
    """Entry point for ensemble training."""
    try:
        results = run_ensemble_training()
        print(json.dumps(results, indent=2))
    except Exception as e:
        log_error_summary(logger, e)
        raise

if __name__ == "__main__":
    main()