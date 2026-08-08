import os
import sys
import json
import logging
import argparse
from pathlib import Path
import numpy as np
import torch
from typing import Dict, List, Any, Optional, Tuple

# Import from utils for logging and device
from utils import get_device, setup_logging, get_logger
from model import MPNN, RidgeBaseline, prepare_gnn_data
from utils import parse_smiles, smiles_to_ecfp

# Configure logging
logger = get_logger(__name__)

def load_redundancy_masks(masks_path: str) -> Dict[str, List[int]]:
    """Load redundancy masks from JSON file.
    
    Args:
        masks_path: Path to redundancy_masks.json
        
    Returns:
        Dictionary mapping molecule_id to mask array (list of 0s and 1s)
    """
    if not os.path.exists(masks_path):
        raise FileNotFoundError(f"Redundancy masks file not found: {masks_path}")
    
    with open(masks_path, 'r') as f:
        masks = json.load(f)
    
    logger.info(f"Loaded {len(masks)} redundancy masks from {masks_path}")
    return masks

def compute_gradient_attribution(
    model: torch.nn.Module,
    smiles: str,
    target_lambda: float,
    device: torch.device
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute gradient-based attribution for a molecule.
    
    Args:
        model: Trained GNN model
        smiles: SMILES string of the molecule
        target_lambda: Experimental lambda_max value
        device: Device to run computation on
        
    Returns:
        Tuple of (node_attribution, edge_attribution) as numpy arrays
    """
    mol = parse_smiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    
    # Create graph data
    data = prepare_gnn_data(mol)
    data = data.to(device)
    
    model.eval()
    model.zero_grad()
    
    # Ensure node features require gradients
    if data.x.requires_grad:
        data.x.retain_grad()
    else:
        data.x.requires_grad = True
    
    # Forward pass
    output = model(data)
    
    # Compute gradient with respect to target
    loss = torch.abs(output - target_lambda)
    loss.backward()
    
    # Extract attributions
    node_attr = data.x.grad.abs().cpu().detach().numpy() if data.x.grad is not None else np.zeros(data.x.shape)
    
    # For edge attribution, we can use the edge weights if available
    # Otherwise, default to uniform or zero
    edge_attr = np.zeros(data.edge_index.shape[1]) if hasattr(data, 'edge_index') else np.array([])
    
    return node_attr, edge_attr

def get_substructure_from_mask(
    smiles: str,
    mask: np.ndarray,
    node_attr: np.ndarray
) -> List[int]:
    """Identify contributing substructures based on attribution and mask.
    
    Args:
        smiles: SMILES string
        mask: Redundancy mask (0 for redundant, 1 for important)
        node_attr: Node attribution weights
        
    Returns:
        List of atom indices that are both important and not redundant
    """
    mol = parse_smiles(smiles)
    if mol is None:
        return []
    
    # Apply mask to attribution weights
    masked_attr = node_attr * mask.reshape(-1, 1) if mask.ndim == 1 else node_attr * mask
    
    # Sum across features to get per-atom importance
    atom_importance = np.sum(masked_attr, axis=1)
    
    # Get indices of atoms with non-zero importance
    contributing_atoms = np.where(atom_importance > 1e-6)[0].tolist()
    
    return contributing_atoms

def apply_redundancy_mask(
    node_attr: np.ndarray,
    mask: np.ndarray
) -> np.ndarray:
    """Apply redundancy mask to node attribution weights.
    
    Args:
        node_attr: Original node attribution weights (n_atoms x n_features)
        mask: Redundancy mask (n_atoms,) - 0 for redundant, 1 for important
        
    Returns:
        Masked attribution weights where redundant atoms are zeroed out
    """
    if node_attr.shape[0] != len(mask):
        raise ValueError(
            f"Mask length ({len(mask)}) does not match number of atoms ({node_attr.shape[0]})"
        )
    
    # Convert mask to array if it's a list
    mask_array = np.array(mask)
    
    # Reshape mask to broadcast correctly
    if mask_array.ndim == 1:
        mask_array = mask_array.reshape(-1, 1)
    
    # Apply mask: zero out redundant atoms
    masked_attr = node_attr * mask_array
    
    # Verify masking occurred
    original_sum = np.sum(np.abs(node_attr))
    masked_sum = np.sum(np.abs(masked_attr))
    
    if original_sum > 0 and masked_sum == original_sum:
        logger.warning("Masking may not have affected any values - check mask values")
    elif masked_sum < original_sum:
        logger.info(f"Masking reduced attribution sum from {original_sum:.4f} to {masked_sum:.4f}")
    
    return masked_attr

def explain_molecule(
    smiles: str,
    model: torch.nn.Module,
    target_lambda: float,
    mask: Optional[np.ndarray],
    device: torch.device
) -> Dict[str, Any]:
    """Explain a single molecule's prediction with optional masking.
    
    Args:
        smiles: SMILES string
        model: Trained model
        target_lambda: Experimental lambda_max
        mask: Optional redundancy mask
        device: Device for computation
        
    Returns:
        Dictionary containing attribution results
    """
    # Compute raw attribution
    node_attr, edge_attr = compute_gradient_attribution(model, smiles, target_lambda, device)
    
    # Store unmasked results
    result = {
        "smiles": smiles,
        "target_lambda": float(target_lambda),
        "unmasked_node_attr": node_attr.tolist(),
        "unmasked_edge_attr": edge_attr.tolist(),
        "masked_node_attr": None,
        "masked_edge_attr": None,
        "mask_applied": False,
        "contributing_atoms": []
    }
    
    # Apply mask if provided
    if mask is not None and len(mask) > 0:
        masked_node_attr = apply_redundancy_mask(node_attr, mask)
        
        result["masked_node_attr"] = masked_node_attr.tolist()
        result["masked_edge_attr"] = edge_attr  # Edge attr unchanged
        result["mask_applied"] = True
        
        # Identify contributing substructures
        contributing_atoms = get_substructure_from_mask(smiles, mask, masked_node_attr)
        result["contributing_atoms"] = contributing_atoms
        
        logger.info(f"Applied mask to {smiles[:20]}...: {len(contributing_atoms)} contributing atoms")
    else:
        logger.info(f"No mask applied for {smiles[:20]}...")
    
    return result

def main():
    """Main function to run attribution analysis on test set with masking."""
    parser = argparse.ArgumentParser(description="Apply and verify masking for attribution analysis")
    parser.add_argument("--model_path", type=str, required=True, help="Path to trained model.pt")
    parser.add_argument("--test_data", type=str, required=True, help="Path to test data CSV")
    parser.add_argument("--masks_path", type=str, required=True, help="Path to redundancy masks JSON")
    parser.add_argument("--output_path", type=str, default="data/processed/attribution_results.json", 
                      help="Path to output attribution results")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    # Setup
    setup_logging()
    device = get_device()
    logger.info(f"Using device: {device}")
    
    # Load redundancy masks
    logger.info(f"Loading redundancy masks from {args.masks_path}")
    masks = load_redundancy_masks(args.masks_path)
    
    # Load model
    logger.info(f"Loading model from {args.model_path}")
    model = MPNN()
    model.load_state_dict(torch.load(args.model_path, map_location=device))
    model.to(device)
    model.eval()
    
    # Load test data
    logger.info(f"Loading test data from {args.test_data}")
    if not os.path.exists(args.test_data):
        raise FileNotFoundError(f"Test data not found: {args.test_data}")
    
    # Simple CSV loading (assuming columns: smi, lambda_max_exp)
    import pandas as pd
    df = pd.read_csv(args.test_data)
    
    if 'smi' not in df.columns or 'lambda_max_exp' not in df.columns:
        raise ValueError("Test data must contain 'smi' and 'lambda_max_exp' columns")
    
    logger.info(f"Loaded {len(df)} test molecules")
    
    # Process each molecule
    results = []
    for idx, row in df.iterrows():
        smiles = row['smi']
        target_lambda = row['lambda_max_exp']
        
        # Get mask for this molecule (use index or smiles as key)
        mask = None
        if str(idx) in masks:
            mask = np.array(masks[str(idx)])
        elif smiles in masks:
            mask = np.array(masks[smiles])
        
        try:
            result = explain_molecule(smiles, model, target_lambda, mask, device)
            results.append(result)
            
            # Verify masking
            if result["mask_applied"] and result["masked_node_attr"] is not None:
                unmasked = np.array(result["unmasked_node_attr"])
                masked = np.array(result["masked_node_attr"])
                
                # Check that masked values are zero where mask was 0
                if mask is not None:
                    mask_array = np.array(mask)
                    zero_mask = mask_array == 0
                    if np.any(zero_mask):
                        masked_zeros = masked[zero_mask]
                        if not np.allclose(masked_zeros, 0, atol=1e-6):
                            logger.warning(f"Masking verification failed for {smiles[:20]}...")
                            logger.warning(f"Non-zero values found in masked region: {np.max(np.abs(masked_zeros))}")
        except Exception as e:
            logger.error(f"Error processing {smiles}: {e}")
            continue
    
    # Save results
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved attribution results to {output_path}")
    
    # Summary
    masked_count = sum(1 for r in results if r["mask_applied"])
    logger.info(f"Processed {len(results)} molecules, {masked_count} with masking applied")

if __name__ == "__main__":
    main()
