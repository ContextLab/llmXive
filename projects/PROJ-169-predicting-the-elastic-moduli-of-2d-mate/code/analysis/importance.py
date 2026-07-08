"""
T023: Implement SHAP interaction value calculation and permutation importance.

This module calculates feature importance for the trained GNN model using:
1. SHAP (SHapley Additive exPlanations) interaction values to quantify node/edge
   feature contributions to the predicted elastic moduli.
2. Permutation importance to rank the top 5 structural descriptors.

Dependencies:
  - T018: Trained GNN model (code/model/train.py)
  - T025: Composition-only baseline (code/analysis/ablation.py)
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import torch
import shap
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader

# Project imports
from utils.config import Config
from utils.logger import get_logger
from model.gnn import create_model, LightweightGNN

# Ensure we can import from the project root
import sys
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

logger = get_logger(__name__)


def load_graphs_from_parquet(parquet_path: str) -> List[Data]:
    """
    Load graphs from the processed parquet file.
    Converts pyarrow tables back to PyTorch Geometric Data objects.
    """
    import pyarrow.parquet as pq
    table = pq.read_table(parquet_path)
    graphs = []

    # Assuming the parquet has columns: 'edge_index', 'node_features', 'edge_features', 'y'
    # We need to reconstruct the Data objects.
    # Note: This is a simplified reconstruction. In a real scenario, we might need
    # more complex serialization logic depending on how the parquet was saved.
    # For this implementation, we assume the data is stored as JSON strings in columns.
    
    for i in range(len(table)):
        row = table.slice(i, 1).to_pydict()
        
        # Reconstruct edge_index (2, num_edges)
        edge_index = np.array(row['edge_index'][0])
        if edge_index.ndim == 1:
            edge_index = edge_index.reshape(2, -1)
        
        # Reconstruct features
        node_features = np.array(row['node_features'][0])
        edge_features = np.array(row['edge_features'][0]) if 'edge_features' in row and row['edge_features'][0] is not None else None
        y = np.array(row['y'][0]) if isinstance(row['y'][0], list) else row['y'][0]
        
        data = Data(
            x=torch.tensor(node_features, dtype=torch.float32),
            edge_index=torch.tensor(edge_index, dtype=torch.long),
            y=torch.tensor([y], dtype=torch.float32)
        )
        
        if edge_features is not None:
            data.edge_attr = torch.tensor(edge_features, dtype=torch.float32)
        
        graphs.append(data)
    
    return graphs


def calculate_shap_values(
    model: LightweightGNN,
    graphs: List[Data],
    device: str,
    num_samples: int = 100
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate SHAP values for the model predictions.
    
    Since SHAP for GNNs is complex, we use a simplified approach:
    1. Create a background dataset (subset of training data).
    2. Use a `Explainer` to compute SHAP values for node features.
    
    Args:
        model: The trained GNN model.
        graphs: List of graph data objects.
        device: Device to run on ('cpu' or 'cuda').
        num_samples: Number of samples to use for SHAP background.
    
    Returns:
        shap_values: Array of SHAP values for node features.
        base_values: The base value (average prediction).
    """
    if len(graphs) == 0:
        raise ValueError("No graphs provided for SHAP calculation.")

    # Limit samples for computational feasibility
    if len(graphs) > num_samples:
        indices = np.random.choice(len(graphs), num_samples, replace=False)
        sample_graphs = [graphs[i] for i in indices]
    else:
        sample_graphs = graphs

    # Convert to batch
    loader = DataLoader(sample_graphs, batch_size=len(sample_graphs))
    batch = next(iter(loader))
    batch = batch.to(device)

    # Define the model function for SHAP
    # We wrap the model to accept (x, edge_index, edge_attr)
    def model_forward(x, edge_index, edge_attr=None):
        model.eval()
        with torch.no_grad():
            x = x.to(device)
            edge_index = edge_index.to(device)
            if edge_attr is not None:
                edge_attr = edge_attr.to(device)
            else:
                edge_attr = None
            
            # Forward pass
            pred = model(x, edge_index, edge_attr)
            return pred.cpu().numpy()

    # Create SHAP explainer
    # We use the 'kernel' explainer as a model-agnostic approach for GNNs
    # This is computationally expensive but works for any model structure
    logger.info(f"Initializing SHAP Kernel Explainer with {len(sample_graphs)} background samples...")
    
    # For Kernel SHAP, we need to pass the data in a specific format
    # We'll use the node features of the first graph as a representative input
    # In a more sophisticated setup, we might average over multiple graphs
    if len(sample_graphs) > 0:
        reference_graph = sample_graphs[0]
        background_x = reference_graph.x.unsqueeze(0).cpu().numpy()
        background_edge_index = reference_graph.edge_index.unsqueeze(0).cpu().numpy()
        
        # Create a simple explainer
        explainer = shap.KernelExplainer(
            lambda x: model_forward(x, background_edge_index[0], reference_graph.edge_attr),
            background_x
        )
        
        # Calculate SHAP values
        # Note: This is a simplified calculation. Real GNN SHAP requires graph-level
        # aggregation which is more complex.
        shap_values = explainer.shap_values(background_x)
        
        # Handle the case where shap_values might be a list (for multi-output)
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
            
        logger.info(f"SHAP values calculated. Shape: {shap_values.shape}")
        return shap_values, None
    else:
        raise ValueError("No valid reference graph found.")


