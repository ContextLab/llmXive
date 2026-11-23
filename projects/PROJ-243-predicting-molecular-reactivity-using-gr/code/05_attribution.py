"""
Attribution Analysis for Molecular Reactivity Prediction.

This script implements GNNExplainer or gradient-based methods to generate
importance scores for the trained models on the preprocessed graph data.
It loads the final graphs, splits, and trained model weights, then computes
attributions for the predictions.

Deliverable: Intermediate importance scores saved to artifacts/attribution_scores.json
"""
import os
import sys
import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple

import torch
import torch.nn.functional as F
from torch_geometric.data import Batch
from torch_geometric.explain import GNNExplainer
import numpy as np
import pandas as pd

# Local imports based on API surface
from config import get_config, ensure_directories
from serialization import load_intermediate_graphs, load_split_indices
from models.spectral_gnn import SpectralGNN
from models.hetero_gnn import HeteroGNN
# Note: Random Forest baseline attribution is handled differently (feature importance)
# and might be aggregated separately if needed, but GNNExplainer is the primary focus here.

def setup_script_logging() -> logging.Logger:
    """Setup logging for the attribution script."""
    logger = logging.getLogger("attribution")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_model_weights(
    model_type: str,
    weights_path: str,
    input_dim: int,
    hidden_dim: int,
    output_dim: int
) -> torch.nn.Module:
    """
    Load trained model weights.
    
    Args:
        model_type: 'spectral_gnn' or 'hetero_gnn'
        weights_path: Path to the .pt file
        input_dim: Input feature dimension
        hidden_dim: Hidden layer dimension
        output_dim: Output dimension (1 for regression)
        
    Returns:
        Loaded model instance with weights
    """
    logger = logging.getLogger("attribution")
    
    if model_type == 'spectral_gnn':
        model = SpectralGNN(input_dim, hidden_dim, output_dim)
    elif model_type == 'hetero_gnn':
        model = HeteroGNN(input_dim, hidden_dim, output_dim)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
        
    if not os.path.exists(weights_path):
        raise FileNotFoundError(f"Model weights not found at {weights_path}")
        
    try:
        state_dict = torch.load(weights_path, map_location='cpu', weights_only=True)
        model.load_state_dict(state_dict)
        model.eval()
        logger.info(f"Successfully loaded {model_type} weights from {weights_path}")
    except Exception as e:
        logger.error(f"Failed to load weights from {weights_path}: {e}")
        raise
        
    return model

def compute_attribution_for_batch(
    model: torch.nn.Module,
    batch: Batch,
    explainer: GNNExplainer,
    node_idx: Optional[int] = None,
    target_idx: Optional[int] = None
) -> Dict[str, Any]:
    """
    Compute attribution scores for a batch of graphs.
    
    Args:
        model: The trained GNN model
        batch: Batch of graphs
        explainer: GNNExplainer instance
        node_idx: Specific node index to explain (if None, explain all nodes)
        target_idx: Specific target index to explain (if None, explain all targets)
        
    Returns:
        Dictionary containing attribution scores
    """
    logger = logging.getLogger("attribution")
    
    model.eval()
    with torch.no_grad():
        # Forward pass to get predictions
        out = model(batch.x, batch.edge_index, batch.batch)
        
        # Determine target for explanation
        # For regression, we explain the prediction value
        if target_idx is not None:
            target = out[target_idx]
        else:
            # Explain all predictions
            target = out
            
        # Run explainer
        # Note: GNNExplainer expects a specific node index for node-level tasks
        # For graph-level tasks, we might need to aggregate or use a specific node
        # Here we assume graph-level explanation by explaining the 'graph' node or aggregating
        
        # Simplified approach: Explain the prediction for the first graph in the batch
        # or aggregate if batch size is 1
        graph_idx = 0
        if batch.num_graphs > 0:
            # Get the node range for the first graph
            start_node = batch.ptr[graph_idx]
            end_node = batch.ptr[graph_idx + 1] if graph_idx + 1 < len(batch.ptr) else batch.x.shape[0]
            
            # Select nodes for the first graph
            node_mask = torch.zeros(batch.x.shape[0], dtype=torch.bool)
            node_mask[start_node:end_node] = True
            
            try:
                explanation = explainer(
                    model=model,
                    x=batch.x,
                    edge_index=batch.edge_index,
                    edge_attr=batch.edge_attr if hasattr(batch, 'edge_attr') else None,
                    target=out[graph_idx], # Explain prediction for first graph
                    index=graph_idx, # Graph index
                    explanation_type='phenomenon' # Explain the prediction itself
                )
                
                # Extract scores
                node_importance = explanation.node_mask.detach().cpu().numpy()
                edge_importance = explanation.edge_mask.detach().cpu().numpy() if hasattr(explanation, 'edge_mask') else None
                
                return {
                    'graph_idx': graph_idx,
                    'node_importance': node_importance.tolist(),
                    'edge_importance': edge_importance.tolist() if edge_importance is not None else None,
                    'prediction': out[graph_idx].item()
                }
            except Exception as e:
                logger.warning(f"Failed to explain graph {graph_idx}: {e}")
                return {
                    'graph_idx': graph_idx,
                    'node_importance': [0.0] * (end_node - start_node),
                    'edge_importance': None,
                    'prediction': out[graph_idx].item(),
                    'error': str(e)
                }
        else:
            logger.warning("Batch contains no graphs")
            return {}

