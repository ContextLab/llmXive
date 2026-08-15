"""
Feature Importance Extraction Module

Implements SHAP-based feature importance extraction from the trained GNN model.
This module loads the trained model and input data, computes SHAP values to
determine the contribution of each topological feature to the Static Scattering
Potential prediction, and saves the results to the designated output directory.
"""

import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

from config import get_config, get_paths
from model.gnn import StaticScatteringPotentialGNN

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_trained_model(model_path: Path) -> StaticScatteringPotentialGNN:
    """
    Load the trained GNN model from disk.

    Args:
        model_path: Path to the saved model pickle file.

    Returns:
        The loaded StaticScatteringPotentialGNN model instance.

    Raises:
        FileNotFoundError: If the model file does not exist.
        pickle.UnpicklingError: If the file is corrupted or not a valid pickle.
    """
    if not model_path.exists():
        raise FileNotFoundError(f"Trained model not found at {model_path}")

    logger.info(f"Loading trained model from {model_path}")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    model.eval()
    logger.info("Model loaded successfully and set to evaluation mode")
    return model

def extract_node_features(graph_data: Dict[str, Any]) -> np.ndarray:
    """
    Extract node feature matrix from a graph dictionary.

    The graph dictionary is expected to contain a 'node_features' key with
    a numpy array of shape (num_nodes, num_features).

    Args:
        graph_data: Dictionary containing graph data including node features.

    Returns:
        numpy array of shape (num_nodes, num_features).

    Raises:
        KeyError: If required keys are missing from the graph data.
    """
    if 'node_features' not in graph_data:
        raise KeyError("Graph data missing 'node_features' key")
    
    features = np.array(graph_data['node_features'])
    logger.debug(f"Extracted features with shape {features.shape}")
    return features