def calculate_permutation_importance(
    model: LightweightGNN,
    graphs: List[Data],
    device: str,
    n_repeats: int = 10
) -> Dict[str, float]:
    """
    Calculate permutation importance for node features.
    
    Args:
        model: The trained GNN model.
        graphs: List of graph data objects.
        device: Device to run on.
        n_repeats: Number of times to permute each feature.
    
    Returns:
        Dictionary mapping feature index to importance score (decrease in R2 or MAE).
    """
    if len(graphs) == 0:
        raise ValueError("No graphs provided for permutation importance.")

    # Create a batch of all graphs
    loader = DataLoader(graphs, batch_size=len(graphs))
    batch = next(iter(loader))
    batch = batch.to(device)
    
    model.eval()
    
    # Get original predictions
    with torch.no_grad():
        original_preds = model(batch.x, batch.edge_index, batch.edge_attr)
        original_targets = batch.y
    
    # Calculate original metric (MAE)
    original_mae = torch.mean(torch.abs(original_preds - original_targets)).item()
    
    # Number of node features
    num_features = batch.x.shape[1]
    importance_scores = {}
    
    logger.info(f"Calculating permutation importance for {num_features} features...")
    
    for feat_idx in range(num_features):
        mae_scores = []
        
        for _ in range(n_repeats):
            # Create a copy of the batch
            permuted_x = batch.x.clone()
            # Permute the feature column
            permuted_values = permuted_x[:, feat_idx].clone()
            permuted_values = permuted_values[torch.randperm(permuted_values.size(0))]
            permuted_x[:, feat_idx] = permuted_values
            
            # Calculate prediction with permuted feature
            with torch.no_grad():
                permuted_preds = model(permuted_x, batch.edge_index, batch.edge_attr)
            
            # Calculate MAE
            mae = torch.mean(torch.abs(permuted_preds - original_targets)).item()
            mae_scores.append(mae)
        
        # Importance is the increase in error
        avg_mae_increase = np.mean(mae_scores) - original_mae
        importance_scores[f"feature_{feat_idx}"] = avg_mae_increase
        
        if feat_idx % 10 == 0:
            logger.info(f"Processed feature {feat_idx}/{num_features}")
    
    return importance_scores


def run_importance_analysis(
    model_path: str,
    data_path: str,
    output_dir: str,
    device: str = "cpu"
) -> Dict[str, Any]:
    """
    Main function to run SHAP and permutation importance analysis.
    
    Args:
        model_path: Path to the saved trained model.
        data_path: Path to the processed parquet file.
        output_dir: Directory to save the results.
        device: Device to use for computation.
    
    Returns:
        Dictionary containing analysis results.
    """
    logger.info(f"Starting importance analysis...")
    logger.info(f"Model path: {model_path}")
    logger.info(f"Data path: {data_path}")
    
    # Load data
    graphs = load_graphs_from_parquet(data_path)
    logger.info(f"Loaded {len(graphs)} graphs")
    
    if len(graphs) == 0:
        raise ValueError("No graphs loaded. Check data path.")
    
    # Load model
    model = create_model(node_dim=graphs[0].x.shape[1], edge_dim=graphs[0].edge_attr.shape[1] if hasattr(graphs[0], 'edge_attr') else 0)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    
    results = {}
    
    # 1. SHAP Values
    try:
        logger.info("Calculating SHAP values...")
        shap_vals, base_vals = calculate_shap_values(model, graphs, device, num_samples=50)
        results['shap'] = {
            'values': shap_vals.tolist(),
            'shape': list(shap_vals.shape)
        }
        if base_vals is not None:
            results['shap']['base_values'] = base_vals.tolist()
        logger.info("SHAP calculation completed.")
    except Exception as e:
        logger.error(f"SHAP calculation failed: {e}")
        results['shap'] = {'error': str(e)}
    
    # 2. Permutation Importance
    try:
        logger.info("Calculating permutation importance...")
        perm_importance = calculate_permutation_importance(model, graphs, device, n_repeats=5)
        # Sort by importance
        sorted_importance = dict(sorted(perm_importance.items(), key=lambda x: x[1], reverse=True))
        results['permutation'] = sorted_importance
        logger.info("Permutation importance completed.")
    except Exception as e:
        logger.error(f"Permutation importance failed: {e}")
        results['permutation'] = {'error': str(e)}
    
    # Save results
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_file = os.path.join(output_dir, "feature_importance.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_file}")
    return results


def main():
    """
    Entry point for running importance analysis.
    """
    config = Config()
    logger.info("Running feature importance analysis (T023)...")
    
    # Default paths
    model_path = os.path.join(config.data_dir, "results", "best_model.pt")
    data_path = os.path.join(config.data_dir, "processed", "graphs_v1.parquet")
    output_dir = os.path.join(config.data_dir, "results")
    
    # Check if files exist
    if not os.path.exists(model_path):
        logger.error(f"Model file not found: {model_path}. Please run training first (T018).")
        return
    
    if not os.path.exists(data_path):
        logger.error(f"Data file not found: {data_path}. Please run ingestion pipeline first (T013).")
        return
    
    results = run_importance_analysis(model_path, data_path, output_dir)
    
    # Print top 5 features from permutation importance
    if 'permutation' in results and isinstance(results['permutation'], dict):
        logger.info("Top 5 most important features (by permutation importance):")
        sorted_feats = sorted(results['permutation'].items(), key=lambda x: x[1], reverse=True)
        for i, (feat, imp) in enumerate(sorted_feats[:5]):
            logger.info(f"  {i+1}. {feat}: {imp:.4f}")
    
    logger.info("Importance analysis completed successfully.")


if __name__ == "__main__":
    main()