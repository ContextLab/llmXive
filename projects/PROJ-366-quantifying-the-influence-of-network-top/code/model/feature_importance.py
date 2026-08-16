"""
Feature Importance Extraction Module.

Implements SHAP-based feature importance extraction from a trained GNN model.
Outputs SHAP values to a NumPy array file as required by T032.
"""
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

# Import from project modules
from config import get_config, get_paths
from model.gnn import load_graphs_for_training, StaticScatteringPotentialGNN

logger = logging.getLogger(__name__)

def load_trained_model(model_path: Path) -> StaticScatteringPotentialGNN:
    """
    Load a trained GNN model from disk.

    Args:
        model_path: Path to the saved model checkpoint.

    Returns:
        The loaded model instance.
    """
    if not model_path.exists():
        raise FileNotFoundError(f"Model checkpoint not found at {model_path}")

    logger.info(f"Loading model from {model_path}")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    model.eval()
    return model

def extract_node_features(graph_data: Dict[str, Any]) -> np.ndarray:
    """
    Extract node features from a graph dictionary.
    
    The graph is expected to have a 'nodes' key containing a list of node objects.
    Each node object should have features (e.g., degree, clustering coefficient).

    Args:
        graph_data: Dictionary representing a graph.

    Returns:
        NumPy array of shape [N_nodes, N_features].
    """
    nodes = graph_data.get('nodes', [])
    if not nodes:
        return np.array([])
    
    # Assume node structure: {id, coords, degree, clustering_coeff, ...}
    # We extract 'degree' and 'clustering_coeff' as topological features.
    # If 'coords' are present, we could also use radial distribution features,
    # but for T032 we focus on topological metrics as per spec FR-005 context.
    
    features_list = []
    for node in nodes:
        # Extract degree and clustering coefficient
        degree = float(node.get('degree', 0))
        clustering = float(node.get('clustering_coeff', 0.0))
        # Normalize features if needed (assuming simple scaling for now)
        features_list.append([degree, clustering])
    
    return np.array(features_list, dtype=np.float32)

def compute_shap_values(
    model: StaticScatteringPotentialGNN,
    feature_matrix: np.ndarray,
    background_size: int = 50
) -> np.ndarray:
    """
    Compute SHAP values for the model predictions.
    
    Since SHAP is an external dependency and might not be installed in all
    environments, we implement a simplified permutation-based feature importance
    that mimics SHAP's behavior for this specific task, or use a fallback if
    shap is not available. However, the task explicitly asks for SHAP.
    
    We will attempt to import shap. If unavailable, we raise an error as
    per "Fail loudly" constraint.
    
    Args:
        model: Trained GNN model.
        feature_matrix: Matrix of input features [N_samples, N_features].
        background_size: Size of background dataset for SHAP.

    Returns:
        NumPy array of SHAP values [N_samples, N_features].
    """
    try:
        import shap
    except ImportError:
        logger.error("SHAP library not installed. Please install it: pip install shap")
        raise RuntimeError("SHAP library is required for T032 but not found.")

    logger.info(f"Computing SHAP values for {feature_matrix.shape[0]} samples...")
    
    # Create a simple wrapper for the model to work with SHAP
    # The model expects graph data, but SHAP expects a function f(x) -> y
    # We assume feature_matrix is [N_samples, N_features] where each row is a sample's aggregated features.
    # For node-level graphs, this is complex. We assume the trainer has already
    # aggregated node features to a graph-level representation for the final prediction.
    
    # If the model operates on node-level, we might need to average SHAP values.
    # For this implementation, we assume the input to this function is the
    # graph-level feature vector derived from the graph.
    
    # We create a mock background dataset
    if feature_matrix.shape[0] < background_size:
        background_size = feature_matrix.shape[0]
    
    background = shap.sample(feature_matrix, background_size)
    
    # Define the model function for SHAP
    # We assume the model has a method `predict` that takes a feature matrix
    # If the model expects a graph object, we need to adapt.
    # Based on T030, the model predicts "local heat flux".
    # For T033a (Pearson), we need a single value per sample (global conductivity).
    # We assume the trainer has aggregated these to a single prediction per sample.
    # Here we assume `model` can predict on a batch of feature vectors.
    
    def model_predict(x):
        # x is [batch, features]
        # We need to convert x back to the format the model expects if necessary.
        # Assuming the model was trained on graph-level features extracted similarly.
        # This is a simplification. In a real scenario, we'd need the exact graph structure.
        # For T032, we assume `model` can accept a numpy array of features.
        with torch.no_grad():
            # Convert to tensor
            x_tensor = torch.FloatTensor(x)
            # Forward pass
            output = model(x_tensor)
            # If output is a tensor, convert to numpy
            return output.detach().numpy()

    # Initialize SHAP explainer
    explainer = shap.PermutationExplainer(model_predict, background)
    
    # Compute SHAP values
    shap_values = explainer.shap_values(feature_matrix)
    
    # Ensure output is a numpy array
    if isinstance(shap_values, list):
        shap_values = np.array(shap_values)
        
    return np.array(shap_values, dtype=np.float32)

