"""Inter-family generalization test for 2D material elastic moduli surrogate model.

This module implements the inter-family generalization test (T021a) to measure
Mean Absolute Percentage Error (MAPE) on unseen chemical families. It enforces
that the test set consists of entirely excluded families (no overlap with training).

Output: data/results/generalization_metrics.json
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
import torch
from torch_geometric.data import Data

from model.gnn import LightweightGNN, create_model
from utils.config import get_config
from utils.logger import log_operation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json(path: Path) -> Dict[str, Any]:
    """Load a JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path: Path, data: Dict[str, Any]) -> None:
    """Save data to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def verify_family_disjoint(
    train_indices: List[int],
    test_indices: List[int],
    graphs_df: pd.DataFrame,
    family_column: str = 'family_id'
) -> Tuple[bool, Set[str], Set[str], Set[str]]:
    """Verify that training and test families are disjoint.

    Args:
        train_indices: List of training sample indices.
        test_indices: List of test sample indices.
        graphs_df: DataFrame containing graph data with family_id.
        family_column: Name of the family identifier column.

    Returns:
        Tuple of (is_disjoint, train_families, test_families, intersection).
    """
    train_families = set(graphs_df.iloc[train_indices][family_column].unique())
    test_families = set(graphs_df.iloc[test_indices][family_column].unique())
    intersection = train_families & test_families

    is_disjoint = len(intersection) == 0

    if not is_disjoint:
        logger.error(f"SC-002 Violation: Found {len(intersection)} overlapping families: {intersection}")
        logger.error(f"Train families: {len(train_families)}, Test families: {len(test_families)}")

    return is_disjoint, train_families, test_families, intersection

def load_graphs_from_parquet(path: Path) -> pd.DataFrame:
    """Load graphs from a parquet file into a DataFrame."""
    if not path.exists():
        raise FileNotFoundError(f"Graphs file not found: {path}")
    df = pd.read_parquet(path)
    # Ensure node_features and edge_features are numpy arrays if stored as lists
    if 'node_features' in df.columns:
        df['node_features'] = df['node_features'].apply(
            lambda x: np.array(x) if isinstance(x, list) else x
        )
    if 'edge_features' in df.columns:
        df['edge_features'] = df['edge_features'].apply(
            lambda x: np.array(x) if isinstance(x, list) else x
        )
    return df

def build_family_mapping(
    graphs_df: pd.DataFrame,
    family_column: str = 'family_id'
) -> Dict[int, str]:
    """Build a mapping from index to family_id."""
    return {idx: row[family_column] for idx, row in graphs_df.iterrows()}

def calculate_mape(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    epsilon: float = 1e-8
) -> float:
    """Calculate Mean Absolute Percentage Error.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.
        epsilon: Small value to avoid division by zero.

    Returns:
        MAPE value (0.0 to 1.0+).
    """
    # Handle case where true values might be zero
    mask = np.abs(y_true) > epsilon
    if not np.any(mask):
        logger.warning("No non-zero true values found for MAPE calculation.")
        return 0.0

    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask]))
    return float(mape)

def convert_to_pyg_graph(row: Dict[str, Any]) -> Data:
    """Convert a DataFrame row to a PyTorch Geometric Data object."""
    # Extract features
    x = row['node_features']
    edge_index = row.get('edge_index', np.array([[0, 1], [1, 0]])) # Placeholder if missing
    edge_attr = row.get('edge_features', np.array([[1.0, 0.0]])) # Placeholder if missing

    # Handle edge_index shape (2, num_edges)
    if isinstance(edge_index, np.ndarray):
        edge_index = torch.tensor(edge_index, dtype=torch.long)
    else:
        # Assume it's already a tensor or list of lists
        edge_index = torch.tensor(edge_index, dtype=torch.long)

    x = torch.tensor(x, dtype=torch.float32)
    edge_attr = torch.tensor(edge_attr, dtype=torch.float32)

    # Target
    target_moduli = row.get('target_moduli', {})
    y_young = target_moduli.get('Young', 0.0)
    y_shear = target_moduli.get('Shear', 0.0)
    y_poisson = target_moduli.get('Poisson', 0.0)

    y = torch.tensor([y_young, y_shear, y_poisson], dtype=torch.float32)

    return Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)

def load_model_and_config(
    model_path: Path,
    device: str = 'cpu'
) -> LightweightGNN:
    """Load the trained GNN model."""
    config = get_config()
    # Infer dimensions from config or defaults if not explicitly set in model path
    # Assuming standard dimensions based on T016
    in_dim = 128  # node_features dimension
    hidden_dim = 64
    out_dim = 3   # Young, Shear, Poisson

    model = create_model(in_dim=in_dim, hidden_dim=hidden_dim, out_dim=out_dim)

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    state_dict = torch.load(model_path, map_location=device, weights_only=True)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model

def run_generalization_test(
    graphs_path: Path,
    split_path: Path,
    model_path: Path,
    output_path: Path,
    device: str = 'cpu'
) -> Dict[str, Any]:
    """Run the inter-family generalization test.

    Steps:
    1. Load graphs and split indices.
    2. Verify family disjointness (SC-002).
    3. Load trained model.
    4. Predict on test set.
    5. Calculate MAPE for Young's, Shear, and Poisson ratios.
    6. Save results.
    """
    log_operation("generalization_test_start", paths={"graphs": str(graphs_path), "split": str(split_path)})

    # 1. Load data
    logger.info(f"Loading graphs from {graphs_path}")
    graphs_df = load_graphs_from_parquet(graphs_path)

    logger.info(f"Loading split indices from {split_path}")
    split_data = load_json(split_path)
    train_indices = split_data['train_indices']
    test_indices = split_data['test_indices']

    # 2. Verify family disjointness
    logger.info("Verifying family disjointness (SC-002)...")
    is_disjoint, train_families, test_families, intersection = verify_family_disjoint(
        train_indices, test_indices, graphs_df
    )

    if not is_disjoint:
        raise RuntimeError(f"SC-002 Failed: Train and test sets share families: {intersection}")

    logger.info(f"SC-002 Passed: {len(train_families)} train families, {len(test_families)} test families. No overlap.")

    # 3. Load model
    logger.info(f"Loading model from {model_path}")
    model = load_model_and_config(model_path, device)

    # 4. Prepare test data and predict
    logger.info(f"Processing {len(test_indices)} test samples...")
    test_rows = graphs_df.iloc[test_indices]
    
    y_true_young = []
    y_true_shear = []
    y_true_poisson = []
    y_pred_young = []
    y_pred_shear = []
    y_pred_poisson = []

    with torch.no_grad():
        for idx, row in test_rows.iterrows():
            data = convert_to_pyg_graph(row)
            data = data.to(device)
            
            # Ensure edge_index is 2D
            if data.edge_index.dim() == 1:
                data.edge_index = data.edge_index.unsqueeze(0)
            
            pred = model(data.x.unsqueeze(0), data.edge_index)
            
            true_y = data.y.unsqueeze(0)
            
            y_true_young.append(true_y[0, 0].item())
            y_true_shear.append(true_y[0, 1].item())
            y_true_poisson.append(true_y[0, 2].item())
            
            y_pred_young.append(pred[0, 0].item())
            y_pred_shear.append(pred[0, 1].item())
            y_pred_poisson.append(pred[0, 2].item())

    y_true_young = np.array(y_true_young)
    y_true_shear = np.array(y_true_shear)
    y_true_poisson = np.array(y_true_poisson)
    y_pred_young = np.array(y_pred_young)
    y_pred_shear = np.array(y_pred_shear)
    y_pred_poisson = np.array(y_pred_poisson)

    # 5. Calculate metrics
    mape_young = calculate_mape(y_true_young, y_pred_young)
    mape_shear = calculate_mape(y_true_shear, y_pred_shear)
    mape_poisson = calculate_mape(y_true_poisson, y_pred_poisson)
    mape_overall = (mape_young + mape_shear + mape_poisson) / 3.0

    logger.info(f"Inter-family MAPE - Young: {mape_young:.4f}, Shear: {mape_shear:.4f}, Poisson: {mape_poisson:.4f}, Overall: {mape_overall:.4f}")

    # 6. Construct result
    result = {
        "test_type": "inter_family_generalization",
        "num_test_samples": len(test_indices),
        "num_train_families": len(train_families),
        "num_test_families": len(test_families),
        "family_disjoint": True,
        "metrics": {
            "young_modulus": {"mape": mape_young},
            "shear_modulus": {"mape": mape_shear},
            "poisson_ratio": {"mape": mape_poisson},
            "overall_mape": mape_overall
        },
        "threshold_mape": 0.15,
        "passes_sc002": mape_overall < 0.15,
        "source": "DFT Surrogate Interpolation",
        "disclaimer": "These results are derived from a machine learning surrogate model interpolating pre-computed DFT data. They do not represent first-principles calculations or solutions to the Schrödinger equation."
    }

    # Save results
    logger.info(f"Saving results to {output_path}")
    save_json(output_path, result)

    log_operation("generalization_test_complete", output=str(output_path), mape_overall=mape_overall)

    return result

def main() -> None:
    """Main entry point for the generalization test."""
    parser = argparse.ArgumentParser(description="Run inter-family generalization test.")
    parser.add_argument(
        "--graphs-path",
        type=str,
        default="data/processed/graphs_v1.parquet",
        help="Path to the processed graphs parquet file."
    )
    parser.add_argument(
        "--split-path",
        type=str,
        default="data/processed/split_indices.json",
        help="Path to the split indices JSON file."
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default="data/processed/model_v1.pt",
        help="Path to the trained model weights."
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/results/generalization_metrics.json",
        help="Path to save the generalization metrics JSON."
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Device to run inference on (cpu or cuda)."
    )

    args = parser.parse_args()

    graphs_path = Path(args.graphs_path)
    split_path = Path(args.split_path)
    model_path = Path(args.model_path)
    output_path = Path(args.output_path)

    if not graphs_path.exists():
        logger.error(f"Graphs file not found: {graphs_path}")
        logger.error("Please run the data ingestion pipeline (T013d0) first.")
        return

    if not split_path.exists():
        logger.error(f"Split file not found: {split_path}")
        logger.error("Please run the split generator (T013f) first.")
        return

    if not model_path.exists():
        logger.error(f"Model file not found: {model_path}")
        logger.error("Please run the training script (T018b) first.")
        return

    try:
        run_generalization_test(
            graphs_path=graphs_path,
            split_path=split_path,
            model_path=model_path,
            output_path=output_path,
            device=args.device
        )
        logger.info("Generalization test completed successfully.")
    except Exception as e:
        logger.error(f"Generalization test failed: {e}")
        raise

if __name__ == "__main__":
    main()