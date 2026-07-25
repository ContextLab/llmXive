import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
import torch
from torch_geometric.data import Data

from config import AnalysisConfig, TrainingConfig, ensure_dirs
from utils.logger import setup_logging, get_logger
from models.mpnn import MPNN, create_mpnn_from_config, MPNNConfig
from data.descriptors import compute_gasteiger_charges, compute_topological_indices

# Import SHAP if available, otherwise handle gracefully
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logging.warning("SHAP not available. Perturbation study will skip SHAP-based ranking.")

def load_model_and_weights(model_path: str, config: MPNNConfig) -> MPNN:
    """Load a trained MPNN model from disk."""
    logger = get_logger(__name__)
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model weights not found at {model_path}")
    
    model = create_mpnn_from_config(config)
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    model.eval()
    logger.info(f"Loaded model from {model_path}")
    return model

def load_processed_data(data_path: str) -> pd.DataFrame:
    """Load the cleaned dataset."""
    logger = get_logger(__name__)
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed data not found at {data_path}")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} rows from {data_path}")
    return df

def prepare_graph_features(row: pd.Series) -> Optional[Data]:
    """Convert a dataframe row to a PyTorch Geometric Data object."""
    try:
        smiles = row['smiles']
        # Extract features computed during preprocessing
        # Assuming columns: gasteiger_charges (list), topological_indices (list)
        # and node_features derived from these
        
        # For perturbation study, we need node-level features
        # This is a simplified approach; in reality, node features would be more complex
        gasteiger = row.get('gasteiger_charges', [])
        topo = row.get('topological_indices', [])
        
        if not gasteiger or not topo:
            return None
        
        # Create node features: concatenate gasteiger charges and topological indices
        # This is a placeholder; actual implementation would use RDKit to generate proper node features
        node_features = []
        for i, g in enumerate(gasteiger):
            node_features.append([g, topo[i] if i < len(topo) else 0.0])
        
        node_features = np.array(node_features, dtype=np.float32)
        
        # Create an empty graph (no edges for simplicity in this perturbation study)
        # In a real scenario, edges would be derived from molecular connectivity
        edge_index = torch.tensor([[], []], dtype=torch.long)
        
        data = Data(x=torch.tensor(node_features), edge_index=edge_index)
        data.y = torch.tensor([row['rate_constant']], dtype=torch.float32)
        data.smiles = smiles
        return data
    except Exception as e:
        logging.error(f"Failed to prepare graph features for {row.get('smiles', 'unknown')}: {e}")
        return None

def run_inference(model: MPNN, graph: Data) -> float:
    """Run inference on a single graph."""
    model.eval()
    with torch.no_grad():
        output = model(graph.x.unsqueeze(0), graph.edge_index.unsqueeze(0) if graph.edge_index.numel() > 0 else None)
        return output.squeeze().item()

def calculate_r2(predictions: List[float], targets: List[float]) -> float:
    """Calculate R² score."""
    if len(predictions) != len(targets) or len(predictions) == 0:
        return 0.0
    
    mean_target = np.mean(targets)
    ss_tot = sum((y - mean_target) ** 2 for y in targets)
    ss_res = sum((y - pred) ** 2 for y, pred in zip(targets, predictions))
    
    if ss_tot == 0:
        return 1.0
    
    return 1 - (ss_res / ss_tot)

def get_shap_rankings(model: MPNN, graphs: List[Data], targets: List[float]) -> Optional[np.ndarray]:
    """
    Compute node-level SHAP values for the model.
    Returns an array of SHAP values for each node in each graph.
    """
    if not SHAP_AVAILABLE:
        logging.warning("SHAP not available. Using gradient-based attribution as fallback.")
        # Fallback: use gradient of output w.r.t. input nodes
        model.eval()
        shap_values = []
        for graph in graphs:
            graph.x.requires_grad_(True)
            output = model(graph.x.unsqueeze(0), graph.edge_index.unsqueeze(0) if graph.edge_index.numel() > 0 else None)
            output.backward(torch.ones_like(output))
            shap_values.append(graph.x.grad.abs().detach().numpy())
            graph.x.requires_grad_(False)
        return shap_values
    
    # Use SHAP's DeepExplainer if available
    try:
        # Simplified SHAP computation for graph data
        # In practice, this would require a proper graph SHAP implementation
        explainer = shap.DeepExplainer(model, torch.randn(10, model.config.input_dim))
        # This is a placeholder; actual implementation would be more complex
        return None
    except Exception as e:
        logging.error(f"SHAP computation failed: {e}")
        return None

