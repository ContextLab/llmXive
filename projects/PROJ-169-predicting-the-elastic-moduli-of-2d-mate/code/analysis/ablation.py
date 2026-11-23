"""
Ablation study runner for intra-family baseline metric generation.

This module computes MAPE/RMSE on random splits within families to establish
a baseline for SC-002 (inter-family generalization).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader as PyGDataLoader
from sklearn.model_selection import train_test_split

# Import existing project modules
from model.gnn import LightweightGNN, create_model
from utils.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
RANDOM_STATE = 42
INTRA_FAMILY_TEST_FRACTION = 0.2
TRAIN_EPOCHS = 5  # Small number for baseline estimation
BATCH_SIZE = 32

class AblationResult:
    """Container for ablation study results."""
    def __init__(
        self,
        family_id: str,
        train_mape: float,
        test_mape: float,
        train_rmse: float,
        test_rmse: float,
        n_train: int,
        n_test: int
    ):
        self.family_id = family_id
        self.train_mape = train_mape
        self.test_mape = test_mape
        self.train_rmse = train_rmse
        self.test_rmse = test_rmse
        self.n_train = n_train
        self.n_test = n_test

    def to_dict(self) -> Dict[str, Any]:
        return {
            "family_id": self.family_id,
            "train_mape": self.train_mape,
            "test_mape": self.test_mape,
            "train_rmse": self.train_rmse,
            "test_rmse": self.test_rmse,
            "n_train": self.n_train,
            "n_test": self.n_test
        }

class BaselineReport:
    """Aggregated baseline report for intra-family performance."""
    def __init__(self):
        self.results: List[AblationResult] = []
        self.avg_test_mape: float = 0.0
        self.avg_test_rmse: float = 0.0
        self.total_families: int = 0

    def add_result(self, result: AblationResult):
        self.results.append(result)

    def compute_aggregates(self):
        if not self.results:
            return
        mape_values = [r.test_mape for r in self.results]
        rmse_values = [r.test_rmse for r in self.results]
        self.avg_test_mape = float(np.mean(mape_values))
        self.avg_test_rmse = float(np.mean(rmse_values))
        self.total_families = len(self.results)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "total_families": self.total_families,
                "avg_test_mape": self.avg_test_mape,
                "avg_test_rmse": self.avg_test_rmse
            },
            "per_family": [r.to_dict() for r in self.results]
        }

def load_graphs_from_parquet(path: str) -> pd.DataFrame:
    """Load graphs from parquet file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Graphs file not found: {path}")
    df = pd.read_parquet(path)
    # Ensure required columns exist
    required_cols = ["node_features", "edge_features", "target_moduli", "family_id"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column in graphs: {col}")
    return df

def convert_to_pyg_graph(row: Any) -> Data:
    """Convert a dataframe row to a PyTorch Geometric Data object."""
    node_features = torch.tensor(row["node_features"], dtype=torch.float32)
    edge_features = torch.tensor(row["edge_features"], dtype=torch.float32)
    # Reconstruct edge_index from edge_features if needed, or assume standard format
    # For this baseline, we assume edge_features contains [src, dst, weight] or similar
    # If edge_features is just a list of floats, we need a mapping.
    # Based on typical GNN data, we assume edge_index is derived or stored.
    # If not, we create a dummy fully connected or simple graph structure for baseline.
    # However, the spec says edge_features is List[List[float32]].
    # We need an edge_index. If not present, we cannot build a valid graph.
    # Assumption: The parquet schema includes an 'edge_index' or we derive it.
    # Since the task description doesn't specify edge_index in the row, we check for it.
    # If missing, we might need to reconstruct from node count or use a dummy.
    # Let's assume the parquet has 'edge_index' as well, or we derive it from 'edge_features' structure.
    # For robustness, we check for 'edge_index'. If missing, we raise an error or create dummy.
    # Given the strict constraints, we assume the data loader (T013d4) produced a valid 'edge_index'.
    # If the column is missing, we try to infer or fail loudly.
    if "edge_index" in row:
        edge_index = torch.tensor(row["edge_index"], dtype=torch.long).t().contiguous()
    else:
        # Fallback: create a dummy star graph or fail.
        # To avoid silent fabrication, we fail if edge_index is missing.
        raise ValueError("Edge index not found in graph row. Cannot build PyG Data.")

    # Target: Young's modulus from target_moduli dict
    target = float(row["target_moduli"].get("Young", row["target_moduli"].get("E", 0.0)))

    return Data(
        x=node_features,
        edge_index=edge_index,
        edge_attr=edge_features,
        y=torch.tensor([target], dtype=torch.float32),
        family_id=row["family_id"]
    )

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float]:
    """Calculate MAPE and RMSE."""
    # Avoid division by zero
    mask = y_true != 0
    if not np.any(mask):
        return 0.0, 0.0
    y_true_mask = y_true[mask]
    y_pred_mask = y_pred[mask]

    mape = np.mean(np.abs((y_true_mask - y_pred_mask) / y_true_mask)) * 100
    rmse = np.sqrt(np.mean((y_true_mask - y_pred_mask) ** 2))
    return float(mape), float(rmse)

