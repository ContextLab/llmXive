"""Evaluation metrics for elastic moduli prediction.

Calculates MAPE, RMSE, and R² for Young's, Shear, and Poisson's ratios.
WARNING: This model is a surrogate interpolating pre-computed DFT results.
It does NOT solve the Schrödinger equation or perform first-principles calculations.
"""
import os
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import torch

from model.gnn import create_model
from model.splitter import load_graphs_from_parquet
from utils.logger import get_logger

logger = get_logger(__name__)

def calculate_metrics(preds: np.ndarray, targets: np.ndarray) -> Dict[str, float]:
    """Calculate MAPE, RMSE, R² for a 1D array of values.

    Args:
        preds: Predicted values
        targets: Ground truth values

    Returns:
        Dictionary with 'mape', 'rmse', 'r2' keys
    """
    if len(preds) == 0:
        return {'mape': 0.0, 'rmse': 0.0, 'r2': 0.0}

    eps = 1e-8
    # MAPE
    mape = np.mean(np.abs((preds - targets) / (np.abs(targets) + eps))) * 100
    # RMSE
    rmse = np.sqrt(np.mean((preds - targets) ** 2))
    # R²
    ss_res = np.sum((targets - preds) ** 2)
    ss_tot = np.sum((targets - np.mean(targets)) ** 2)
    r2 = 1 - (ss_res / (ss_tot + eps))

    return {
        'mape': float(mape),
        'rmse': float(rmse),
        'r2': float(r2)
    }

def evaluate_model(
    model_path: Path,
    data_path: Path,
    split_manifest_path: Path,
    device: str = 'cpu'
) -> Dict[str, Any]:
    """Evaluate trained model on test set.

    Loads the model, applies it to the test split defined in the manifest,
    and calculates metrics for Young's, Shear, and Poisson's ratios.

    Args:
        model_path: Path to saved model state dict
        data_path: Path to processed graphs parquet file
        split_manifest_path: Path to split manifest JSON
        device: Device to run inference on

    Returns:
        Dictionary containing metrics per modulus type and sample counts
    """
    logger.info(f"Loading model from {model_path}")
    
    # Initialize model architecture (matching training config)
    # node_dim=1 is a placeholder; real implementation uses feature dim from data
    # We assume the model was trained with specific hidden dims and layers
    model = create_model(node_dim=12, hidden_dim=64, num_layers=2)
    
    state_dict = torch.load(model_path, map_location=device, weights_only=True)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    logger.info(f"Loading data from {data_path}")
    graphs = load_graphs_from_parquet(data_path)
    
    logger.info(f"Loading split manifest from {split_manifest_path}")
    with open(split_manifest_path) as f:
        manifest = json.load(f)
    
    test_ids = set(manifest['test_ids'])
    test_graphs = [g for g in graphs if g['material_id'] in test_ids]
    
    if not test_graphs:
        raise ValueError(f"No test graphs found for IDs in manifest: {test_ids}")

    logger.info(f"Evaluating on {len(test_graphs)} test samples")

    all_preds = {
        'youngs': [],
        'shear': [],
        'poissons': []
    }
    all_targets = {
        'youngs': [],
        'shear': [],
        'poissons': []
    }

    with torch.no_grad():
        for g in test_graphs:
            # Extract features and targets from the graph dict
            # Assuming the graph dict has 'node_features', 'edge_index', 'edge_features', 'target_tensor'
            node_features = torch.tensor(g['node_features'], dtype=torch.float).to(device)
            
            # Reconstruct edge_index and edge_features if present
            edge_index = torch.tensor(g['edge_index'], dtype=torch.long).to(device)
            edge_features = torch.tensor(g.get('edge_features', []), dtype=torch.float).to(device)
            
            # Create batch vector (all zeros for single graph)
            batch = torch.zeros(node_features.shape[0], dtype=torch.long).to(device)
            
            # Prepare input for the model
            # The model expects (x, edge_index, edge_attr, batch)
            # We need to handle edge_attr being potentially empty or 2D
            if edge_features.dim() == 1:
                edge_features = edge_features.unsqueeze(1)
            
            # Run inference
            # Assuming create_model returns a model that takes (x, edge_index, edge_attr, batch)
            try:
                output = model(node_features, edge_index, edge_features, batch)
            except TypeError:
                # Fallback for models that might take different arguments
                # Some implementations might only take x, edge_index, batch
                output = model(node_features, edge_index, batch)
            
            # Output shape: (num_graphs, num_targets) or (num_graphs,)
            # We expect 3 targets: Young's, Shear, Poisson's
            if output.dim() == 1:
                output = output.unsqueeze(0)
            
            pred_vals = output.squeeze().cpu().numpy()
            
            # Extract targets from the graph
            # target_tensor should be [Young's, Shear, Poisson's]
            target_vals = np.array(g['target_tensor'])
            
            # Ensure we have 3 values
            if len(pred_vals) != 3 or len(target_vals) != 3:
                logger.warning(f"Dimension mismatch for {g['material_id']}: pred={len(pred_vals)}, target={len(target_vals)}")
                continue

            all_preds['youngs'].append(pred_vals[0])
            all_preds['shear'].append(pred_vals[1])
            all_preds['poissons'].append(pred_vals[2])

            all_targets['youngs'].append(target_vals[0])
            all_targets['shear'].append(target_vals[1])
            all_targets['poissons'].append(target_vals[2])

    # Convert to numpy arrays
    results = {
        'n_samples': len(test_graphs),
        'metadata': {
            'model_path': str(model_path),
            'data_path': str(data_path),
            'split_manifest_path': str(split_manifest_path),
            'warning': "These results are ML interpolations of DFT data, not first-principles solutions."
        }
    }

    # Calculate metrics for each modulus type
    for key in ['youngs', 'shear', 'poissons']:
        preds_arr = np.array(all_preds[key])
        targets_arr = np.array(all_targets[key])
        
        metrics = calculate_metrics(preds_arr, targets_arr)
        results[f'{key}_metrics'] = metrics
        
        logger.info(f"{key.capitalize()} - MAPE: {metrics['mape']:.2f}%, RMSE: {metrics['rmse']:.4f}, R²: {metrics['r2']:.4f}")

    return results

def main():
    parser = argparse.ArgumentParser(description="Evaluate trained GNN model on test set")
    parser.add_argument('--model', required=True, help='Path to saved model state dict')
    parser.add_argument('--data', required=True, help='Path to processed graphs parquet file')
    parser.add_argument('--split', required=True, help='Path to split manifest JSON')
    parser.add_argument('--output', required=True, help='Path to output JSON file')
    parser.add_argument('--device', default='cpu', help='Device to run inference on')
    
    args = parser.parse_args()

    try:
        results = evaluate_model(
            model_path=Path(args.model),
            data_path=Path(args.data),
            split_manifest_path=Path(args.split),
            device=args.device
        )
        
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Evaluation results saved to {output_path}")
        logger.info(f"Test set size: {results['n_samples']}")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise

if __name__ == '__main__':
    main()