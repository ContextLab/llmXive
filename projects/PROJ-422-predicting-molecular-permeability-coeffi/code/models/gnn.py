"""
GNN model definitions and training utilities for molecular permeability prediction.

This module provides:
* MPNNLayer – a message‑passing layer compatible with the unit tests.
* MPNN – a configurable 3‑layer MPNN (default) using only global mean pooling,
  suitable for the CPU‑only training script.
* Factory ``create_mpnn_model`` that returns an ``MPNN`` instance (so the unit
  tests expecting ``isinstance(..., MPNN)`` succeed) with a ``layers`` attribute
  whose length equals the requested number of message‑passing layers.
* Minimal ``train_epoch`` and ``validate_epoch`` helpers for the unit tests.
* ``main`` entry‑point that trains the model on the dummy single‑node graphs
  (as used by ``code/analysis/train.py``) and saves the checkpoint to
  ``code/models/gnn.pt`` as required by the specification.
"""

import json
import logging
import time
from pathlib import Path

import psutil
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data, DataLoader
from torch_geometric.nn import MessagePassing, global_mean_pool

import pandas as pd
import numpy as np

# ----------------------------------------------------------------------
# Logging utilities (project‑specific)
# ----------------------------------------------------------------------
try:
    # The project provides a logging helper; import if available.
    from utils.logging import setup_logging, log_result_artifact
except Exception:  # pragma: no cover
    # Fallback to a very small wrapper when the helper cannot be imported.
    def setup_logging(*args, **kwargs):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

    def log_result_artifact(*args, **kwargs):
        pass

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Compatibility layer for the tests
# ----------------------------------------------------------------------
class MPNNLayer(MessagePassing):
    """
    Single message‑passing layer.

    The unit tests instantiate the layer with ``in_channels`` and
    ``out_channels`` (and optionally ``edge_dim``).  ``edge_dim`` is ignored
    because the current model does not use edge attributes.
    """
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        hidden_channels: int | None = None,
        dropout: float = 0.1,
        edge_dim: int | None = None,  # accepted for test compatibility
    ):
        super().__init__(aggr="add")
        hidden_channels = out_channels if hidden_channels is None else hidden_channels
        self.lin_msg = nn.Linear(in_channels, hidden_channels)
        self.lin_update = nn.Linear(hidden_channels + in_channels, out_channels)
        self.dropout = nn.Dropout(dropout)
        self.bn = nn.BatchNorm1d(out_channels)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor | None = None) -> torch.Tensor:
        """
        Forward pass of the layer.

        If ``edge_index`` is ``None`` or empty we skip message passing and
        simply propagate the node features unchanged (this allows the model
        to operate on the dummy single‑node graphs used in the training
        script).
        """
        if edge_index is None or edge_index.numel() == 0:
            msg = x  # no neighbours – message is the node feature itself
        else:
            msg = self.propagate(edge_index, x=x)  # [N, hidden]
        combined = torch.cat([x, msg], dim=1)      # [N, in+hidden]
        out = self.lin_update(combined)
        out = self.bn(out)
        out = F.relu(out)
        out = self.dropout(out)
        return out

    def message(self, x_j: torch.Tensor) -> torch.Tensor:
        """Message function – a simple linear transformation followed by ReLU."""
        return F.relu(self.lin_msg(x_j))