def train_epoch(model: LightweightGNN, loader: PyGDataLoader, optimizer: torch.optim.Optimizer, device: torch.device) -> float:
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        out = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
        loss = torch.nn.functional.mse_loss(out.squeeze(), batch.y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * batch.num_graphs
    return total_loss / len(loader.dataset)

def evaluate_model(model: LightweightGNN, loader: PyGDataLoader, device: torch.device) -> Tuple[np.ndarray, np.ndarray]:
    """Evaluate model and return predictions and targets."""
    model.eval()
    preds = []
    targets = []
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
            preds.extend(out.squeeze().cpu().numpy().tolist())
            targets.extend(batch.y.squeeze().cpu().numpy().tolist())
    return np.array(preds), np.array(targets)

def run_ablation_study_for_family(
    family_graphs: List[Dict],
    family_id: str,
    device: torch.device
) -> Optional[AblationResult]:
    """Run intra-family baseline for a single family."""
    if len(family_graphs) < 4:  # Need at least 4 for split
        logger.warning(f"Family {family_id} too small ({len(family_graphs)}). Skipping.")
        return None

    # Convert to PyG
    pyg_graphs = [convert_to_pyg_graph(row) for row in family_graphs]

    # Split within family
    train_idx, test_idx = train_test_split(
        list(range(len(pyg_graphs))),
        test_size=INTRA_FAMILY_TEST_FRACTION,
        random_state=RANDOM_STATE
    )

    train_data = [pyg_graphs[i] for i in train_idx]
    test_data = [pyg_graphs[i] for i in test_idx]

    if not train_data or not test_data:
        return None

    train_loader = PyGDataLoader(train_data, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = PyGDataLoader(test_data, batch_size=BATCH_SIZE, shuffle=False)

    # Create model
    # Assuming node_features dim is 128, edge_features dim is 64 as per spec
    model = create_model(node_dim=128, edge_dim=64, hidden_dim=32, out_dim=1)
    model = model.to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    # Train
    for epoch in range(TRAIN_EPOCHS):
        train_epoch(model, train_loader, optimizer, device)

    # Evaluate
    y_pred, y_true = evaluate_model(model, test_loader, device)

    mape, rmse = calculate_metrics(y_true, y_pred)

    # Also evaluate on train for reference
    train_pred, train_true = evaluate_model(model, train_loader, device)
    train_mape, train_rmse = calculate_metrics(train_true, train_pred)

    return AblationResult(
        family_id=family_id,
        train_mape=train_mape,
        test_mape=mape,
        train_rmse=train_rmse,
        test_rmse=rmse,
        n_train=len(train_data),
        n_test=len(test_data)
    )

def run_ablation_study(
    graphs_path: str,
    split_path: str,
    output_path: str
) -> BaselineReport:
    """
    Run full intra-family baseline study.

    This function:
    1. Loads graphs and split indices.
    2. Groups graphs by family_id.
    3. For each family, performs a random train/test split.
    4. Trains a small GNN on the train split.
    5. Evaluates on the test split.
    6. Aggregates results.
    """
    logger.info(f"Loading graphs from {graphs_path}")
    df = load_graphs_from_parquet(graphs_path)

    # Verify split indices if needed, but for intra-family we use all families
    # We group by family_id
    families = df.groupby("family_id")

    device = torch.device("cpu")  # Enforce CPU as per project constraints

    report = BaselineReport()

    for family_id, group in families:
        logger.info(f"Processing family: {family_id} (n={len(group)})")
        result = run_ablation_study_for_family(
            group.to_dict(orient="records"),
            family_id,
            device
        )
        if result:
            report.add_result(result)

    report.compute_aggregates()

    # Save report
    logger.info(f"Saving baseline report to {output_path}")
    with open(output_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)

    return report

def main():
    parser = argparse.ArgumentParser(
        description="Generate intra-family baseline metrics."
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/processed/graphs_v1.parquet",
        help="Path to graphs parquet file."
    )
    parser.add_argument(
        "--split-path",
        type=str,
        default="data/processed/split_indices.json",
        help="Path to split indices JSON (optional for intra-family)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/intra_family_baseline.json",
        help="Output path for baseline report JSON."
    )

    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    try:
        run_ablation_study(
            graphs_path=args.data_path,
            split_path=args.split_path,
            output_path=args.output
        )
        logger.info("Intra-family baseline generation completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise SystemExit(1)
    except Exception as e:
        logger.error(f"Error during ablation study: {e}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()