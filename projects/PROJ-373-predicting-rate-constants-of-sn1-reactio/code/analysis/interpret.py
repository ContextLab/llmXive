import os
import sys
import json
import logging
import argparse
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors
import shap

# Local imports based on provided API surface
# We assume these are available in the project context
# If not, we implement minimal versions or import from relative paths
try:
    from models.mpnn import MPNN, MPNNConfig, create_mpnn_from_config
    from utils.logger import setup_logging, get_logger
except ImportError:
    # Fallback for standalone execution context if needed
    pass

def load_model_and_weights(model_path: str) -> Tuple[Any, MPNNConfig]:
    """
    Load the best model and its configuration.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    # Load config from a standard location or embedded in model
    # Assuming config is stored in artifacts/metrics.json or similar
    # For this implementation, we load the model and infer config if possible
    # or load from a sidecar file if T022 saved it.
    # Given T022 saves best_model.pt and metrics.json, we might need to reconstruct config
    # or rely on the model state dict structure.
    # For robustness, we assume a sidecar config or default reconstruction.
    config_path = os.path.join(os.path.dirname(model_path), "best_model_config.json")
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        config = MPNNConfig(**config_dict)
    else:
        # Fallback: try to infer or use defaults (not ideal but necessary if sidecar missing)
        # In a real scenario, T022 should ensure this exists.
        config = MPNNConfig() 
    
    model = MPNN(config)
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    model.eval()
    return model, config

def load_processed_data(data_path: str) -> pd.DataFrame:
    """
    Load the cleaned dataset.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    return pd.read_csv(data_path)

