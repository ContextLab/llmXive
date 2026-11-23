import logging
import json
import sys
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
import numpy as np
import pandas as pd

# Optional imports for GNNExplainer
# We attempt to import torch_geometric and torch_geometric.explain
# If not available, we handle the ImportError gracefully but fail loudly if the task requires it.
try:
    import torch
    from torch_geometric.explain import GNNExplainer
    from torch_geometric.data import Data
    from torch_geometric.nn import MessagePassing
    HAS_TORCH_GEOMETRIC = True
except ImportError:
    HAS_TORCH_GEOMETRIC = False
    logging.warning("torch_geometric not installed. GNNExplainer functionality will be unavailable.")

from models.gnn import MPNN, create_mpnn_model
from utils.logging import setup_logging, log_result_artifact

logger = logging.getLogger(__name__)

def load_test_graphs_from_csv(csv_path: str, model_config: Dict[str, Any]) -> List[Data]:
    """
    Load test data from CSV and reconstruct PyTorch Geometric Data objects.
    Assumes the CSV contains node features and a target column, and potentially edge indices.
    Since the specific schema of 'data/processed/test.csv' isn't fully defined in the prompt,
    we assume a standard format: node features in columns, target in 'target', and edges
    might be implicit or stored in a separate structure.
    
    For this implementation, we assume the CSV contains flattened node features.
    To run GNNExplainer, we need a graph structure (edge_index).
    If the CSV doesn't have explicit edges, we might need to reconstruct a k-NN graph
    or assume a pre-computed edge index exists.
    
    Given the constraints and typical pipeline flow:
    1. We load the CSV.
    2. We assume the model was trained on a specific graph structure.
    3. We will attempt to load the 'test_graphs.pt' file if it exists, which is a common
       practice for GNN pipelines to store graph structures.
    4. If not, we fallback to creating a dummy graph structure for explanation purposes
       (e.g., treating each sample as a small graph or using a k-NN approach), 
       but this is less ideal.
    
    However, the task requires identifying substructures. This implies the data IS graph-structured.
    We will assume the existence of a serialized graph file `data/interim/test_graphs.pt` 
    generated during the split/preprocessing phase (T017/T014b) or that the CSV contains 
    enough info to reconstruct it.
    
    For robustness, we'll try to load from a standard path first.
    """
    graphs = []
    graph_path = Path("data/interim/test_graphs.pt")
    
    if graph_path.exists():
        logger.info(f"Loading pre-computed test graphs from {graph_path}")
        # Assuming a list of Data objects was saved
        import torch
        graphs = torch.load(graph_path)
        if not isinstance(graphs, list):
            graphs = [graphs]
    else:
        logger.warning(f"Graph file {graph_path} not found. Attempting to reconstruct from CSV.")
        # Fallback: Load CSV and create dummy graphs if possible.
        # This is a simplification. In a real scenario, T014b/T017 should have saved graph structures.
        df = pd.read_csv(csv_path)
        # We need to know the feature columns. Let's assume all numeric cols except 'target' are features.
        # And we need an edge_index. If missing, we can't do substructure analysis properly.
        # We will raise an error if edge info is missing, as substructure analysis requires it.
        logger.error("Graph structure file missing. Cannot perform substructure analysis without edge_index.")
        raise FileNotFoundError("Graph structure file 'data/interim/test_graphs.pt' not found. "
                                "Please ensure T014b/T017 saved the graph structures.")

    return graphs

