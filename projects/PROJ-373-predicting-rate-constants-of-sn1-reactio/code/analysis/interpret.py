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
from torch.utils.data import DataLoader, TensorDataset
import shap

# Project imports based on API surface
from config import ensure_dirs
from utils.logger import get_logger
from models.mpnn import MPNN, create_mpnn_from_config, MPNNConfig
from models.save_artifacts import load_best_training_result

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = get_logger(__name__)

def load_model_and_weights(config_path: str, weights_path: str) -> Tuple[MPNN, MPNNConfig]:
    """Load the MPNN model and its configuration."""
    with open(config_path, 'r') as f:
        config_dict = json.load(f)
    
    model_config = MPNNConfig(
        hidden_dim=config_dict.get('hidden_dim', 128),
        num_layers=config_dict.get('num_layers', 3),
        dropout=config_dict.get('dropout', 0.1),
        learning_rate=config_dict.get('learning_rate', 1e-3),
        edge_dim=config_dict.get('edge_dim', 16)
    )
    
    model = create_mpnn_from_config(model_config)
    model.load_state_dict(torch.load(weights_path, map_location='cpu'))
    model.eval()
    
    return model, model_config

def load_processed_data(data_path: str) -> pd.DataFrame:
    """Load the processed dataset."""
    return pd.read_csv(data_path)

