"""
T023b: GNN Redundancy Check (Latent Cosine Similarity)

Calculates latent cosine similarity for GNN subgraphs using the trained model.
Flags subgraphs with similarity > 0.9.
Generates redundancy_masks.json.
Applies masking to attribution weights.

Dependency: T015a (Trained GNN model 'model.pt')
Dependency: T024 (Raw attribution 'raw_attribution.json' - must exist or be generated)
Output: data/processed/redundancy_masks.json, data/processed/masked_attribution.json
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
import torch
from torch_geometric.data import Data
from rdkit import Chem
from rdkit.Chem import AllChem

# Configure logging to match project standard
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
MODEL_FILE = DATA_PROCESSED / "model.pt"
RAW_ATTR_FILE = DATA_PROCESSED / "raw_attribution.json"
MASKED_ATTR_FILE = DATA_PROCESSED / "masked_attribution.json"
MASKS_FILE = DATA_PROCESSED / "redundancy_masks.json"

# Parameters
SIMILARITY_THRESHOLD = 0.9
DEVICE = "cpu"

def load_gnn_model() -> torch.nn.Module:
    """Load the trained GNN model."""
    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Trained model not found at {MODEL_FILE}. "
            "Run code/train.py first (Task T015a)."
        )
    
    # Import model architecture from sibling module
    # We need to reconstruct the model to load weights
    # Assuming the model class is 'MPNN' defined in code/model.py
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "code"))
        from model import MPNN, build_gnn_model
    except ImportError as e:
        logger.error(f"Failed to import model architecture: {e}")
        raise

    # Heuristic: Try to load the state dict and infer architecture
    # In a real scenario, we would save the config with the model
    # For now, we assume standard params if not saved
    try:
        checkpoint = torch.load(MODEL_FILE, map_location=DEVICE, weights_only=True)
        state_dict = checkpoint.get('model_state_dict', checkpoint)
        
        # Attempt to build model with common defaults
        # These should match the training script T015a
        model = build_gnn_model(
            num_atom_types=65, # Standard RDKit atom mapping size
            num_bond_types=12, # Standard RDKit bond mapping size
            hidden_dim=128,
            num_layers=2
        )
        model.load_state_dict(state_dict)
        model.to(DEVICE)
        model.eval()
        logger.info(f"Successfully loaded model from {MODEL_FILE}")
        return model
    except Exception as e:
        logger.error(f"Failed to load model weights: {e}")
        raise

def smiles_to_graph(smiles: str) -> Optional[Data]:
    """Convert SMILES to PyG Data object for the GNN."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    # Get atom features
    # Map RDKit atom types to integers
    atom_types = []
    for atom in mol.GetAtoms():
        atom_types.append(atom.GetAtomicNum())
    
    # Get bond features
    # Map RDKit bond types to integers
    edge_indices = []
    edge_attrs = []
    for bond in mol.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()
        edge_indices.append([i, j])
        edge_indices.append([j, i]) # Undirected
        
        # Simple bond type encoding
        bt = bond.GetBondType()
        bond_type = 1 if bt == Chem.BondType.SINGLE else \
                    2 if bt == Chem.BondType.DOUBLE else \
                    3 if bt == Chem.BondType.TRIPLE else 4
        edge_attrs.append(bond_type)
        edge_attrs.append(bond_type)

    edge_index = torch.tensor(edge_indices, dtype=torch.long).t().contiguous()
    edge_attr = torch.tensor(edge_attrs, dtype=torch.float).unsqueeze(1)
    x = torch.tensor(atom_types, dtype=torch.float).unsqueeze(1)

    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
    return data

def extract_subgraph_latents(model: torch.nn.Module, graphs: List[Data]) -> Dict[str, torch.Tensor]:
    """
    Run forward pass to extract latent representations for subgraphs.
    We define 'subgraph' here as the graph-level embedding (readout).
    Returns a dict mapping molecule_id (index) to latent vector.
    """
    latents = {}
    model.eval()
    
    with torch.no_grad():
        for idx, data in enumerate(graphs):
            if data is None:
                continue
            data = data.to(DEVICE)
            try:
                # Forward pass - assumes model outputs graph embedding directly
                # or we need to sum/mean pool node embeddings
                # MPNN usually returns (batch, hidden_dim)
                out = model(data) 
                # If out is node-level, pool it
                if out.dim() == 2 and out.size(0) == data.num_nodes:
                    # Mean pooling
                    latent = out.mean(dim=0)
                elif out.dim() == 2:
                    latent = out.squeeze(0)
                else:
                    latent = out
                
                latents[f"mol_{idx}"] = latent.cpu()
            except Exception as e:
                logger.warning(f"Failed to compute latent for molecule {idx}: {e}")
    
    return latents

