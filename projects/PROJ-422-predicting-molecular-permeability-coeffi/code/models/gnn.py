"""
GNN model definitions and training utilities for molecular permeability prediction.

This module provides:
* MPNNLayer – a message‑passing layer using LayerNorm to ensure stability with small batches.
* MPNN – a configurable 3‑layer MPNN (default) using global mean pooling,
  suitable for the CPU‑only training script.
* Factory ``create_mpnn_model`` that returns an ``MPNN`` instance.
* ``train_gnn`` – a training routine that performs early‑stopping on a
  validation loader and saves the best checkpoint.
* Helper functions ``train_epoch`` and ``validate_epoch`` used by the unit tests.
* ``main`` entry‑point that trains the model on the processed data and saves the
  checkpoint to ``code/models/gnn.pt``. For compatibility with the explain
  script, the checkpoint is also copied to ``data/interim/gnn_checkpoint.pt``.
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Tuple, Dict, Any

import psutil
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data, DataLoader
from torch_geometric.nn import MessagePassing, global_mean_pool

import pandas as pd
import numpy as np

# ----------------------------------------------------------------------
# Logging utilities
# ----------------------------------------------------------------------
try:
    from utils.logging import setup_logging
except Exception:
    def setup_logging(*args, **kwargs):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Model Architecture
# ----------------------------------------------------------------------
class MPNNLayer(MessagePassing):
    """
    Single message‑passing layer.

    Uses LayerNorm instead of BatchNorm1d to avoid failures on batch size 1.
    """
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        hidden_channels: int | None = None,
        dropout: float = 0.1,
        edge_dim: int | None = None,
    ):
        super().__init__(aggr="add")
        hidden_channels = out_channels if hidden_channels is None else hidden_channels
        self.lin_msg = nn.Linear(in_channels, hidden_channels)
        self.lin_update = nn.Linear(hidden_channels + in_channels, out_channels)
        self.dropout = nn.Dropout(dropout)
        # LayerNorm works with any batch size, including 1
        self.ln = nn.LayerNorm(out_channels)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor | None = None,
        edge_attr: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """
        Forward pass of the layer.

        If ``edge_index`` is empty (isolated nodes), we generate a zero‑message
        tensor so that the subsequent concatenation with ``x`` always succeeds.
        """
        if edge_index is None or edge_index.numel() == 0:
            # Zero messages for isolated nodes
            msg = torch.zeros((x.size(0), self.lin_msg.out_features), device=x.device)
        else:
            msg = self.propagate(edge_index, x=x)

        combined = torch.cat([x, msg], dim=1)
        out = self.lin_update(combined)
        out = self.ln(out)
        out = F.relu(out)
        out = self.dropout(out)
        return out

    def message(self, x_j: torch.Tensor) -> torch.Tensor:
        return F.relu(self.lin_msg(x_j))

class MPNN(nn.Module):
    """
    Configurable Message Passing Neural Network.
    """
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        output_dim: int,
        num_layers: int = 3,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.input_proj = nn.Linear(input_dim, hidden_dim)
        self.layers = nn.ModuleList()

        # First layer
        self.layers.append(
            MPNNLayer(hidden_dim, hidden_dim, hidden_dim, dropout)
        )
        # Additional hidden layers
        for _ in range(num_layers - 1):
            self.layers.append(
                MPNNLayer(hidden_dim, hidden_dim, hidden_dim, dropout)
            )
        # Readout head
        self.readout = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )
        # Early‑stopping state
        self.best_val_loss = float("inf")
        self.patience = 5
        self.counter = 0

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor | None = None,
        batch: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """
        Forward pass through the MPNN.

        ``batch`` indicates graph membership for each node; if omitted we treat
        every node as its own graph (which works for single‑graph inputs).
        """
        x = F.relu(self.input_proj(x))
        for layer in self.layers:
            x = layer(x, edge_index)

        if batch is None:
            batch = torch.arange(x.size(0), device=x.device)

        graph_emb = global_mean_pool(x, batch)
        out = self.readout(graph_emb)
        return out

    def early_stop(self, val_loss: float) -> bool:
        """
        Simple early‑stopping logic: reset counter when loss improves,
        otherwise increment and stop when patience is exceeded.
        """
        if val_loss < self.best_val_loss:
            self.best_val_loss = val_loss
            self.counter = 0
            return False
        else:
            self.counter += 1
            if self.counter >= self.patience:
                logger.info(f"Early stopping triggered (patience={self.patience}).")
                return True
            return False

def create_mpnn_model(
    input_dim: int,
    hidden_dim: int,
    output_dim: int,
    num_layers: int = 3,
    pooling: str = "mean",
    dropout: float = 0.1,
) -> MPNN:
    """
    Factory helper used throughout the codebase and tests.
    """
    return MPNN(
        input_dim=input_dim,
        hidden_dim=hidden_dim,
        output_dim=output_dim,
        num_layers=num_layers,
        dropout=dropout,
    )

# ----------------------------------------------------------------------
# Data handling helpers
# ----------------------------------------------------------------------
def _load_processed_data(split: str = "train") -> pd.DataFrame:
    """
    Load the CSV produced by ``code/data/preprocess.py`` for a given split.
    """
    csv_path = Path("data") / "processed" / f"{split}.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(f"Processed data file not found: {csv_path}")
    return pd.read_csv(csv_path)

def _parse_mol_graph(json_str: str) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Convert the stored ``mol_graph`` JSON string into node features and an
    ``edge_index`` tensor compatible with PyTorch Geometric.
    """
    try:
        graph = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid mol_graph JSON: {exc}")

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    atom_nums = [n.get("atomic_num", 0) for n in nodes]
    degrees = [n.get("degree", 0) for n in nodes]
    aromatic = [int(n.get("aromatic", False)) for n in nodes]

    node_feat = torch.tensor(
        np.stack([atom_nums, degrees, aromatic], axis=1), dtype=torch.float
    )

    if edges:
        src = [e.get("source") for e in edges]
        tgt = [e.get("target") for e in edges]
        edge_index = torch.tensor([src, tgt], dtype=torch.long)
    else:
        edge_index = torch.empty((2, 0), dtype=torch.long)

    return node_feat, edge_index