def prepare_graph_features(row: Dict[str, Any]) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Prepare graph features from a data row.
    Returns: (node_features, edge_index, edge_features)
    """
    smiles = row['smiles']
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    
    # Compute node features (e.g., atomic number, degree, etc.)
    # This is a simplified version; actual implementation depends on T013/T016 descriptors
    num_atoms = mol.GetNumAtoms()
    node_features = []
    for atom in mol.GetAtoms():
        # Example features: atomic number, degree, formal charge, etc.
        feat = [
            atom.GetAtomicNum(),
            atom.GetDegree(),
            atom.GetFormalCharge(),
            atom.GetIsAromatic()
        ]
        node_features.append(feat)
    
    node_features = torch.tensor(node_features, dtype=torch.float)
    
    # Edge index
    edge_list = []
    edge_features = []
    for bond in mol.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()
        edge_list.append([i, j])
        # Edge features: bond type, conjugation, etc.
        edge_feat = [bond.GetBondTypeAsDouble()]
        edge_features.append(edge_feat)
    
    if edge_list:
        edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()
        edge_features = torch.tensor(edge_features, dtype=torch.float)
    else:
        edge_index = torch.empty((2, 0), dtype=torch.long)
        edge_features = torch.empty((0, 1), dtype=torch.float)
    
    return node_features, edge_index, edge_features

def run_inference(model: Any, node_features: torch.Tensor, edge_index: torch.Tensor, edge_features: torch.Tensor) -> float:
    """
    Run inference on a single graph.
    """
    with torch.no_grad():
        # Ensure inputs are on CPU
        node_features = node_features.cpu()
        edge_index = edge_index.cpu()
        edge_features = edge_features.cpu()
        
        # Assuming model expects a batch of graphs or single graph
        # MPNN implementation details vary; this is a placeholder for the actual call
        # We assume the model can handle a single graph input
        # If the model expects a batch, we might need to unsqueeze
        try:
            output = model(node_features, edge_index, edge_features)
            return output.item()
        except Exception as e:
            logging.error(f"Inference failed: {e}")
            raise

def calculate_r2(predictions: List[float], targets: List[float]) -> float:
    """
    Calculate R² score.
    """
    if len(predictions) != len(targets):
        raise ValueError("Predictions and targets must have the same length")
    
    predictions = np.array(predictions)
    targets = np.array(targets)
    
    ss_res = np.sum((targets - predictions) ** 2)
    ss_tot = np.sum((targets - np.mean(targets)) ** 2)
    
    if ss_tot == 0:
        return 0.0
    return 1 - (ss_res / ss_tot)

def get_shap_rankings(model: Any, data_df: pd.DataFrame, node_features_list: List[torch.Tensor], edge_indices_list: List[torch.Tensor], edge_features_list: List[torch.Tensor]) -> np.ndarray:
    """
    Compute SHAP values and return node-level rankings.
    This is a simplified implementation; actual SHAP for GNNs can be complex.
    We use a permutation-based approach or a simplified SHAP explainer.
    """
    # Prepare data for SHAP
    # For node-level SHAP, we need to aggregate over the graph
    # This is a placeholder for the actual SHAP computation
    # In practice, we might use a library like captum or a custom implementation
    
    # For this task, we assume we have node-level SHAP values from a previous step (T026)
    # If not, we compute them here using a simplified method
    # We'll use a simple perturbation-based method to estimate node importance
    
    shap_values_list = []
    for i, (node_feat, edge_idx, edge_feat) in enumerate(zip(node_features_list, edge_indices_list, edge_features_list)):
        # Create an explainer
        # This is a placeholder; actual implementation depends on the model architecture
        # We'll use a simple method: perturb each node and measure output change
        base_output = run_inference(model, node_feat, edge_idx, edge_feat)
        node_shap = np.zeros(node_feat.shape[0])
        
        for node_idx in range(node_feat.shape[0]):
            # Perturb this node
            perturbed_feat = node_feat.clone()
            perturbed_feat[node_idx] = 0  # Zero out the node features
            
            try:
                perturbed_output = run_inference(model, perturbed_feat, edge_idx, edge_feat)
                node_shap[node_idx] = abs(perturbed_output - base_output)
            except:
                node_shap[node_idx] = 0.0
        
        shap_values_list.append(node_shap)
    
    return np.array(shap_values_list)

def perform_perturbation_study(model: Any, data_df: pd.DataFrame, node_features_list: List[torch.Tensor], edge_indices_list: List[torch.Tensor], edge_features_list: List[torch.Tensor], shap_values: np.ndarray) -> List[Dict[str, Any]]:
    """
    Perform perturbation study by masking top SHAP-ranked atoms.
    """
    results = []
    
    # Baseline predictions
    baseline_preds = []
    for i, (node_feat, edge_idx, edge_feat) in enumerate(zip(node_features_list, edge_indices_list, edge_features_list)):
        try:
            pred = run_inference(model, node_feat, edge_idx, edge_feat)
            baseline_preds.append(pred)
        except:
            baseline_preds.append(np.nan)
    
    baseline_targets = data_df['rate_constant'].values.tolist()
    
    # Perturbed predictions
    perturbed_preds = []
    for i, (node_feat, edge_idx, edge_feat, shap_vals) in enumerate(zip(node_features_list, edge_indices_list, edge_features_list, shap_values)):
        # Identify top 5 atoms by absolute SHAP value
        top_k = 5
        if len(shap_vals) < top_k:
            top_k = len(shap_vals)
        
        top_indices = np.argsort(np.abs(shap_vals))[-top_k:]
        
        # Create mask: set features of top atoms to zero
        perturbed_feat = node_feat.clone()
        for idx in top_indices:
            perturbed_feat[idx] = 0.0
        
        try:
            pred = run_inference(model, perturbed_feat, edge_idx, edge_feat)
            perturbed_preds.append(pred)
        except:
            perturbed_preds.append(np.nan)
    
    # Calculate R² for baseline and perturbed
    baseline_r2 = calculate_r2(baseline_preds, baseline_targets)
    perturbed_r2 = calculate_r2(perturbed_preds, baseline_targets)
    
    # Drop in R²
    r2_drop = baseline_r2 - perturbed_r2
    
    # Store results
    results.append({
        'baseline_r2': baseline_r2,
        'perturbed_r2': perturbed_r2,
        'r2_drop': r2_drop,
        'num_perturbed_atoms': top_k
    })
    
    return results

def run_interpretability_analysis(model_path: str, data_path: str, output_path: str):
    """
    Main function to run interpretability analysis including perturbation study.
    """
    # Load model
    model, config = load_model_and_weights(model_path)
    
    # Load data
    data_df = load_processed_data(data_path)
    
    # Prepare graph features
    node_features_list = []
    edge_indices_list = []
    edge_features_list = []
    
    for _, row in data_df.iterrows():
        try:
            node_feat, edge_idx, edge_feat = prepare_graph_features(row)
            node_features_list.append(node_feat)
            edge_indices_list.append(edge_idx)
            edge_features_list.append(edge_feat)
        except Exception as e:
            logging.warning(f"Skipping row due to error: {e}")
            continue
    
    # Get SHAP rankings (node-level)
    shap_values = get_shap_rankings(model, data_df, node_features_list, edge_indices_list, edge_features_list)
    
    # Perform perturbation study
    perturbation_results = perform_perturbation_study(model, data_df, node_features_list, edge_indices_list, edge_features_list, shap_values)
    
    # Save results to CSV
    output_file = os.path.join(output_path, "perturbation_results.csv")
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=perturbation_results[0].keys())
        writer.writeheader()
        writer.writerows(perturbation_results)
    
    logging.info(f"Perturbation results saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Run interpretability analysis and perturbation study")
    parser.add_argument("--model", type=str, required=True, help="Path to the best model weights (best_model.pt)")
    parser.add_argument("--data", type=str, required=True, help="Path to the cleaned dataset CSV")
    parser.add_argument("--output", type=str, required=True, help="Output directory for results")
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Ensure output directory exists
    os.makedirs(args.output, exist_ok=True)
    
    # Run analysis
    run_interpretability_analysis(args.model, args.data, args.output)

if __name__ == "__main__":
    main()