def compute_shap_values(
    model: StaticScatteringPotentialGNN,
    feature_matrix: np.ndarray,
    sample_size: int = 100
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute SHAP (SHapley Additive exPlanations) values for feature importance.

    Since the model is a PyTorch-based GNN and we are working with CPU-only
    constraints, we use a simplified approximation method that computes
    feature importance by perturbing input features and measuring output changes.
    This mimics SHAP behavior without requiring the full SHAP library which
    may have heavy dependencies.

    Args:
        model: The trained GNN model.
        feature_matrix: Input feature matrix of shape (num_samples, num_features).
        sample_size: Number of perturbation samples to use for approximation.

    Returns:
        Tuple of (mean_shap_values, shap_std) where:
            - mean_shap_values: Average SHAP value per feature
            - shap_std: Standard deviation of SHAP values per feature
    """
    logger.info(f"Computing feature importance using perturbation-based SHAP approximation")
    logger.info(f"Input feature matrix shape: {feature_matrix.shape}")
    logger.info(f"Using {sample_size} perturbation samples")

    if feature_matrix.ndim == 1:
        # Single sample case
        feature_matrix = feature_matrix.reshape(1, -1)

    num_samples, num_features = feature_matrix.shape
    shap_values = np.zeros((num_samples, num_features))

    # Compute baseline (expected) output
    with torch.no_grad():
        baseline_output = model(torch.tensor(feature_matrix, dtype=torch.float32))
        if isinstance(baseline_output, tuple):
            baseline_output = baseline_output[0]
        baseline_output = baseline_output.numpy() if hasattr(baseline_output, 'numpy') else np.array(baseline_output)
    
    baseline_mean = np.mean(baseline_output)

    # Perturbation-based SHAP approximation
    for i in range(num_samples):
        base_features = feature_matrix[i:i+1]
        
        for j in range(num_features):
            # Create perturbed samples by masking one feature at a time
            perturbed_features = base_features.copy()
            
            # Randomly sample perturbations
            perturbation_indices = np.random.choice(
                num_samples, size=sample_size, replace=True
            )
            
            for k, idx in enumerate(perturbation_indices):
                perturbed_features[:, j] = feature_matrix[idx, j]
                
                with torch.no_grad():
                    output = model(torch.tensor(perturbed_features, dtype=torch.float32))
                    if isinstance(output, tuple):
                        output = output[0]
                    output_val = output.numpy() if hasattr(output, 'numpy') else np.array(output)
                
                shap_values[i, j] += (output_val[0, 0] - baseline_mean) / sample_size

    mean_shap = np.mean(shap_values, axis=0)
    shap_std = np.std(shap_values, axis=0)

    logger.info(f"Computed SHAP values. Mean range: [{mean_shap.min():.6f}, {mean_shap.max():.6f}]")
    logger.info(f"SHAP std range: [{shap_std.min():.6f}, {shap_std.max():.6f}]")

    return mean_shap, shap_std

def extract_feature_importance(
    model: StaticScatteringPotentialGNN,
    graphs: List[Dict[str, Any]],
    feature_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Extract feature importance for all graphs in the dataset.

    Args:
        model: The trained GNN model.
        graphs: List of graph dictionaries containing node features.
        feature_names: Optional list of feature names. If None, generic names are used.

    Returns:
        Dictionary containing feature importance results for each sample and
        aggregate statistics.
    """
    if not graphs:
        raise ValueError("No graphs provided for feature importance extraction")

    logger.info(f"Extracting feature importance for {len(graphs)} graphs")

    # Collect all feature matrices
    all_features = []
    valid_graph_indices = []
    
    for i, graph in enumerate(graphs):
        try:
            features = extract_node_features(graph)
            # Use mean of node features as sample representation
            sample_features = np.mean(features, axis=0)
            all_features.append(sample_features)
            valid_graph_indices.append(i)
        except KeyError as e:
            logger.warning(f"Skipping graph {i} due to missing features: {e}")
            continue

    if not all_features:
        raise ValueError("No valid graphs found with feature data")

    feature_matrix = np.array(all_features)
    logger.info(f"Processed feature matrix shape: {feature_matrix.shape}")

    # Compute SHAP values
    mean_shap, shap_std = compute_shap_values(model, feature_matrix)

    # Prepare results
    results = {
        'sample_importance': [],
        'aggregate': {
            'mean_shap': mean_shap.tolist(),
            'shap_std': shap_std.tolist(),
            'feature_names': feature_names or [f'feature_{i}' for i in range(len(mean_shap))],
            'num_samples': len(valid_graph_indices),
            'num_features': len(mean_shap)
        },
        'top_features': []
    }

    # Create per-sample importance results
    for i, graph_idx in enumerate(valid_graph_indices):
        sample_result = {
            'sample_id': graphs[graph_idx].get('id', f'graph_{graph_idx}'),
            'shap_values': mean_shap[i].tolist(),
            'shap_std': shap_std[i].tolist()
        }
        results['sample_importance'].append(sample_result)

    # Identify top features by absolute mean SHAP value
    top_indices = np.argsort(np.abs(mean_shap))[::-1][:10]
    for idx in top_indices:
        results['top_features'].append({
            'feature_index': int(idx),
            'feature_name': results['aggregate']['feature_names'][idx],
            'mean_shap': float(mean_shap[idx]),
            'shap_std': float(shap_std[idx]),
            'absolute_importance': float(np.abs(mean_shap[idx]))
        })

    logger.info(f"Feature importance extraction complete. Top 3 features: {[f['feature_name'] for f in results['top_features'][:3]]}")
    
    return results

def main():
    """
    Main entry point for feature importance extraction.
    
    This function:
    1. Loads configuration and paths
    2. Loads the trained GNN model
    3. Loads the graph data used for training
    4. Computes feature importance using SHAP approximation
    5. Saves results to the designated output file
    """
    logger.info("Starting feature importance extraction (T032)")
    
    try:
        # Load configuration
        config = get_config()
        paths = get_paths()
        
        # Define paths
        model_path = paths['model_output'] / 'trained_gnn_model.pkl'
        graphs_path = paths['processed_graphs'] / 'training_graphs.pkl'
        output_dir = paths['model_outputs']
        output_path = output_dir / 'feature_importance.json'
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load trained model
        model = load_trained_model(model_path)
        
        # Load graph data
        if not graphs_path.exists():
            raise FileNotFoundError(f"Training graphs not found at {graphs_path}")
        
        with open(graphs_path, 'rb') as f:
            graphs = pickle.load(f)
        
        logger.info(f"Loaded {len(graphs)} graphs for feature importance analysis")
        
        # Extract feature importance
        importance_results = extract_feature_importance(model, graphs)
        
        # Save results
        with open(output_path, 'w') as f:
            json.dump(importance_results, f, indent=2)
        
        logger.info(f"Feature importance results saved to {output_path}")
        
        # Log summary
        logger.info("=== Feature Importance Summary ===")
        logger.info(f"Number of samples analyzed: {importance_results['aggregate']['num_samples']}")
        logger.info(f"Number of features: {importance_results['aggregate']['num_features']}")
        logger.info("Top 5 features by importance:")
        for i, feat in enumerate(importance_results['top_features'][:5]):
            logger.info(f"  {i+1}. {feat['feature_name']}: {feat['mean_shap']:.6f} (±{feat['shap_std']:.6f})")
        
        logger.info("T032 task completed successfully")
        
    except Exception as e:
        logger.error(f"Feature importance extraction failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
