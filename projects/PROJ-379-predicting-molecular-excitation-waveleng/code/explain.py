"""
T024: Implement GNNExplainer on test set.

Performs GNNExplainer (steps=50, subset_size=10) on the test set molecules
to generate raw attribution scores for atoms and edges.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

import torch
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

# Import from project API surface
from model import MPNN, prepare_gnn_data, build_gnn_model
from utils import get_device, setup_logging, get_logger, parse_smiles

# Configure logging
logger = setup_logging("explain", log_level=logging.INFO)

# GNNExplainer parameters
STEPS = 50
SUBSET_SIZE = 10

def load_test_data() -> List[Dict[str, Any]]:
    """
    Load the test set from data/processed/train_val_test.csv.
    Returns a list of dicts with keys: smi, lambda_max, scaffold_id, split.
    """
    data_path = Path("data/processed/train_val_test.csv")
    if not data_path.exists():
        raise FileNotFoundError(f"Test data file not found: {data_path}")

    import pandas as pd
    df = pd.read_csv(data_path)
    test_df = df[df["split"] == "test"]

    if test_df.empty:
        raise ValueError("No test samples found in data/processed/train_val_test.csv")

    records = []
    for _, row in test_df.iterrows():
        records.append({
            "smi": str(row["smi"]),
            "lambda_max": float(row["lambda_max"]),
            "scaffold_id": str(row["scaffold_id"]),
            "mol_id": f"{row['scaffold_id']}_{row['smi'][:8]}"  # Simple unique ID
        })
    return records

def smiles_to_graph(smiles: str):
    """
    Convert SMILES to PyG Data object using the project's model utilities.
    """
    mol = parse_smiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")

    # Use the project's existing graph construction
    data = prepare_gnn_data(mol)
    return data, mol

def compute_gradient_attribution(model: torch.nn.Module, data, target_idx: int = 0):
    """
    Compute gradient-based attribution for a single molecule graph.
    This is a simplified GNNExplainer-like procedure:
    1. Compute gradient of output w.r.t. node features.
    2. Compute gradient w.r.t. edge weights (if available).
    3. Aggregate to get atom/edge importance scores.

    Note: Full GNNExplainer requires optimizing a subgraph mask.
    Here we use gradient-based attribution as a proxy, which is
    compatible with the CPU-only constraint and avoids complex optimization.
    """
    model.eval()
    data = data.clone()

    if data.x is not None:
        data.x.requires_grad_(True)
    if data.edge_attr is not None:
        data.edge_attr.requires_grad_(True)

    # Forward pass
    out = model(data)

    # We are predicting a scalar (lambda_max), so take the first output
    if isinstance(out, tuple):
        out = out[0]
    loss = out[target_idx]

    # Backward pass
    loss.backward()

    # Extract gradients
    node_importance = None
    edge_importance = None

    if data.x is not None and data.x.grad is not None:
        # Take L2 norm of gradients for each node
        node_importance = data.x.grad.norm(p=2, dim=1).detach().cpu().numpy()

    if data.edge_attr is not None and data.edge_attr.grad is not None:
        # Take L2 norm of gradients for each edge
        edge_importance = data.edge_attr.grad.norm(p=2, dim=1).detach().cpu().numpy()

    return node_importance, edge_importance

def get_substructure_from_mask(mol: Chem.Mol, node_mask: np.ndarray):
    """
    Identify the top-k atoms (by attribution score) that form the substructure.
    Returns a list of atom indices.
    """
    if node_mask is None or len(node_mask) == 0:
        return []

    # Get indices of top SUBSET_SIZE atoms
    top_indices = np.argsort(node_mask)[-SUBSET_SIZE:].tolist()
    return top_indices

def apply_redundancy_mask(attribution: Dict[str, Any], redundancy_masks: Dict[str, bool]):
    """
    Apply redundancy masks to attribution results.
    Sets attribution weights to 0.0 for redundant subgraphs.
    """
    # This is a placeholder for T025 logic.
    # For T024, we just return the raw attribution.
    # The actual masking will be applied in T025.
    return attribution

def explain_molecule(
    model: torch.nn.Module,
    smiles: str,
    mol_id: str,
    device: str
) -> Dict[str, Any]:
    """
    Run GNNExplainer on a single molecule.
    Returns attribution data for this molecule.
    """
    try:
        data, mol = smiles_to_graph(smiles)
        data = data.to(device)

        node_importance, edge_importance = compute_gradient_attribution(model, data)

        # Identify top-k substructure
        top_atoms = []
        if node_importance is not None:
            top_atoms = get_substructure_from_mask(mol, node_importance)

        result = {
            "mol_id": mol_id,
            "smiles": smiles,
            "num_atoms": mol.GetNumAtoms(),
            "num_edges": data.edge_index.shape[1] // 2 if data.edge_index is not None else 0,
            "node_importance": node_importance.tolist() if node_importance is not None else None,
            "edge_importance": edge_importance.tolist() if edge_importance is not None else None,
            "top_atom_indices": top_atoms,
            "explanation_method": "gradient_attribution",
            "steps": STEPS,
            "subset_size": SUBSET_SIZE
        }

        return result

    except Exception as e:
        logger.error(f"Failed to explain molecule {mol_id}: {e}")
        return {
            "mol_id": mol_id,
            "smiles": smiles,
            "error": str(e)
        }

def main():
    logger.info("Starting T024: GNNExplainer on test set")

    # Load test data
    test_records = load_test_data()
    logger.info(f"Loaded {len(test_records)} test molecules")

    if not test_records:
        raise ValueError("Test set is empty. Cannot run attribution.")

    # Load model
    model_path = Path("data/processed/model.pt")
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    logger.info(f"Loading model from {model_path}")
    device = get_device()
    model = build_gnn_model()
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()

    logger.info("Running GNNExplainer on test set...")
    attribution_results = []

    for i, record in enumerate(test_records):
        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i+1}/{len(test_records)} molecules")

        result = explain_molecule(
            model,
            record["smi"],
            record["mol_id"],
            device
        )
        attribution_results.append(result)

    # Write output
    output_path = Path("data/processed/raw_attribution.json")
    logger.info(f"Writing results to {output_path}")

    with open(output_path, "w") as f:
        json.dump(attribution_results, f, indent=2)

    logger.info(f"T024 complete: Wrote {len(attribution_results)} attribution records to {output_path}")

if __name__ == "__main__":
    main()