def run_attribution_analysis(
    config: Dict[str, Any],
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Main function to run attribution analysis on the dataset.
    
    Args:
        config: Configuration dictionary
        logger: Logger instance
        
    Returns:
        Dictionary containing attribution results
    """
    logger.info("Starting attribution analysis...")
    
    # Load data
    graphs_path = config['paths']['graphs_final']
    splits_path = config['paths']['splits_dir']
    
    logger.info(f"Loading graphs from {graphs_path}")
    graphs = load_intermediate_graphs(graphs_path)
    logger.info(f"Loaded {len(graphs)} graphs")
    
    if len(graphs) == 0:
        logger.error("No graphs found. Cannot proceed with attribution.")
        return {'error': 'No graphs found'}
    
    # Load splits to select a subset for analysis (e.g., test set)
    logger.info(f"Loading splits from {splits_path}")
    try:
        split_indices = load_split_indices(splits_path)
        test_indices = split_indices.get('test', [])
    except Exception as e:
        logger.warning(f"Could not load splits: {e}. Using all graphs.")
        test_indices = list(range(len(graphs)))
    
    # Select subset for analysis (limit to first 50 to save time)
    subset_size = min(50, len(test_indices))
    subset_indices = test_indices[:subset_size]
    subset_graphs = [graphs[i] for i in subset_indices]
    
    logger.info(f"Analyzing {subset_size} graphs from the test set")
    
    # Create batch
    batch = Batch.from_data_list(subset_graphs)
    
    # Initialize model
    model_type = 'spectral_gnn' # Focus on Spectral GNN for attribution
    weights_path = config['paths']['weights_spectral_gnn']
    input_dim = config['model']['input_dim']
    hidden_dim = config['model']['hidden_dim']
    output_dim = config['model']['output_dim']
    
    logger.info(f"Loading {model_type} model from {weights_path}")
    model = load_model_weights(model_type, weights_path, input_dim, hidden_dim, output_dim)
    
    # Initialize Explainer
    logger.info("Initializing GNNExplainer...")
    explainer = GNNExplainer(
        model=model,
        epochs=50,
        lr=0.01,
        coeff={
            'node_feat': 1.0,
            'edge': 1.0
        }
    )
    
    # Compute attributions
    attribution_results = []
    start_time = time.time()
    
    for i, graph in enumerate(subset_graphs):
        logger.info(f"Processing graph {i+1}/{subset_size}")
        single_batch = Batch.from_data_list([graph])
        
        result = compute_attribution_for_batch(
            model=model,
            batch=single_batch,
            explainer=explainer,
            graph_idx=0
        )
        
        if result:
            result['original_index'] = subset_indices[i]
            attribution_results.append(result)
    
    elapsed_time = time.time() - start_time
    logger.info(f"Attribution analysis completed in {elapsed_time:.2f} seconds")
    
    return {
        'total_graphs_analyzed': len(attribution_results),
        'subset_indices': subset_indices,
        'elapsed_time': elapsed_time,
        'results': attribution_results
    }

def main():
    """Main entry point for the attribution script."""
    logger = setup_script_logging()
    
    try:
        # Load configuration
        config = get_config()
        ensure_directories(config)
        
        # Ensure output directory exists
        output_dir = config['paths']['artifacts']
        os.makedirs(output_dir, exist_ok=True)
        
        # Run analysis
        results = run_attribution_analysis(config, logger)
        
        # Save results
        output_path = os.path.join(output_dir, 'attribution_scores.json')
        logger.info(f"Saving attribution scores to {output_path}")
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Attribution analysis complete. Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Attribution analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
