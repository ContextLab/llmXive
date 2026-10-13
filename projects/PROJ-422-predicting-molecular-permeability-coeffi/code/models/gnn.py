"""
GNN model training script for molecular permeability prediction.

Implements a shallow 2‑layer Message Passing Neural Network (MPNN) with early
stopping (patience 5) and a maximum of 50 epochs. Includes a CPU feasibility
pre‑check that records its result in ``data/results/metrics.json`` under the
key ``cpu_feasibility_check`` (value ``passed`` or ``warning``).
"""
import logging
import time
import json
from pathlib import Path
import psutil
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data, DataLoader
from torch_geometric.nn import MessagePassing, global_mean_pool, global_max_pool
import pandas as pd
import numpy as np

from utils.logging import setup_logging, log_result_artifact

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _cpu_feasibility_check() -> str:
    """Simple CPU feasibility check.

    Returns:
        str: ``'passed'`` if the machine has at least 2 logical CPUs and
             at least 2 GB of free RAM, otherwise ``'warning'``.
    """
    cpu_count = psutil.cpu_count(logical=True)
    mem = psutil.virtual_memory()
    free_gb = mem.available / (1024 ** 3)

    if cpu_count >= 2 and free_gb >= 2:
        status = "passed"
    else:
        status = "warning"

    # Write status to the project's metrics file
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
    """Load processed CSV data for a given split.

    Args:
        split: ``'train'`` or ``'test'``.

    Returns:
        pandas.DataFrame with the processed rows.

    Raises:
        FileNotFoundError: If the expected CSV does not exist.
    """
    csv_path = Path("data") / "processed" / f"{split}.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(f"Processed data file not found: {csv_path}")
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} rows from {csv_path}")
    return df

def _build_graph_dataset(df: pd.DataFrame, target_col: str = "target") -> list:
    """Convert a DataFrame into a list of torch_geometric.Data objects.

    The function assumes that all columns except the target are numeric
    descriptor features. For the purposes of this feasibility study each
    molecule is represented as a *single‑node* graph whose node feature
    vector is the descriptor vector.

    Args:
        df: DataFrame containing descriptor columns and the target.
        target_col: Name of the column containing the regression target.

    Returns:
        List[Data] suitable for torch_geometric.DataLoader.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame.")
    feature_cols = [c for c in df.columns if c != target_col]
    data_list = []
    for _, row in df.iterrows():
        x = torch.tensor(row[feature_cols].values, dtype=torch.float).unsqueeze(0)  # shape [1, F]
        edge_index = torch.empty((2, 0), dtype=torch.long)  # No edges for single‑node graph
        y = torch.tensor([row[target_col]], dtype=torch.float)
        data = Data(x=x, edge_index=edge_index, y=y)
        data_list.append(data)
    logger.info(f"Constructed {len(data_list)} graph objects (single‑node each).")
    return data_list

# ----------------------------------------------------------------------
# Model definition (shallow 2‑layer MPNN)
# ----------------------------------------------------------------------
class MPNNLayer(MessagePassing):
    """Single message‑passing layer using additive aggregation."""
    def __init__(self, in_channels: int, out_channels: int, hidden_channels: int, dropout: float = 0.1):
        super().__init__(aggr="add")
        self.lin_msg = nn.Linear(in_channels, hidden_channels)
        self.lin_update = nn.Linear(hidden_channels + in_channels, out_channels)
        self.dropout = nn.Dropout(dropout)
        self.bn = nn.BatchNorm1d(out_channels)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        msg = self.propagate(edge_index, x=x)               # [N, hidden]
        combined = torch.cat([x, msg], dim=1)               # [N, in+hidden]
        out = self.lin_update(combined)
        out = self.bn(out)
        out = F.relu(out)
        out = self.dropout(out)
        return out

    def message(self, x_j: torch.Tensor) -> torch.Tensor:
        return F.relu(self.lin_msg(x_j))

class MPNN(nn.Module):
    """Two‑layer MPNN with mean & max readout."""
    def __init__(self, in_features: int, hidden_channels: int = 64, dropout: float = 0.1):
        super().__init__()
        self.input_proj = nn.Linear(in_features, hidden_channels)
        # Two layers as required by the task
        self.mpnn1 = MPNNLayer(hidden_channels, hidden_channels, hidden_channels, dropout)
        self.mpnn2 = MPNNLayer(hidden_channels, hidden_channels, hidden_channels, dropout)

        self.readout = nn.Sequential(
            nn.Linear(hidden_channels * 2, hidden_channels),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_channels, 1)
        )

        # Early‑stopping state
        self.best_val_loss = float("inf")
        self.patience = 5
        self.counter = 0

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, batch: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.input_proj(x))
        x = self.mpnn1(x, edge_index)
        x = self.mpnn2(x, edge_index)

        mean = global_mean_pool(x, batch)
        max_ = global_max_pool(x, batch)
        graph_repr = torch.cat([mean, max_], dim=1)
        out = self.readout(graph_repr)
        return out

    def early_stop(self, val_loss: float) -> bool:
        """Update early‑stopping counters.

        Returns:
            bool: ``True`` if training should stop.
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
# Training utilities
# ----------------------------------------------------------------------
def train_one_epoch(model: MPNN, loader: DataLoader, optimizer, device):
    model.train()
    total_loss = 0.0
    criterion = nn.MSELoss()
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        out = model(batch.x, batch.edge_index, batch.batch).squeeze()
        loss = criterion(out, batch.y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * batch.num_graphs
    return total_loss / len(loader.dataset)

def evaluate(model: MPNN, loader: DataLoader, device):
    model.eval()
    total_loss = 0.0
    criterion = nn.MSELoss()
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index, batch.batch).squeeze()
            loss = criterion(out, batch.y)
            total_loss += loss.item() * batch.num_graphs
    return total_loss / len(loader.dataset)