def calculate_cosine_similarity_matrix(latents: Dict[str, torch.Tensor]) -> Tuple[Dict[str, str], np.ndarray, List[str]]:
    """
    Calculate pairwise cosine similarity between all latent vectors.
    Returns a map of (id1, id2) -> similarity, and the matrix.
    """
    ids = sorted(latents.keys())
    n = len(ids)
    if n == 0:
        return {}, np.zeros((0,0)), []
    
    vectors = torch.stack([latents[i] for i in ids])
    
    # Normalize
    norms = vectors.norm(dim=1, keepdim=True)
    norms[norms == 0] = 1 # Avoid div by zero
    normalized = vectors / norms
    
    # Cosine similarity = dot product of normalized vectors
    sim_matrix = torch.matmul(normalized, normalized.T).numpy()
    
    sim_map = {}
    for i in range(n):
        for j in range(i + 1, n):
            sim_map[(ids[i], ids[j])] = float(sim_matrix[i, j])
    
    return sim_map, sim_matrix, ids

def identify_redundant_subgraphs(sim_matrix: np.ndarray, ids: List[str]) -> Dict[str, bool]:
    """
    Identify subgraphs (molecules) that are redundant (similarity > threshold).
    We flag a subgraph as redundant if it has high similarity to ANY other subgraph.
    In a strict sense, we might cluster them, but here we flag the 'duplicate' ones.
    Strategy: If sim(i, j) > 0.9, mark j as redundant (assuming i is the representative).
    """
    masks = {sid: False for sid in ids}
    n = len(ids)
    
    for i in range(n):
        for j in range(i + 1, n):
            if sim_matrix[i, j] > SIMILARITY_THRESHOLD:
                # Mark the second one as redundant to keep the first
                masks[ids[j]] = True
                logger.debug(f"Redundant: {ids[j]} similar to {ids[i]} (sim={sim_matrix[i, j]:.3f})")
    
    logger.info(f"Total subgraphs: {n}")
    logger.info(f"Redundant subgraphs flagged: {sum(masks.values())}")
    return masks

def apply_masks_to_attribution(raw_attr: Dict, masks: Dict[str, bool]) -> Dict:
    """
    Apply redundancy masks to raw attribution data.
    If a molecule_id is flagged as redundant, set all its weights to 0.0.
    """
    masked_attr = {}
    for mol_id, data in raw_attr.items():
        if masks.get(mol_id, False):
            # Zero out weights
            masked_data = {
                "atom_weights": {k: 0.0 for k in data.get("atom_weights", {})},
                "bond_weights": {k: 0.0 for k in data.get("bond_weights", {})}
            }
            masked_attr[mol_id] = masked_data
            logger.debug(f"Masked attribution for {mol_id}")
        else:
            masked_attr[mol_id] = data
    
    return masked_attr