class MPNN(nn.Module):
    """
    Configurable Message Passing Neural Network.

    * ``num_layers`` – number of ``MPNNLayer`` blocks (default 3 to satisfy
      the unit test that expects three layers).
    * Uses only global mean pooling (as required by FR‑006).
    * Provides an ``early_stop`` method used by the original training script.
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
        Forward pass.

        * ``x`` – node feature matrix ``[total_nodes, input_dim]``.
        * ``edge_index`` – optional edge list; if omitted the layer acts as an
          identity message pass (required for the dummy graphs).
        * ``batch`` – optional batch vector mapping nodes to graphs; if omitted
          each row is treated as a separate graph.
        """
        x = F.relu(self.input_proj(x))
        for layer in self.layers:
            x = layer(x, edge_index)

        if batch is None:
            # Treat each sample as its own graph.
            batch = torch.arange(x.size(0), device=x.device)

        # Global mean pooling yields one vector per graph.
        graph_emb = global_mean_pool(x, batch)
        out = self.readout(graph_emb)
        return out

    # ------------------------------------------------------------------
    # Early‑stopping helper (used by the original script)
    # ------------------------------------------------------------------
    def early_stop(self, val_loss: float) -> bool:
        """Update early‑stopping counters.

        Returns:
            True if training should stop, False otherwise.
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

# ----------------------------------------------------------------------
# Factory and training helpers required by the tests
# ----------------------------------------------------------------------
def create_mpnn_model(
    input_dim: int,
    hidden_dim: int,
    output_dim: int,
    num_layers: int = 3,
    pooling: str = "mean",  # kept for API compatibility; only mean is used
    dropout: float = 0.1,
) -> MPNN:
    """
    Factory that builds a ``MPNN`` instance.

    The unit tests expect the returned object to be an instance of ``MPNN``
    and to expose a ``layers`` attribute whose length equals ``num_layers``.
    """
    # ``pooling`` argument is ignored – the model always uses mean pooling.
    return MPNN(
        input_dim=input_dim,
        hidden_dim=hidden_dim,
        output_dim=output_dim,
        num_layers=num_layers,
        dropout=dropout,
    )

def train_epoch(
    model: nn.Module,
    x: torch.Tensor,
    edge_index: torch.Tensor | None,
    batch: torch.Tensor,
    y: torch.Tensor,
    optimizer: torch.optim.Optimizer,
) -> float:
    """
    Perform a single training epoch on a *single* batch.

    Mirrors the minimal behaviour exercised by the unit tests:
    forward pass, MSE loss, back‑propagation, optimizer step, and return
    the loss as a Python ``float``.
    """
    model.train()
    optimizer.zero_grad()
    pred = model(x, edge_index, batch).squeeze()
    loss = nn.MSELoss()(pred, y.squeeze())
    loss.backward()
    optimizer.step()
    return loss.item()

def validate_epoch(
    model: nn.Module,
    x: torch.Tensor,
    edge_index: torch.Tensor | None,
    batch: torch.Tensor,
    y: torch.Tensor,
) -> dict:
    """
    Evaluate a model on a *single* batch.

    Returns a dictionary containing at least ``loss``, ``rmse`` and ``mae``.
    """
    model.eval()
    with torch.no_grad():
        pred = model(x, edge_index, batch).squeeze()
        loss = nn.MSELoss()(pred, y.squeeze()).item()
        mae = nn.L1Loss()(pred, y.squeeze()).item()
        rmse = torch.sqrt(nn.MSELoss()(pred, y.squeeze())).item()
    return {"loss": loss, "rmse": rmse, "mae": mae}

# ----------------------------------------------------------------------
# Helper utilities used by the original script
# ----------------------------------------------------------------------
def _cpu_feasibility_check() -> str:
    """Simple CPU feasibility check."""
    cpu_count = psutil.cpu_count(logical=True)
    mem = psutil.virtual_memory()
    free_gb = mem.available / (1024 ** 3)

    if cpu_count >= 2 and free_gb >= 2:
        status = "passed"
    else:
        status = "warning"

    metrics_path = Path("data") / "results" / "metrics.json"
    try:
        if metrics_path.exists():
            with metrics_path.open("r", encoding="utf-8") as f:
                metrics = json.load(f)
        else:
            metrics = {}
    except Exception as e:
        logger.error(f"Failed to read existing metrics.json: {e}")
        metrics = {}

    metrics["cpu_feasibility_check"] = status
    try:
        with metrics_path.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"CPU feasibility check written as '{status}'.")
    except Exception as e:
        logger.error(f"Failed to write cpu_feasibility_check to metrics.json: {e}")

    return status

def _load_processed_data(split: str = "train") -> pd.DataFrame:
    """Load processed CSV data for a given split."""
    csv_path = Path("data") / "processed" / f"{split}.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(f"Processed data file not found: {csv_path}")
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} rows from {csv_path}")
    return df

def _build_graph_dataset(df: pd.DataFrame, target_col: str = "target") -> list:
    """Convert a DataFrame into a list of torch_geometric.Data objects."""
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame.")
    feature_cols = [c for c in df.columns if c != target_col]
    data_list = []
    for _, row in df.iterrows():
        x = torch.tensor(row[feature_cols].values, dtype=torch.float).unsqueeze(0)  # [1, F]
        edge_index = torch.empty((2, 0), dtype=torch.long)  # No edges for single‑node graph
        y = torch.tensor([row[target_col]], dtype=torch.float)
        data = Data(x=x, edge_index=edge_index, y=y)
        data_list.append(data)
    logger.info(f"Constructed {len(data_list)} graph objects (single‑node each).")
    return data_list

# ----------------------------------------------------------------------
# Main execution (updated to satisfy FR‑006)
# ----------------------------------------------------------------------
def main():
    """Entry point for the GNN training script (T004)."""
    setup_logging(task_id="T004")
    logger.info("Starting GNN training script (T004).")
    cpu_status = _cpu_feasibility_check()
    if cpu_status != "passed":
        logger.warning("CPU feasibility check returned a warning – proceeding anyway.")

    # Load data
    try:
        df_train = _load_processed_data("train")
        df_test = _load_processed_data("test")
    except FileNotFoundError as e:
        logger.error(e)
        return

    # Determine target column (fallback to 'target' if not present)
    possible_targets = ["permeability_coefficient", "logP", "target"]
    target_col = next((c for c in possible_targets if c in df_train.columns), None)
    if not target_col:
        logger.error("No recognised target column found in training data.")
        return

    # Build graph datasets (single‑node graphs as a feasibility study)
    train_graphs = _build_graph_dataset(df_train, target_col=target_col)
    test_graphs = _build_graph_dataset(df_test, target_col=target_col)

    # Split a validation set (10 % of training data)
    val_size = max(1, int(0.1 * len(train_graphs)))
    np.random.seed(42)
    indices = np.random.permutation(len(train_graphs))
    val_idx, train_idx = indices[:val_size], indices[val_size:]
    train_subset = [train_graphs[i] for i in train_idx]
    val_subset = [train_graphs[i] for i in val_idx]

    train_loader = DataLoader(train_subset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_subset, batch_size=32, shuffle=False)
    test_loader = DataLoader(test_graphs, batch_size=32, shuffle=False)

    # Model & optimizer
    in_features = train_graphs[0].x.shape[1]
    model = MPNN(
        input_dim=in_features,
        hidden_dim=64,
        output_dim=1,
        num_layers=3,      # three message‑passing layers as required
        dropout=0.1,
    )
    device = torch.device("cpu")
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    # Training loop with early stopping
    start_time = time.time()
    peak_memory = 0.0
    best_epoch = -1

    for epoch in range(1, 51):  # max 50 epochs
        model.train()
        train_loss = 0.0
        for batch in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            out = model(batch.x, batch.edge_index, batch.batch).squeeze()
            loss = nn.MSELoss()(out, batch.y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * batch.num_graphs
        train_loss /= len(train_loader.dataset)

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(device)
                out = model(batch.x, batch.edge_index, batch.batch).squeeze()
                loss = nn.MSELoss()(out, batch.y)
                val_loss += loss.item() * batch.num_graphs
        val_loss /= len(val_loader.dataset)

        # Update peak memory
        mem = psutil.Process().memory_info().rss / (1024 ** 3)
        peak_memory = max(peak_memory, mem)

        logger.info(f"Epoch {epoch:02d} | Train loss: {train_loss:.4f} | Val loss: {val_loss:.4f}")

        # Early stopping
        if model.early_stop(val_loss):
            break

        # Save best checkpoint
        if val_loss < model.best_val_loss:
            checkpoint_path = Path("code") / "models" / "gnn.pt"
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "val_loss": val_loss,
                },
                checkpoint_path,
            )
            best_epoch = epoch
            logger.info(f"Checkpoint saved (epoch {epoch}).")

    training_time_hours = (time.time() - start_time) / 3600.0

    # Write results to metrics.json (same location as previous script)
    metrics_path = Path("data") / "results" / "metrics.json"
    try:
        if metrics_path.exists():
            with metrics_path.open("r", encoding="utf-8") as f:
                metrics = json.load(f)
        else:
            metrics = {}
    except Exception as e:
        logger.error(f"Failed to read existing metrics.json: {e}")
        metrics = {}

    metrics.setdefault("models", {})
    metrics["models"]["gnn"] = {
        "training_time_hours": training_time_hours,
        "peak_memory_gb": round(peak_memory, 3),
        "best_epoch": best_epoch if best_epoch != -1 else None,
        "patience": 5,
        "max_epochs": 50,
    }

    try:
        with metrics_path.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Training metrics written to {metrics_path}")
    except Exception as e:
        logger.error(f"Failed to write GNN metrics: {e}")

    logger.info("GNN training completed.")

if __name__ == "__main__":
    main()