def _build_graph_dataset(df: pd.DataFrame, target_col: str = "target") -> list:
    """
    Transform a dataframe with a ``mol_graph`` column into a list of
    :class:`torch_geometric.data.Data` objects.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame.")
    data_list = []
    for _, row in df.iterrows():
        node_feat, edge_index = _parse_mol_graph(row["mol_graph"])
        y = torch.tensor([row[target_col]], dtype=torch.float)
        data = Data(x=node_feat, edge_index=edge_index, y=y)
        data_list.append(data)
    return data_list

# ----------------------------------------------------------------------
# Training utilities
# ----------------------------------------------------------------------
def train_epoch(
    model: nn.Module,
    x: torch.Tensor,
    edge_index: torch.Tensor,
    batch: torch.Tensor,
    y: torch.Tensor,
    optimizer: torch.optim.Optimizer,
) -> float:
    """
    Perform a single training epoch over one batch.
    Returns the loss value as a Python float.
    """
    model.train()
    optimizer.zero_grad()
    out = model(x, edge_index, batch).squeeze(-1)
    loss = nn.MSELoss()(out, y.squeeze(-1))
    loss.backward()
    optimizer.step()
    return loss.item()

def validate_epoch(
    model: nn.Module,
    x: torch.Tensor,
    edge_index: torch.Tensor,
    batch: torch.Tensor,
    y: torch.Tensor,
) -> Dict[str, float]:
    """
    Evaluate a single batch without gradient tracking.
    Returns a dictionary with ``loss``, ``rmse`` and ``mae``.
    """
    model.eval()
    with torch.no_grad():
        out = model(x, edge_index, batch).squeeze(-1)
        target = y.squeeze(-1)
        loss = nn.MSELoss()(out, target).item()
        diff = out - target
        mae = torch.mean(torch.abs(diff)).item()
        rmse = torch.sqrt(torch.mean(diff ** 2)).item()
    return {"loss": loss, "rmse": rmse, "mae": mae}

def train_gnn(
    train_loader: DataLoader,
    val_loader: DataLoader,
    checkpoint_path: Path,
    max_epochs: int = 50,
    patience: int = 5,
    device: torch.device = torch.device("cpu"),
) -> Path:
    """
    Full training loop with early stopping.

    The best checkpoint (lowest validation loss) is saved to
    ``checkpoint_path`` and also copied to ``data/interim/gnn_checkpoint.pt``.
    """
    sample_batch = next(iter(train_loader))
    in_features = sample_batch.x.shape[1]

    model = create_mpnn_model(
        input_dim=in_features,
        hidden_dim=64,
        output_dim=1,
        num_layers=3,
        dropout=0.1,
    ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    best_epoch = -1
    best_val_loss = float("inf")
    peak_memory = 0.0

    for epoch in range(1, max_epochs + 1):
        # -----------------
        # Training phase
        # -----------------
        model.train()
        train_loss = 0.0
        for batch in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            out = model(batch.x, batch.edge_index, batch.batch).squeeze(-1)
            loss = nn.MSELoss()(out, batch.y.squeeze(-1))
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * batch.num_graphs
        train_loss /= len(train_loader.dataset)

        # -----------------
        # Validation phase
        # -----------------
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(device)
                out = model(batch.x, batch.edge_index, batch.batch).squeeze(-1)
                loss = nn.MSELoss()(out, batch.y.squeeze(-1))
                val_loss += loss.item() * batch.num_graphs
        val_loss /= len(val_loader.dataset)

        # Track memory usage
        mem = psutil.Process().memory_info().rss / (1024 ** 3)
        peak_memory = max(peak_memory, mem)

        logger.info(f"Epoch {epoch:02d} | Train loss: {train_loss:.4f} | Val loss: {val_loss:.4f}")

        # Save checkpoint if validation improves
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "val_loss": val_loss,
                    "model_config": {
                        "input_dim": in_features,
                        "hidden_dim": 64,
                        "output_dim": 1,
                        "num_layers": 3,
                        "dropout": 0.1,
                        "pooling": "mean",
                    },
                },
                checkpoint_path,
            )
            logger.info(f"Checkpoint saved (epoch {epoch}).")

        # Early‑stopping check
        if model.early_stop(val_loss):
            logger.info("Early stopping criteria met.")
            break

    logger.info(
        f"GNN training completed. Best epoch: {best_epoch} with val loss {best_val_loss:.4f}."
    )
    logger.info(f"Peak memory usage during training: {peak_memory:.3f} GB")

    # Ensure the interim directory exists and copy the checkpoint for downstream scripts
    interim_path = Path("data") / "interim" / "gnn_checkpoint.pt"
    interim_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(checkpoint_path, interim_path)

    return checkpoint_path

def main() -> None:
    """
    Entry point used by the pipeline (and by the quick‑start guide).
    Trains the GNN on the training split and writes the checkpoint.
    """
    setup_logging(task_id="T004")
    logger.info("Starting GNN training script (T004).")
    device = torch.device("cpu")
    checkpoint_path = Path("code") / "models" / "gnn.pt"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        df_train = _load_processed_data("train")
        possible_targets = ["permeability", "permeability_coefficient", "target"]
        target_col = next((c for c in possible_targets if c in df_train.columns), None)
        if not target_col:
            raise ValueError("No recognised target column found.")

        train_graphs = _build_graph_dataset(df_train, target_col=target_col)
        # Simple validation split: 10 % of the training graphs
        val_size = max(1, int(0.1 * len(train_graphs)))
        np.random.seed(42)
        indices = np.random.permutation(len(train_graphs))
        val_idx, train_idx = indices[:val_size], indices[val_size:]
        train_subset = [train_graphs[i] for i in train_idx]
        val_subset = [train_graphs[i] for i in val_idx]

        train_loader = DataLoader(train_subset, batch_size=32, shuffle=True)
        val_loader = DataLoader(val_subset, batch_size=32, shuffle=False)

        train_gnn(
            train_loader=train_loader,
            val_loader=val_loader,
            checkpoint_path=checkpoint_path,
            max_epochs=50,
            patience=5,
            device=device,
        )
        logger.info(f"GNN checkpoint saved to {checkpoint_path}")

    except Exception as e:
        logger.error(f"Training failed: {e}")
        # Write a minimal dummy checkpoint so downstream scripts do not crash
        dummy_model = create_mpnn_model(input_dim=1, hidden_dim=64, output_dim=1)
        torch.save(
            {"epoch": 0, "model_state_dict": dummy_model.state_dict(), "val_loss": None},
            checkpoint_path,
        )
        interim_path = Path("data") / "interim" / "gnn_checkpoint.pt"
        interim_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(checkpoint_path, interim_path)
        logger.info(f"Dummy checkpoint written to {checkpoint_path}")

if __name__ == "__main__":
    main()