def extract_feature_importance(
    model_path: Path,
    graphs_path: Path,
    output_path: Path,
    sample_limit: Optional[int] = None
) -> Tuple[Path, Dict[str, Any]]:
    """
    Main function to extract feature importance and save results.

    Args:
        model_path: Path to the trained model.
        graphs_path: Path to the directory containing processed graphs.
        output_path: Path where SHAP values will be saved.
        sample_limit: Optional limit on the number of samples to process.

    Returns:
        Tuple of (output_path, metadata_dict).
    """
    logger.info(f"Starting feature importance extraction...")
    
    # Load model
    model = load_trained_model(model_path)
    
    # Load graphs
    graphs, metadata = load_graphs_for_training(graphs_path, limit=sample_limit)
    
    if not graphs:
        raise ValueError("No graphs found for feature importance extraction.")
    
    logger.info(f"Processing {len(graphs)} graphs...")
    
    # Extract features for each graph
    feature_matrix_list = []
    for graph in graphs:
        features = extract_node_features(graph)
        # Aggregate node features to graph level (e.g., mean)
        if features.size > 0:
            graph_features = np.mean(features, axis=0)
            feature_matrix_list.append(graph_features)
        else:
            # Handle empty graph case if necessary
            feature_matrix_list.append(np.zeros(2)) # Assuming 2 features: degree, clustering
    
    feature_matrix = np.array(feature_matrix_list, dtype=np.float32)
    logger.info(f"Feature matrix shape: {feature_matrix.shape}")
    
    # Compute SHAP values
    shap_values = compute_shap_values(model, feature_matrix)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save SHAP values
    logger.info(f"Saving SHAP values to {output_path}")
    np.save(output_path, shap_values)
    
    metadata_output = {
        "shape": list(shap_values.shape),
        "n_samples": len(graphs),
        "n_features": feature_matrix.shape[1],
        "model_path": str(model_path),
        "graphs_path": str(graphs_path)
    }
    
    return output_path, metadata_output

def main():
    """Entry point for the feature importance extraction script."""
    import sys
    import torch # Required for model loading if using torch
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    config = get_config()
    paths = get_paths(config)
    
    model_path = paths['model_output'] / 'trained_gnn.pkl'
    graphs_path = paths['graphs']
    output_file = paths['model_output'] / 'shap_values.npy'
    
    try:
        output_path, metadata = extract_feature_importance(
            model_path=model_path,
            graphs_path=graphs_path,
            output_path=output_file
        )
        logger.info(f"Feature importance extraction completed successfully.")
        logger.info(f"Output saved to: {output_path}")
        logger.info(f"Metadata: {metadata}")
        
        # Save metadata as JSON for verification
        metadata_path = output_file.with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
    except Exception as e:
        logger.error(f"Feature importance extraction failed: {e}")
        raise

if __name__ == "__main__":
    main()
