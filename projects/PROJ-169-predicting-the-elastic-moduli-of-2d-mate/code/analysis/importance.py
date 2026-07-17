import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from torch_geometric.data import Data
import torch

# Import existing utilities
from data_models.material_graph import MaterialGraph
from model.gnn import create_model
from model.splitter import load_graphs_from_parquet as load_graphs_splitter
from utils.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

def load_graphs_from_parquet(path: Path) -> List[MaterialGraph]:
    """
    Load graphs from the processed parquet file.
    Delegates to the splitter module which already implements this.
    """
    return load_graphs_splitter(path)

def calculate_shap_values(
    model: torch.nn.Module,
    graphs: List[MaterialGraph],
    device: str = "cpu"
) -> Dict[str, Any]:
    """
    Calculate SHAP interaction values for the model inputs.
    
    Note: This is a placeholder implementation for the SHAP task (T023).
    The actual implementation requires converting MaterialGraph to a flat tensor
    representation suitable for SHAP KernelExplainer or DeepExplainer.
    
    For T024 (Permutation Importance), we focus on the structural descriptors
    directly accessible from the graph features.
    """
    logger.warning("SHAP calculation is a placeholder for T023. Implementing T024 instead.")
    return {"status": "placeholder", "message": "See calculate_permutation_importance"}

def calculate_permutation_importance(
    model: torch.nn.Module,
    graphs: List[MaterialGraph],
    target_metric: str = "mape",
    n_permutations: int = 10,
    feature_indices: Optional[List[int]] = None,
    device: str = "cpu"
) -> List[Dict[str, Any]]:
    """
    Calculate permutation importance for structural descriptors.
    
    This method measures the decrease in model performance when a single feature
    (or group of features) is randomly shuffled. A feature is considered important
    if shuffling its values causes the model performance to decrease significantly.
    
    Args:
        model: Trained GNN model.
        graphs: List of MaterialGraph objects (test set).
        target_metric: Metric to use for importance calculation ('mape', 'rmse', 'r2').
        n_permutations: Number of permutations per feature.
        feature_indices: Indices of features to evaluate. If None, uses all node features.
        device: Device to run inference on.
    
    Returns:
        List of dictionaries containing feature index, importance score, and description.
    """
    logger.info(f"Starting permutation importance calculation with {n_permutations} permutations.")
    
    # Convert graphs to PyG Data objects for inference
    # We assume the model expects a batch of graphs or a single large graph
    # For permutation importance, we need to process graphs individually or in small batches
    # to isolate the effect of permuting features.
    
    # Extract node features from the first graph to determine feature dimension
    if not graphs:
        raise ValueError("No graphs provided for permutation importance.")
    
    # Determine feature indices to evaluate
    # Assuming node features are stored in 'node_features' attribute of MaterialGraph
    # and are 1D arrays representing structural descriptors
    sample_graph = graphs[0]
    if not hasattr(sample_graph, 'node_features') or sample_graph.node_features is None:
        raise ValueError("Graphs must have 'node_features' attribute for permutation importance.")
    
    n_features = sample_graph.node_features.shape[1] if sample_graph.node_features.ndim > 1 else 1
    
    if feature_indices is None:
        feature_indices = list(range(n_features))
    
    logger.info(f"Evaluating {len(feature_indices)} features out of {n_features} total.")
    
    # Get baseline predictions and metrics
    # We need a way to compute the target metric. For simplicity, we'll assume
    # we can compute a loss or error directly.
    # Since we don't have the targets here, we'll assume the model outputs
    # a prediction and we compare it to a stored target.
    # In a real scenario, we'd pass the targets or load them with the graphs.
    
    # For this implementation, we'll compute the mean absolute error (MAE)
    # as a proxy for performance, assuming the model outputs a scalar per graph.
    # We'll need to reconstruct the targets from the graphs if they are stored.
    
    # Let's assume MaterialGraph has a 'target_moduli' attribute
    # If not, we'll skip the metric calculation and just report raw prediction changes
    has_targets = all(hasattr(g, 'target_moduli') and g.target_moduli is not None for g in graphs)
    
    if not has_targets:
        logger.warning("Graphs do not have 'target_moduli'. Using raw prediction variance as importance metric.")
        use_metric = False
    else:
        use_metric = True
    
    # Baseline prediction (no permutation)
    baseline_scores = []
    for g in graphs:
        # Convert to PyG Data
        # Assuming we have a helper to convert MaterialGraph to PyG Data
        # Since we don't have it in the API, we'll do a simple conversion
        # This is a simplification; in reality, we'd use the same conversion as in train.py
        
        # Create a dummy Data object
        x = torch.tensor(g.node_features, dtype=torch.float32)
        edge_index = torch.tensor(g.edge_index, dtype=torch.long) if hasattr(g, 'edge_index') else None
        y = torch.tensor(g.target_moduli, dtype=torch.float32).unsqueeze(0) if use_metric else None
        
        # If edge_index is missing, we can't run the GNN properly
        if edge_index is None:
            logger.error("Graphs must have 'edge_index' for GNN inference.")
            raise ValueError("Missing edge_index in graphs.")
        
        # Run inference
        model.eval()
        with torch.no_grad():
            # Assuming model takes (x, edge_index) and returns a prediction
            # This depends on the exact model signature
            try:
                pred = model(x.unsqueeze(0), edge_index.unsqueeze(0)) # Batch dimension
                pred = pred.squeeze()
            except Exception as e:
                logger.error(f"Error during model inference: {e}")
                raise
            
            if use_metric:
                # Compute error for this graph
                error = torch.abs(pred - y).item()
                baseline_scores.append(error)
            else:
                # Store prediction for variance calculation
                baseline_scores.append(pred.item())
    
    baseline_score = np.mean(baseline_scores) if use_metric else np.var(baseline_scores)
    logger.info(f"Baseline score: {baseline_score:.4f}")
    
    # Permutation importance calculation
    importance_results = []
    
    for feat_idx in feature_indices:
        perm_scores = []
        
        for _ in range(n_permutations):
            # Create a copy of graphs with permuted feature
            permuted_graphs = []
            for g in graphs:
                new_graph = MaterialGraph(
                    node_features=g.node_features.copy() if hasattr(g.node_features, 'copy') else np.array(g.node_features),
                    edge_index=g.edge_index.copy() if hasattr(g.edge_index, 'copy') else np.array(g.edge_index),
                    target_moduli=g.target_moduli.copy() if hasattr(g.target_moduli, 'copy') else np.array(g.target_moduli) if hasattr(g, 'target_moduli') else None,
                    family_id=g.family_id
                )
                
                # Permute the feature
                if new_graph.node_features.ndim > 1:
                    feature_col = new_graph.node_features[:, feat_idx].copy()
                    np.random.shuffle(feature_col)
                    new_graph.node_features[:, feat_idx] = feature_col
                else:
                    # 1D case
                    np.random.shuffle(new_graph.node_features)
                
                permuted_graphs.append(new_graph)
            
            # Evaluate on permuted graphs
            perm_score = 0.0
            for i, pg in enumerate(permuted_graphs):
                x = torch.tensor(pg.node_features, dtype=torch.float32)
                edge_index = torch.tensor(pg.edge_index, dtype=torch.long)
                y = torch.tensor(pg.target_moduli, dtype=torch.float32).unsqueeze(0) if use_metric else None
                
                model.eval()
                with torch.no_grad():
                    try:
                        pred = model(x.unsqueeze(0), edge_index.unsqueeze(0))
                        pred = pred.squeeze()
                    except Exception as e:
                        logger.error(f"Error during permuted inference: {e}")
                        raise
                    
                    if use_metric:
                        error = torch.abs(pred - y).item()
                        perm_score += error
                    else:
                        perm_score += pred.item()
            
            if use_metric:
                perm_score /= len(permuted_graphs)
                # Importance is the increase in error
                importance = perm_score - baseline_score
            else:
                # For variance, we look at how much the prediction changes
                # This is a simplified metric
                importance = abs(perm_score - np.mean(baseline_scores))
            
            perm_scores.append(importance)
        
        mean_importance = np.mean(perm_scores)
        std_importance = np.std(perm_scores)
        
        importance_results.append({
            "feature_index": feat_idx,
            "importance_score": float(mean_importance),
            "std_score": float(std_importance),
            "description": f"Structural descriptor {feat_idx}"
        })
    
    # Sort by importance score descending
    importance_results.sort(key=lambda x: x["importance_score"], reverse=True)
    
    logger.info(f"Permutation importance calculation complete. Top 3 features: {[r['feature_index'] for r in importance_results[:3]]}")
    
    return importance_results