def perform_perturbation_study(
    model: MPNN,
    graphs: List[Data],
    targets: List[float],
    shap_values: Optional[List[np.ndarray]],
    top_k: int = 5,
    threshold: float = 0.1
) -> Dict[str, Any]:
    """
    Perform perturbation study by masking top SHAP-ranked nodes.
    
    Args:
        model: Trained MPNN model
        graphs: List of graph data objects
        targets: True target values
        shap_values: List of node-level SHAP values (or gradients)
        top_k: Number of top nodes to mask per graph
        threshold: Minimum absolute SHAP value to consider a node important
    
    Returns:
        Dictionary with perturbation results
    """
    logger = get_logger(__name__)
    logger.info(f"Starting perturbation study on {len(graphs)} molecules")
    
    # Baseline predictions (unmasked)
    baseline_predictions = []
    for graph in graphs:
        pred = run_inference(model, graph)
        baseline_predictions.append(pred)
    
    baseline_r2 = calculate_r2(baseline_predictions, targets)
    logger.info(f"Baseline R²: {baseline_r2:.4f}")
    
    # Perturbed predictions (masked top nodes)
    perturbed_predictions = []
    perturbation_details = []
    
    for i, (graph, shap_vals) in enumerate(zip(graphs, shap_values)):
        if shap_vals is None or shap_vals.shape[0] == 0:
            # No SHAP values, skip perturbation for this graph
            perturbed_predictions.append(baseline_predictions[i])
            perturbation_details.append({
                'row_index': i,
                'smiles': graph.smiles,
                'n_nodes': 0,
                'n_masked': 0,
                'original_pred': baseline_predictions[i],
                'perturbed_pred': baseline_predictions[i],
                'pred_drop': 0.0,
                'reason': 'no_shap_values'
            })
            continue
        
        # Identify top nodes to mask
        # shap_vals shape: (n_nodes, n_features)
        node_importance = np.sum(np.abs(shap_vals), axis=1)  # Aggregate across features
        
        # Select nodes with |SHAP| > threshold OR top_k nodes
        important_nodes = np.where(node_importance > threshold)[0]
        if len(important_nodes) > top_k:
            top_nodes = np.argsort(node_importance)[-top_k:]
        else:
            top_nodes = important_nodes
        
        # Create masked graph
        masked_graph = Data(
            x=graph.x.clone(),
            edge_index=graph.edge_index.clone(),
            y=graph.y.clone()
        )
        masked_graph.smiles = graph.smiles
        
        # Zero out features for selected nodes
        for node_idx in top_nodes:
            masked_graph.x[node_idx] = 0.0
        
        # Run inference on masked graph
        perturbed_pred = run_inference(model, masked_graph)
        perturbed_predictions.append(perturbed_pred)
        
        # Record details
        pred_drop = abs(baseline_predictions[i] - perturbed_pred)
        perturbation_details.append({
            'row_index': i,
            'smiles': graph.smiles,
            'n_nodes': len(node_importance),
            'n_masked': len(top_nodes),
            'original_pred': baseline_predictions[i],
            'perturbed_pred': perturbed_pred,
            'pred_drop': pred_drop,
            'reason': 'nodes_masked'
        })
    
    # Calculate perturbed R²
    perturbed_r2 = calculate_r2(perturbed_predictions, targets)
    logger.info(f"Perturbed R²: {perturbed_r2:.4f}")
    logger.info(f"R² drop: {baseline_r2 - perturbed_r2:.4f}")
    
    # Aggregate results
    results = {
        'baseline_r2': baseline_r2,
        'perturbed_r2': perturbed_r2,
        'r2_drop': baseline_r2 - perturbed_r2,
        'mean_pred_drop': np.mean([d['pred_drop'] for d in perturbation_details]),
        'total_molecules': len(graphs),
        'molecules_with_shap': sum(1 for d in perturbation_details if d['reason'] == 'nodes_masked'),
        'details': perturbation_details
    }
    
    return results

