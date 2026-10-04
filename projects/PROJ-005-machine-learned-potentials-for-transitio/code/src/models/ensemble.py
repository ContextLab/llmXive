import os
import json
import random
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch_geometric.data import Data, Batch

from src.models.schnet import SchNet, get_model_config
from src.utils.config import load_config, get_project_root
from src.utils.logging import setup_logger, get_logger, log_metric

# Configure logger
logger = get_logger(__name__)

class GraphDataset(torch.utils.data.Dataset):
    """
    PyTorch Dataset wrapper for graph data loaded from parquet.
    Expects a list of dictionaries with 'x', 'edge_index', 'edge_attr', 'y' keys.
    """
    def __init__(self, data_list: List[Dict[str, Any]]):
        self.data_list = data_list

    def __len__(self):
        return len(self.data_list)

    def __getitem__(self, idx):
        item = self.data_list[idx]
        # Ensure tensors are on correct device (handled in training loop usually, but good practice)
        return Data(
            x=torch.tensor(item['x'], dtype=torch.float),
            edge_index=torch.tensor(item['edge_index'], dtype=torch.long),
            edge_attr=torch.tensor(item['edge_attr'], dtype=torch.float),
            y=torch.tensor(item['y'], dtype=torch.float).view(-1, 1)
        )

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
    device: torch.device,
    seed: int,
    max_epochs: int = 30,
    patience: int = 5,
    lr: float = 1e-4,
    checkpoint_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Train a single SchNet model with Early Stopping and Hard Cap.
    
    Args:
        model: The SchNet model instance.
        train_loader: DataLoader for training set.
        val_loader: DataLoader for validation set.
        device: Torch device (cpu or cuda).
        seed: Random seed for this training run.
        max_epochs: Hard cap on number of epochs (default 30).
        patience: Number of epochs to wait for improvement before stopping (default 5).
        lr: Learning rate.
        checkpoint_dir: Directory to save checkpoints.
    
    Returns:
        Dictionary containing training history and best metrics.
    """
    set_seed(seed)
    
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=2)

    best_val_loss = float('inf')
    epochs_without_improvement = 0
    history = {'train_loss': [], 'val_loss': []}
    best_model_state = None
    
    logger.info(f"Starting training for seed {seed} with max_epochs={max_epochs}, patience={patience}")

    for epoch in range(1, max_epochs + 1):
        model.train()
        epoch_train_loss = 0.0
        
        for batch in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            
            out = model(batch.x, batch.edge_index, batch.edge_attr)
            loss = criterion(out, batch.y)
            
            loss.backward()
            optimizer.step()
            
            epoch_train_loss += loss.item() * batch.num_graphs

        avg_train_loss = epoch_train_loss / len(train_loader.dataset)
        history['train_loss'].append(avg_train_loss)

        # Validation phase
        model.eval()
        epoch_val_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(device)
                out = model(batch.x, batch.edge_index, batch.edge_attr)
                loss = criterion(out, batch.y)
                epoch_val_loss += loss.item() * batch.num_graphs

        avg_val_loss = epoch_val_loss / len(val_loader.dataset)
        history['val_loss'].append(avg_val_loss)
        
        scheduler.step(avg_val_loss)

        log_metric(logger, "train_loss", avg_train_loss, epoch)
        log_metric(logger, "val_loss", avg_val_loss, epoch)

        # Early Stopping Logic
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            epochs_without_improvement = 0
            best_model_state = model.state_dict().copy()
            logger.info(f"Epoch {epoch}: Improvement! Val Loss: {avg_val_loss:.6f}")
            
            # Save best checkpoint immediately upon improvement
            if checkpoint_dir:
                checkpoint_dir.mkdir(parents=True, exist_ok=True)
                checkpoint_path = checkpoint_dir / f"seed_{seed}_best.pt"
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': best_model_state,
                    'optimizer_state_dict': optimizer.state_dict(),
                    'val_loss': best_val_loss,
                    'seed': seed
                }, checkpoint_path)
        else:
            epochs_without_improvement += 1
            logger.debug(f"Epoch {epoch}: No improvement ({epochs_without_improvement}/{patience})")

        # Hard Cap Check (explicitly at end of loop, though range handles it)
        if epoch == max_epochs:
            logger.info(f"Hard cap reached: {max_epochs} epochs completed.")
            break

        # Early Stopping Trigger
        if epochs_without_improvement >= patience:
            logger.warning(f"Early stopping triggered at epoch {epoch} (patience={patience}).")
            break

    # Finalize: Load best model state if we have one
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
    
    # Save final checkpoint (last state or best state depending on policy, here we save best)
    if checkpoint_dir:
        final_checkpoint_path = checkpoint_dir / f"seed_{seed}_final.pt"
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'val_loss': best_val_loss,
            'seed': seed,
            'history': history
        }, final_checkpoint_path)
        logger.info(f"Final checkpoint saved to {final_checkpoint_path}")

    return {
        'seed': seed,
        'best_val_loss': best_val_loss,
        'epochs_trained': epoch,
        'history': history
    }

class EnsembleManager:
    """
    Manages the training and storage of an ensemble of models.
    """
    def __init__(self, num_models: int, config: Dict[str, Any], device: torch.device):
        self.num_models = num_models
        self.config = config
        self.device = device
        self.models: List[SchNet] = []
        self.results: List[Dict[str, Any]] = []
        self.checkpoint_dir = Path(get_project_root()) / "data" / "processed" / "models"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def train_ensemble(
        self,
        train_data: List[Dict[str, Any]],
        val_data: List[Dict[str, Any]],
        batch_size: int = 32,
        max_epochs: int = 30,
        patience: int = 5,
        lr: float = 1e-4
    ):
        """
        Train the full ensemble of models with different seeds.
        
        Args:
            train_data: List of graph dictionaries for training.
            val_data: List of graph dictionaries for validation.
            batch_size: Batch size for DataLoader.
            max_epochs: Hard cap on epochs (from task T024).
            patience: Early stopping patience.
            lr: Learning rate.
        """
        logger.info(f"Initializing ensemble training for {self.num_models} models.")
        
        # Create datasets and loaders
        train_dataset = GraphDataset(train_data)
        val_dataset = GraphDataset(val_data)
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

        for i in range(self.num_models):
            seed = 42 + i  # Distinct seeds
            logger.info(f"--- Training Model {i+1}/{self.num_models} (Seed: {seed}) ---")
            
            # Initialize Model
            model_cfg = get_model_config(self.config)
            model = SchNet(**model_cfg)
            model = model.to(self.device)
            
            # Train
            result = train_model(
                model=model,
                train_loader=train_loader,
                val_loader=val_loader,
                device=self.device,
                seed=seed,
                max_epochs=max_epochs,
                patience=patience,
                lr=lr,
                checkpoint_dir=self.checkpoint_dir
            )
            
            self.results.append(result)
            self.models.append(model)
            
            logger.info(f"Model {i+1} finished. Best Val Loss: {result['best_val_loss']:.6f}")

        logger.info("Ensemble training complete.")
        return self.results

def run_ensemble_training(
    graphs: List[Dict[str, Any]],
    splits: Dict[str, List[int]],
    num_models: int = 5,
    batch_size: int = 32,
    max_epochs: int = 30,
    patience: int = 5,
    lr: float = 1e-4
) -> List[Dict[str, Any]]:
    """
    Orchestrates the training of the ensemble using the provided graphs and splits.
    
    Args:
        graphs: Full list of graph data dictionaries.
        splits: Dictionary with 'train_indices' and 'val_indices' keys.
        num_models: Number of models in the ensemble.
        batch_size: Batch size.
        max_epochs: Hard cap on epochs.
        patience: Early stopping patience.
        lr: Learning rate.
        
    Returns:
        List of training result dictionaries.
    """
    config = load_config()
    device = torch.device("cpu") # Enforce CPU as per constraints
    
    train_indices = splits.get('train_indices', [])
    val_indices = splits.get('val_indices', [])
    
    train_data = [graphs[i] for i in train_indices]
    val_data = [graphs[i] for i in val_indices]
    
    manager = EnsembleManager(num_models, config, device)
    results = manager.train_ensemble(
        train_data=train_data,
        val_data=val_data,
        batch_size=batch_size,
        max_epochs=max_epochs,
        patience=patience,
        lr=lr
    )
    
    return results

def main():
    """
    Entry point for standalone execution of ensemble training.
    Expects `graphs.parquet` and `splits.json` to exist in the processed directory.
    """
    import pandas as pd
    
    logger.info("Starting Ensemble Training (T024)")
    
    # Load Data
    project_root = get_project_root()
    graphs_path = project_root / "data" / "processed" / "graphs.parquet"
    splits_path = project_root / "data" / "processed" / "splits.json"
    
    if not graphs_path.exists():
        raise FileNotFoundError(f"Required input {graphs_path} not found. Run data ingestion first.")
    if not splits_path.exists():
        raise FileNotFoundError(f"Required input {splits_path} not found. Run split generation first.")
    
    logger.info(f"Loading graphs from {graphs_path}")
    df_graphs = pd.read_parquet(graphs_path)
    
    # Convert parquet rows to list of dicts (assuming columns match graph attributes)
    # Note: In a real scenario, we might need to reconstruct edge_index/edge_attr if stored differently.
    # Assuming the parquet stores flattened features or the ingestion step prepared this format.
    # For this implementation, we assume the parquet contains necessary columns: 
    # 'x', 'edge_index', 'edge_attr', 'y' (or similar mapping).
    # If the parquet stores lists in cells, pandas handles them as objects.
    
    graphs_list = []
    for _, row in df_graphs.iterrows():
        # Handle potential numpy arrays or lists in cells
        graph_entry = {
            'x': row['x'] if isinstance(row['x'], (list, np.ndarray)) else row['x'].tolist(),
            'edge_index': row['edge_index'] if isinstance(row['edge_index'], (list, np.ndarray)) else row['edge_index'].tolist(),
            'edge_attr': row['edge_attr'] if isinstance(row['edge_attr'], (list, np.ndarray)) else row['edge_attr'].tolist(),
            'y': row['y'] if isinstance(row['y'], (list, np.ndarray)) else row['y'].tolist()
        }
        graphs_list.append(graph_entry)
    
    logger.info(f"Loaded {len(graphs_list)} graphs.")
    
    import json
    with open(splits_path, 'r') as f:
        splits = json.load(f)
    
    # Assume splits structure: {"train_indices": [...], "val_indices": [...]}
    # If splits.json has a different structure (e. g. fold-based), we adapt here.
    # Based on T011, splits.json usually contains train/val/test lists.
    # We will use the first fold defined or the global train/val if structured that way.
    
    if 'train_indices' not in splits:
        # Fallback if structure is different, e.g., {"0": {"train": [...], "val": [...]}}
        # For T024, we assume a simple split or the first fold is used for this demo.
        # However, T029a handles the CV loop. T024 is the training loop implementation.
        # We will assume `splits` contains the specific indices to use for this run.
        # If the splits file has multiple folds, we might need to pick one.
        # Let's assume the file structure is: {"train": [...], "val": [...]} or similar.
        if 'train' in splits and 'val' in splits:
            splits_indices = {'train_indices': splits['train'], 'val_indices': splits['val']}
        else:
            raise ValueError(f"Unexpected splits.json structure: {list(splits.keys())}")
    else:
        splits_indices = splits
    
    # Run Training
    results = run_ensemble_training(
        graphs=graphs_list,
        splits=splits_indices,
        num_models=5,
        max_epochs=30,
        patience=5
    )
    
    # Save summary
    summary_path = project_root / "data" / "processed" / "ensemble_training_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Training summary saved to {summary_path}")
    logger.info("Ensemble Training (T024) completed successfully.")

if __name__ == "__main__":
    main()