# ----------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------
def main():
    """
    Entry point for the GNN training script.

    The script:
    1. Performs a CPU feasibility pre‑check and records the result.
    2. Loads ``data/processed/train.csv`` and ``data/processed/test.csv``.
    3. Constructs single‑node graph objects from descriptor columns.
    4. Trains a 2‑layer MPNN (max 50 epochs, early stopping patience 5).
    5. Saves the best checkpoint under ``data/interim/gnn_best.pt``.
    6. Logs training time and peak memory usage to ``data/results/metrics.json``.
    """
    # ------------------------------------------------------------------
    # Logging & CPU check
    # ------------------------------------------------------------------
    setup_logging(task_id="T004")
    logger.info("Starting GNN training script (T004).")
    cpu_status = _cpu_feasibility_check()
    if cpu_status != "passed":
        logger.warning("CPU feasibility check returned a warning – proceeding anyway.")

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Build graph datasets
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Model & optimizer
    # ------------------------------------------------------------------
    in_features = train_graphs[0].x.shape[1]
    model = MPNN(in_features=in_features, hidden_channels=64, dropout=0.1)
    device = torch.device("cpu")
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    # ------------------------------------------------------------------
    # Training loop
    # ------------------------------------------------------------------
    start_time = time.time()
    peak_memory = 0.0
    best_epoch = -1

    for epoch in range(1, 51):  # max 50 epochs
        train_loss = train_one_epoch(model, train_loader, optimizer, device)
        val_loss = evaluate(model, val_loader, device)

        # Update peak memory (in GB)
        mem = psutil.Process().memory_info().rss / (1024 ** 3)
        peak_memory = max(peak_memory, mem)

        logger.info(f"Epoch {epoch:02d} | Train loss: {train_loss:.4f} | Val loss: {val_loss:.4f}")

        # Early stopping check
        if model.early_stop(val_loss):
            break

        # Save checkpoint if this is the best validation loss so far
        if val_loss < model.best_val_loss:
            checkpoint_path = Path("data") / "interim" / "gnn_best.pt"
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "val_loss": val_loss
            }, checkpoint_path)
            best_epoch = epoch
            logger.info(f"Checkpoint saved (epoch {epoch}).")

    training_time_hours = (time.time() - start_time) / 3600.0

    # ------------------------------------------------------------------
    # Write results to metrics.json
    # ------------------------------------------------------------------
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
        "max_epochs": 50
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