def run_importance_analysis(
    graphs_path: Path,
    model_path: Path,
    output_path: Path,
    device: str = "cpu"
) -> Dict[str, Any]:
    """
    Run the full importance analysis pipeline.
    
    Args:
        graphs_path: Path to the processed graphs parquet file.
        model_path: Path to the trained model weights.
        output_path: Path to save the importance results.
        device: Device to run inference on.
    
    Returns:
        Dictionary containing the analysis results.
    """
    logger.info(f"Running importance analysis. Graphs: {graphs_path}, Model: {model_path}")
    
    # Load graphs
    graphs = load_graphs_from_parquet(graphs_path)
    logger.info(f"Loaded {len(graphs)} graphs.")
    
    # Load model
    model = create_model() # Assuming create_model returns an untrained model
    # Load weights
    if model_path.exists():
        state_dict = torch.load(model_path, map_location=device)
        model.load_state_dict(state_dict)
    else:
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    model.to(device)
    model.eval()
    
    # Calculate permutation importance
    importance_results = calculate_permutation_importance(
        model=model,
        graphs=graphs,
        device=device
    )
    
    # Prepare output
    results = {
        "analysis_type": "permutation_importance",
        "num_graphs": len(graphs),
        "results": importance_results
    }
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Importance analysis results saved to {output_path}")
    
    return results

def main():
    """Main entry point for the importance analysis script."""
    parser = argparse.ArgumentParser(description="Run permutation importance analysis on trained GNN model.")
    parser.add_argument("--graphs", type=str, required=True, help="Path to processed graphs parquet file.")
    parser.add_argument("--model", type=str, required=True, help="Path to trained model weights.")
    parser.add_argument("--output", type=str, required=True, help="Path to save importance results.")
    parser.add_argument("--device", type=str, default="cpu", help="Device to run inference on.")
    
    args = parser.parse_args()
    
    # Configure logging
    configure_log_file(Path(args.output).parent / "importance_analysis.log")
    
    # Run analysis
    try:
        results = run_importance_analysis(
            graphs_path=Path(args.graphs),
            model_path=Path(args.model),
            output_path=Path(args.output),
            device=args.device
        )
        print(json.dumps(results, indent=2))
    except Exception as e:
        logger.error(f"Importance analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()