def prepare_graph_features(df: pd.DataFrame) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Prepare graph features from the dataframe.
    Returns: node_features, edge_index, edge_features
    Note: This assumes the dataframe has pre-computed descriptors that can be
    reshaped into node features for the graph.
    """
    # Extract node features (Gasteiger charges and topological indices)
    # Assuming columns 'gasteiger_charges' and 'topological_indices' contain lists
    node_features_list = []
    
    for _, row in df.iterrows():
        # Combine charges and indices into a single feature vector per node
        # This is a simplification; in reality, we'd need the actual graph structure
        # For the perturbation study, we assume the features are already flattened
        # or we reconstruct them based on the molecule structure
        
        # Placeholder: assuming we have a 'node_features' column or reconstructing it
        if 'node_features' in df.columns:
            node_features_list.append(np.array(row['node_features']))
        else:
            # Fallback: combine charges and indices if available
            charges = np.array(row.get('gasteiger_charges', [0.0] * 10))
            indices = np.array(row.get('topological_indices', [0.0] * 5))
            combined = np.concatenate([charges, indices])
            node_features_list.append(combined)
    
    # Pad to max length if necessary (simplified approach)
    max_len = max(len(f) for f in node_features_list)
    padded_features = np.zeros((len(node_features_list), max_len))
    for i, f in enumerate(node_features_list):
        padded_features[i, :len(f)] = f
    
    node_features = torch.tensor(padded_features, dtype=torch.float32)
    
    # For edge_index and edge_features, we'd need actual graph structure
    # This is a placeholder implementation
    num_nodes = len(df)
    edge_index = torch.tensor([[i, i+1] for i in range(num_nodes-1)], dtype=torch.long).t()
    edge_features = torch.ones((edge_index.shape[1], 1), dtype=torch.float32)
    
    return node_features, edge_index, edge_features

def run_inference(model: MPNN, node_features: torch.Tensor, edge_index: torch.Tensor, 
                 edge_features: torch.Tensor, batch_size: int = 32) -> np.ndarray:
    """Run model inference and return predictions."""
    model.eval()
    predictions = []
    
    with torch.no_grad():
        for i in range(0, node_features.shape[0], batch_size):
            batch_nodes = node_features[i:i+batch_size]
            batch_edges = edge_index[:, i:i+batch_size] if i+batch_size < edge_index.shape[1] else edge_index
            batch_edge_feats = edge_features[i:i+batch_size] if i+batch_size < edge_features.shape[0] else edge_features
            
            # Simplified forward pass - actual implementation would depend on MPNN structure
            try:
                output = model(batch_nodes, batch_edges, batch_edge_feats)
                predictions.extend(output.cpu().numpy())
            except Exception as e:
                logger.warning(f"Error during inference: {e}")
                predictions.extend([0.0] * (batch_nodes.shape[0]))
    
    return np.array(predictions)

def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate R² score."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

def perform_perturbation_study(model: MPNN, df: pd.DataFrame, 
                              node_features: torch.Tensor, edge_index: torch.Tensor,
                              edge_features: torch.Tensor,
                              shap_values: np.ndarray,
                              top_k: int = 5) -> pd.DataFrame:
    """
    Perform perturbation study by zeroing out top SHAP-ranked features.
    
    Args:
        model: Trained MPNN model
        df: Original dataframe with true labels
        node_features: Original node features tensor
        edge_index: Edge index tensor
        edge_features: Edge features tensor
        shap_values: SHAP values array (n_samples, n_features)
        top_k: Number of top features to perturb
    
    Returns:
        DataFrame with perturbation results
    """
    # Get true labels
    y_true = df['rate_constant'].values
    
    # Calculate baseline R²
    baseline_preds = run_inference(model, node_features, edge_index, edge_features)
    baseline_r2 = calculate_r2(y_true, baseline_preds)
    
    results = []
    
    # Identify top features by mean absolute SHAP value
    feature_importance = np.mean(np.abs(shap_values), axis=0)
    top_feature_indices = np.argsort(feature_importance)[-top_k:][::-1]
    
    logger.info(f"Top {top_k} features for perturbation: {top_feature_indices}")
    
    for feat_idx in top_feature_indices:
        logger.info(f"Perturbing feature index {feat_idx}")
        
        # Create perturbed features by zeroing out the specific feature
        perturbed_features = node_features.clone()
        perturbed_features[:, feat_idx] = 0.0
        
        # Run inference on perturbed data
        perturbed_preds = run_inference(model, perturbed_features, edge_index, edge_features)
        
        # Calculate performance drop
        perturbed_r2 = calculate_r2(y_true, perturbed_preds)
        r2_drop = baseline_r2 - perturbed_r2
        
        results.append({
            'feature_index': int(feat_idx),
            'feature_importance': float(feature_importance[feat_idx]),
            'baseline_r2': float(baseline_r2),
            'perturbed_r2': float(perturbed_r2),
            'r2_drop': float(r2_drop)
        })
    
    return pd.DataFrame(results)

def run_interpretability_analysis(data_path: str, config_path: str, weights_path: str,
                                 shap_values_path: str, output_path: str,
                                 top_k: int = 5) -> None:
    """
    Run full interpretability analysis including perturbation study.
    
    Args:
        data_path: Path to processed dataset CSV
        config_path: Path to model config JSON
        weights_path: Path to model weights PT file
        shap_values_path: Path to saved SHAP values NPZ file
        output_path: Path to save perturbation results CSV
    """
    # Load data and model
    logger.info(f"Loading data from {data_path}")
    df = load_processed_data(data_path)
    
    logger.info(f"Loading model from {weights_path}")
    model, _ = load_model_and_weights(config_path, weights_path)
    
    # Prepare features
    logger.info("Preparing graph features")
    node_features, edge_index, edge_features = prepare_graph_features(df)
    
    # Load SHAP values
    logger.info(f"Loading SHAP values from {shap_values_path}")
    shap_data = np.load(shap_values_path)
    shap_values = shap_data['values'] if 'values' in shap_data else shap_data['arr_0']
    
    # Ensure SHAP values match data shape
    if shap_values.shape[0] != len(df):
        logger.warning(f"SHAP values shape {shap_values.shape[0]} doesn't match data {len(df)}, truncating")
        shap_values = shap_values[:len(df)]
    
    # Perform perturbation study
    logger.info("Running perturbation study")
    perturbation_results = perform_perturbation_study(
        model, df, node_features, edge_index, edge_features,
        shap_values, top_k=top_k
    )
    
    # Save results
    ensure_dirs([output_path])
    perturbation_results.to_csv(output_path, index=False)
    logger.info(f"Perturbation results saved to {output_path}")
    
    # Print summary
    logger.info("Perturbation Study Summary:")
    logger.info(perturbation_results.to_string(index=False))

def main():
    """Main entry point for perturbation study."""
    parser = argparse.ArgumentParser(description="Run perturbation study for model interpretability")
    parser.add_argument('--data', type=str, required=True, help='Path to processed dataset CSV')
    parser.add_argument('--config', type=str, required=True, help='Path to model config JSON')
    parser.add_argument('--weights', type=str, required=True, help='Path to model weights PT file')
    parser.add_argument('--shap', type=str, required=True, help='Path to SHAP values NPZ file')
    parser.add_argument('--output', type=str, required=True, help='Path to save perturbation results CSV')
    parser.add_argument('--top_k', type=int, default=5, help='Number of top features to perturb')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Run analysis
    run_interpretability_analysis(
        data_path=args.data,
        config_path=args.config,
        weights_path=args.weights,
        shap_values_path=args.shap,
        output_path=args.output,
        top_k=args.top_k
    )

if __name__ == '__main__':
    main()