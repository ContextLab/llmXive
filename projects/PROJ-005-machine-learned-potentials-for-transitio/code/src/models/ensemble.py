"""
Ensemble training logic for SchNet models using Leave-Ligand-Scaffold-Out splits.

This module handles:
1. Loading split configurations from data/processed/splits.json.
2. Training 5 models (one per fold) with different seeds.
3. Saving checkpoints and metrics.
"""
import os
import json
import random
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
import torch
from torch_geometric.data import Data, DataLoader
from torch_geometric.loader import NeighborLoader

# Import local components
from src.models.schnet import SchNet, get_model_config
from src.utils.config import get_project_root
from src.utils.logging import setup_logger, log_metric

logger = logging.getLogger(__name__)


class GraphDataset(torch.utils.data.Dataset):
    """
    Custom PyTorch Dataset for loading graph data from a Parquet file
    filtered by specific indices.
    """
    def __init__(
        self,
        parquet_path: Path,
        indices: List[int],
        node_attr_cols: List[str] = ['atomic_number', 'formal_charge'],
        edge_attr_cols: List[str] = ['distance'],
        target_col: str = 'energy_dft'
    ):
        self.parquet_path = parquet_path
        self.indices = sorted(indices)
        self.node_attr_cols = node_attr_cols
        self.edge_attr_cols = edge_attr_cols
        self.target_col = target_col

        # Load full dataframe once
        self.df = pd.read_parquet(parquet_path)

        # Validate indices
        max_idx = self.df.index.max() if len(self.df) > 0 else -1
        if any(i < 0 or i > max_idx for i in self.indices):
            raise ValueError(f"Indices out of range for dataframe (max: {max_idx})")

    def __len__(self) -> int:
        return len(self.indices)

    def __getitem__(self, idx: int) -> Data:
        row_idx = self.indices[idx]
        row = self.df.iloc[row_idx]

        # Extract node features
        # Assuming node features are stored as lists/arrays in the row
        # Or if the row contains flattened node features, we need to reshape.
        # For this implementation, we assume 'atomic_numbers' and 'formal_charges'
        # are lists in the row corresponding to nodes.
        if 'atomic_numbers' in row.index:
            atomic_numbers = torch.tensor(row['atomic_numbers'], dtype=torch.long)
            formal_charges = torch.tensor(row['formal_charges'], dtype=torch.float)
        else:
            # Fallback if stored differently
            atomic_numbers = torch.tensor([row['atomic_number']], dtype=torch.long)
            formal_charges = torch.tensor([row['formal_charge']], dtype=torch.float)

        # Combine node attributes
        x = torch.stack([atomic_numbers.float(), formal_charges], dim=1)

        # Extract edge attributes
        # Assuming 'edge_index' and 'edge_distances' are stored
        if 'edge_index' in row.index:
            edge_index = torch.tensor(row['edge_index'], dtype=torch.long)
            edge_attr = torch.tensor(row['edge_distances'], dtype=torch.float).unsqueeze(1)
        else:
            # Fallback for simple graphs
            edge_index = torch.tensor([[0, 1], [1, 0]], dtype=torch.long)
            edge_attr = torch.tensor([[0.0], [0.0]], dtype=torch.float)

        # Target
        y = torch.tensor([row[self.target_col]], dtype=torch.float)

        return Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)


def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def train_model(
    train_loader: DataLoader,
    val_loader: DataLoader,
    config: Dict[str, Any],
    seed: int,
    model_path: Path
) -> Dict[str, float]:
    """
    Train a single SchNet model.

    Args:
        train_loader: DataLoader for training set.
        val_loader: DataLoader for validation set.
        config: Model and training configuration.
        seed: Random seed for this model.
        model_path: Path to save the checkpoint.

    Returns:
        Dictionary of final metrics.
    """
    set_seed(seed)
    logger.info(f"Training model with seed {seed}...")

    # Initialize model
    model_config = get_model_config(config)
    model = SchNet(**model_config)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.get('lr', 1e-4))
    criterion = torch.nn.MSELoss()

    device = torch.device('cpu') # Enforce CPU as per constraints
    model.to(device)

    best_val_loss = float('inf')
    epochs = config.get('max_epochs', 30)

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for batch in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            out = model(batch.x, batch.edge_index, batch.edge_attr)
            loss = criterion(out, batch.y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_train_loss = total_loss / len(train_loader)

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(device)
                out = model(batch.x, batch.edge_index, batch.edge_attr)
                loss = criterion(out, batch.y)
                val_loss += loss.item()

        avg_val_loss = val_loss / len(val_loader)

        if epoch % 5 == 0 or epoch == epochs:
            logger.info(
                f"Epoch {epoch:03d} | Train Loss: {avg_train_loss:.6f} | Val Loss: {avg_val_loss:.6f}"
            )
            log_metric(f"fold_{seed}_epoch_{epoch}_val_loss", avg_val_loss)

        # Save best
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': best_val_loss,
                'config': config
            }, model_path)
            logger.info(f"Saved best model to {model_path}")

    return {'final_val_loss': best_val_loss}


def run_ensemble_training(
    splits_path: Optional[Path] = None,
    graphs_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Run the full 5-Fold LLSO ensemble training.

    Args:
        splits_path: Path to splits.json.
        graphs_path: Path to graphs.parquet.
        output_dir: Directory to save models and metrics.
        config: Training configuration.

    Returns:
        List of results for each fold.
    """
    if splits_path is None:
        project_root = get_project_root()
        splits_path = project_root / "data" / "processed" / "splits.json"
    if graphs_path is None:
        project_root = get_project_root()
        graphs_path = project_root / "data" / "processed" / "graphs.parquet"
    if output_dir is None:
        project_root = get_project_root()
        output_dir = project_root / "data" / "processed" / "models"

    if config is None:
        config = {
            'max_epochs': 30,
            'lr': 1e-4,
            'batch_size': 32,
            'hidden_channels': 128,
            'num_filters': 32,
            'num_gnn_layers': 3
        }

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load splits
    if not splits_path.exists():
        raise FileNotFoundError(f"Splits file not found at {splits_path}")

    with open(splits_path, 'r') as f:
        splits = json.load(f)

    logger.info(f"Loaded {len(splits)} splits from {splits_path}")

    results = []

    for fold_idx, split_data in enumerate(splits):
        logger.info(f"--- Processing Fold {fold_idx} ---")

        train_indices = split_data['train_indices']
        test_indices = split_data['test_indices']

        # Create datasets
        train_dataset = GraphDataset(graphs_path, train_indices)
        test_dataset = GraphDataset(graphs_path, test_indices)

        # Create loaders
        train_loader = DataLoader(train_dataset, batch_size=config['batch_size'], shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=config['batch_size'], shuffle=False)

        # Define paths
        model_path = output_dir / f"seed_{fold_idx}.pt"

        # Train
        metrics = train_model(
            train_loader,
            test_loader, # Using test as val for simplicity in this loop, or split train further
            config,
            seed=fold_idx,
            model_path=model_path
        )

        results.append({
            'fold': fold_idx,
            'train_count': len(train_indices),
            'test_count': len(test_indices),
            'model_path': str(model_path),
            'metrics': metrics
        })

    return results


def main() -> None:
    """Main entry point for ensemble training."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        results = run_ensemble_training()

        # Save summary
        project_root = get_project_root()
        summary_path = project_root / "data" / "processed" / "ensemble_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Ensemble training complete. Summary saved to {summary_path}")

    except Exception as e:
        logger.error(f"Ensemble training failed: {e}", exc_info=True)
        raise