def run_interpretability_analysis(
    model_path: str,
    data_path: str,
    output_path: str,
    top_k: int = 5,
    threshold: float = 0.1
) -> None:
    """
    Main function to run the full interpretability and perturbation analysis.
    
    Args:
        model_path: Path to saved model weights
        data_path: Path to cleaned dataset
        output_path: Path to save perturbation results
        top_k: Number of top nodes to mask
        threshold: Minimum SHAP value for node importance
    """
    logger = get_logger(__name__)
    ensure_dirs()
    
    # Load configuration
    config = TrainingConfig()
    model_config = MPNNConfig(
        input_dim=config.input_dim,
        hidden_dim=config.hidden_dim,
        output_dim=1,
        num_layers=config.num_layers,
        dropout=config.dropout
    )
    
    # Load model
    logger.info("Loading model...")
    model = load_model_and_weights(model_path, model_config)
    
    # Load data
    logger.info("Loading data...")
    df = load_processed_data(data_path)
    
    # Prepare graphs
    logger.info("Preparing graph features...")
    graphs = []
    valid_indices = []
    for idx, row in df.iterrows():
        graph = prepare_graph_features(row)
        if graph is not None:
            graphs.append(graph)
            valid_indices.append(idx)
    
    logger.info(f"Prepared {len(graphs)} valid graphs out of {len(df)} rows")
    
    if len(graphs) == 0:
        logger.error("No valid graphs prepared. Exiting.")
        return
    
    targets = [graph.y.item() for graph in graphs]
    
    # Compute SHAP values
    logger.info("Computing SHAP values...")
    shap_values = get_shap_rankings(model, graphs, targets)
    
    # Perform perturbation study
    logger.info("Performing perturbation study...")
    results = perform_perturbation_study(
        model, graphs, targets, shap_values, top_k=top_k, threshold=threshold
    )
    
    # Save results
    logger.info(f"Saving results to {output_path}")
    output_df = pd.DataFrame(results['details'])
    output_df.to_csv(output_path, index=False)
    
    # Also save summary
    summary_path = output_path.replace('.csv', '_summary.json')
    with open(summary_path, 'w') as f:
        json.dump({
            'baseline_r2': results['baseline_r2'],
            'perturbed_r2': results['perturbed_r2'],
            'r2_drop': results['r2_drop'],
            'mean_pred_drop': results['mean_pred_drop'],
            'total_molecules': results['total_molecules'],
            'molecules_with_shap': results['molecules_with_shap']
        }, f, indent=2)
    
    logger.info(f"Perturbation study complete. R² dropped from {results['baseline_r2']:.4f} to {results['perturbed_r2']:.4f}")

def main():
    parser = argparse.ArgumentParser(description='Run perturbation study for model interpretability')
    parser.add_argument('--model-path', type=str, required=True, help='Path to model weights')
    parser.add_argument('--data-path', type=str, required=True, help='Path to cleaned dataset')
    parser.add_argument('--output-path', type=str, default='artifacts/perturbation_results.csv', help='Path to save results')
    parser.add_argument('--top-k', type=int, default=5, help='Number of top nodes to mask')
    parser.add_argument('--threshold', type=float, default=0.1, help='Minimum SHAP value for node importance')
    parser.add_argument('--log-level', type=str, default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    setup_logging(level=args.log_level)
    run_interpretability_analysis(
        model_path=args.model_path,
        data_path=args.data_path,
        output_path=args.output_path,
        top_k=args.top_k,
        threshold=args.threshold
    )

if __name__ == '__main__':
    main()