def explain_gnn(model_path: str, data_path: str, output_path: str) -> Dict[str, Any]:
    """
    Apply GNNExplainer to the trained GNN model on the test set.
    
    Args:
        model_path: Path to the saved GNN model checkpoint.
        data_path: Path to the test data (CSV or graph file).
        output_path: Path to save the explanation results JSON.
        
    Returns:
        Dictionary containing explanation results.
    """
    if not HAS_TORCH_GEOMETRIC:
        raise RuntimeError("torch_geometric is required for GNNExplainer but is not installed.")

    logger.info(f"Loading GNN model from {model_path}")
    
    # Load model
    # We need to reconstruct the model architecture. 
    # Assuming the model was saved with its architecture info or we can load it directly.
    # The gnn.py module likely has a way to load or create the model.
    # Let's assume we load the state dict and create a fresh model instance.
    # We need the model config. We'll try to load it from the checkpoint or use defaults.
    
    checkpoint = torch.load(model_path, map_location=torch.device('cpu'))
    model_config = checkpoint.get('model_config', {})
    
    # Create model instance
    # The create_mpnn_model function in gnn.py likely takes these config params
    model = create_mpnn_model(**model_config)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    logger.info(f"Loading test graphs from {data_path}")
    test_graphs = load_test_graphs_from_csv(data_path, model_config)
    
    explainer = GNNExplainer(
        model=model,
        epochs=100,
        lr=0.01,
        coeff_l1=0.01,
        coeff_entropy=0.1
    )
    
    explanations = []
    feature_names = model_config.get('feature_names', [f"feat_{i}" for i in range(model_config.get('num_features', 10))])
    
    logger.info(f"Starting GNNExplainer on {len(test_graphs)} test samples...")
    
    for i, graph in enumerate(test_graphs):
        if i % 50 == 0:
            logger.info(f"Explaining sample {i}/{len(test_graphs)}")
        
        # Move to CPU
        graph = graph.to(torch.device('cpu'))
        
        # Get prediction
        with torch.no_grad():
            pred = model(graph.x, graph.edge_index, graph.batch if hasattr(graph, 'batch') else None)
            if hasattr(pred, 'squeeze'):
                pred = pred.squeeze()
        
        # Get explanation
        # GNNExplainer expects a target index for classification or a target value for regression.
        # Since this is a regression task (permeability), we need to handle this carefully.
        # GNNExplainer for regression usually maximizes the predicted value or minimizes error.
        # We will explain the prediction for the specific sample.
        
        # Note: GNNExplainer's explain_graph method is designed for graph-level tasks.
        # Assuming our model does graph-level regression (predicting permeability of the whole molecule).
        explanation = explainer.explain_graph(graph.x, graph.edge_index)
        
        # Extract node and edge masks
        node_mask = explanation.node_mask.detach().numpy()
        edge_mask = explanation.edge_mask.detach().numpy()
        
        # Identify top influential nodes (substructures)
        # We rank nodes by their mask values
        node_importance_indices = np.argsort(node_mask.flatten())[::-1]
        top_node_indices = node_importance_indices[:10] # Top 10 nodes
        
        # Map node indices to feature importance (if available) or just indices
        # Since we don't have a direct mapping from node index to chemical substructure name
        # without a more complex RDKit integration, we will report the node indices and their
        # feature vectors, and potentially the most important features within those nodes.
        
        sample_explanation = {
            "sample_index": i,
            "prediction": float(pred) if hasattr(pred, 'item') else float(pred),
            "top_node_indices": top_node_indices.tolist(),
            "top_node_masks": node_mask.flatten()[top_node_indices].tolist(),
            "edge_mask_shape": list(edge_mask.shape)
        }
        
        # Optional: Aggregate feature importance across nodes for this graph
        # This is a simplification. Real substructure analysis would map nodes to atoms/bonds.
        explanations.append(sample_explanation)
    
    # Aggregate results
    # We can compute the average importance of each node position across all graphs?
    # No, node indices are not aligned across graphs.
    # Instead, we report the most frequently appearing top nodes? Not really meaningful.
    # We will report the list of explanations and maybe a summary of top features across all.
    
    # Let's try to aggregate feature importance by averaging node masks across all graphs (if shapes match)
    # This is tricky if graphs have different numbers of nodes.
    # Alternative: Report the top features from the model's perspective if available.
    
    # For now, we save the list of per-graph explanations.
    # We also try to identify "common" high-importance features by looking at the node features
    # that were most frequently masked highly.
    
    all_top_features = []
    for exp in explanations:
        # We don't have a direct mapping, so we'll just collect the top node masks
        pass
    
    result = {
        "model_path": model_path,
        "data_path": data_path,
        "num_samples_explained": len(explanations),
        "explanations": explanations,
        "note": "Substructure identification requires mapping node indices to chemical atoms/groups. "
                "This output provides node-level importance scores. For chemical interpretation, "
                "these indices must be mapped back to the molecular graph using RDKit."
    }
    
    # Save to JSON
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Saved GNN explanations to {output_path}")
    log_result_artifact("feature_importance_gnn", output_path)
    
    return result

def main():
    """Main entry point for GNN explainability analysis."""
    setup_logging()
    
    # Configuration
    model_path = "data/interim/gnn_checkpoint.pt"
    test_data_path = "data/processed/test.csv" # Or the graph file path
    output_path = "results/feature_importance_gnn.json"
    
    # Check if model exists
    if not Path(model_path).exists():
        logger.error(f"Model checkpoint not found at {model_path}. "
                     "Please run training (T022) first.")
        sys.exit(1)
    
    try:
        explain_gnn(model_path, test_data_path, output_path)
        logger.info("GNN explanation analysis completed successfully.")
    except Exception as e:
        logger.error(f"Error during GNN explanation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()