def main():
    logger.info("Starting T023b: GNN Redundancy Check")
    
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    # 1. Load Trained Model
    try:
        model = load_gnn_model()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # 2. Load Raw Attribution (Input from T024)
    if not RAW_ATTR_FILE.exists():
        logger.error(f"Raw attribution file not found: {RAW_ATTR_FILE}. "
                     "Run code/explain.py (Task T024) first.")
        # We can't proceed without raw attribution to mask
        sys.exit(1)
    
    with open(RAW_ATTR_FILE, 'r') as f:
        raw_attribution = json.load(f)
    
    logger.info(f"Loaded raw attribution for {len(raw_attribution)} molecules.")

    # 3. Prepare Graphs and Extract Latents
    # We need to re-construct graphs for the molecules in the attribution file
    # to compute their latent representations using the model.
    # We assume the keys in raw_attribution are molecule IDs or indices.
    # If they are indices, we need the SMILES. If they are SMILES, we parse them.
    # Assuming keys are "mol_0", "mol_1"... or similar, and we need to map to SMILES.
    # However, we don't have the SMILES list here directly unless we load the dataset again.
    # To be robust, we will try to load the test split from train_val_test.csv.
    
    input_df_path = DATA_PROCESSED / "train_val_test.csv"
    if not input_df_path.exists():
        logger.error(f"Input data {input_df_path} not found. Cannot reconstruct graphs.")
        sys.exit(1)
    
    df = pd.read_csv(input_df_path)
    # Filter for test set if possible, otherwise use all
    if 'split' in df.columns:
        test_df = df[df['split'] == 'test'].reset_index(drop=True)
    else:
        test_df = df.copy()
    
    logger.info(f"Processing {len(test_df)} molecules from test set.")
    
    graphs = []
    valid_indices = []
    for idx, row in test_df.iterrows():
        smi = row['smi']
        g = smiles_to_graph(smi)
        if g is not None:
            graphs.append(g)
            valid_indices.append(idx)
        else:
            logger.warning(f"Invalid SMILES at index {idx}, skipping.")
    
    if len(graphs) == 0:
        logger.error("No valid graphs to process.")
        sys.exit(1)
    
    # 4. Extract Latents
    logger.info("Extracting latent representations...")
    latents = extract_subgraph_latents(model, graphs)
    
    # 5. Calculate Similarity
    logger.info("Calculating pairwise cosine similarities...")
    sim_map, sim_matrix, ids = calculate_cosine_similarity_matrix(latents)
    
    # 6. Identify Redundant Subgraphs
    masks = identify_redundant_subgraphs(sim_matrix, ids)
    
    # 7. Save Redundancy Masks
    with open(MASKS_FILE, 'w') as f:
        json.dump(masks, f, indent=2)
    logger.info(f"Redundancy masks written to {MASKS_FILE}")
    
    # 8. Apply Masks to Attribution
    # Note: The keys in raw_attribution must match the logic used to generate them.
    # If raw_attribution keys are "mol_0", "mol_1" corresponding to the test set order,
    # we can apply masks directly.
    # If keys are SMILES, we need to map.
    # Assuming keys match the 'ids' generated from the test set order.
    
    # We need to map the 'ids' (mol_0, mol_1...) to the keys in raw_attribution.
    # If raw_attribution keys are not in the same format, this step might fail.
    # Let's assume the keys in raw_attribution are exactly the 'ids' we generated.
    # If not, we try to match by index if keys are numeric strings.
    
    final_raw_keys = list(raw_attribution.keys())
    if len(final_raw_keys) != len(ids):
        logger.warning(f"Key count mismatch: Attribution has {len(final_raw_keys)}, Latents has {len(ids)}. "
                       "Attempting to apply masks by index order if keys are numeric.")
    
    # Simple heuristic: if keys are "mol_X", we use them.
    # If not, we assume the order in raw_attribution matches the order in test_df.
    # We will apply the mask to the i-th item in raw_attribution if it corresponds to ids[i].
    
    # Reconstruct raw_attr in a list to apply masks by index
    # This assumes the order of keys in raw_attribution is deterministic and matches 'ids'
    # If raw_attribution is a dict, order is preserved in Python 3.7+
    attr_items = list(raw_attribution.items())
    
    masked_attribution = {}
    for i, (key, val) in enumerate(attr_items):
        if i < len(ids):
            mol_id = ids[i]
            is_redundant = masks.get(mol_id, False)
        else:
            is_redundant = False # Fallback for extra items
        
        if is_redundant:
            masked_val = {
                "atom_weights": {k: 0.0 for k in val.get("atom_weights", {})},
                "bond_weights": {k: 0.0 for k in val.get("bond_weights", {})}
            }
            masked_attribution[key] = masked_val
        else:
            masked_attribution[key] = val
    
    with open(MASKED_ATTR_FILE, 'w') as f:
        json.dump(masked_attribution, f, indent=2)
    
    logger.info(f"Masked attribution written to {MASKED_ATTR_FILE}")
    logger.info("T023b completed successfully.")

if __name__ == "__main__":
    main()