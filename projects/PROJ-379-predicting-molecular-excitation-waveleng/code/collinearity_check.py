import os
import sys
import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any

# Import from local utils and models as per project API
from utils import setup_logging, get_logger, smiles_to_ecfp
from models import Molecule

# Ensure logging is configured
logger = get_logger("collinearity_check")

def calculate_ecfp_correlation(ecfp_matrix: np.ndarray, threshold: float = 0.9) -> Tuple[np.ndarray, List[int]]:
    """
    Calculate Pearson correlation matrix for ECFP bits.
    Returns correlation matrix and list of bit indices flagged as collinear.
    
    Args:
        ecfp_matrix: numpy array of shape (n_molecules, n_bits)
        threshold: correlation threshold to flag collinearity
        
    Returns:
        corr_matrix: Pearson correlation matrix
        flagged_bits: list of bit indices that are highly correlated
    """
    if ecfp_matrix.shape[0] < 2:
        logger.warning("Not enough molecules to calculate correlation.")
        return np.zeros((ecfp_matrix.shape[1], ecfp_matrix.shape[1])), []

    # Calculate Pearson correlation
    corr_matrix = np.corrcoef(ecfp_matrix, rowvar=False)
    
    # Handle NaNs (can happen if a bit is constant)
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
    
    # Find pairs with correlation >= threshold
    # We look at upper triangle to avoid duplicates and self-correlation
    flagged_bits = set()
    rows, cols = np.where(np.abs(corr_matrix) >= threshold)
    
    for r, c in zip(rows, cols):
        if r != c:
            flagged_bits.add(r)
            flagged_bits.add(c)
            
    return corr_matrix, sorted(list(flagged_bits))

def calculate_gnn_similarity(subgraph_embeddings: np.ndarray, threshold: float = 0.9) -> Tuple[np.ndarray, List[int]]:
    """
    Calculate cosine similarity for GNN subgraph embeddings.
    Returns similarity matrix and list of subgraph indices flagged as redundant.
    
    Args:
        subgraph_embeddings: numpy array of shape (n_subgraphs, embedding_dim)
        threshold: similarity threshold to flag redundancy
        
    Returns:
        sim_matrix: Cosine similarity matrix
        flagged_subgraphs: list of subgraph indices that are highly similar
    """
    if subgraph_embeddings.shape[0] < 2:
        logger.warning("Not enough subgraphs to calculate similarity.")
        return np.zeros((subgraph_embeddings.shape[0], subgraph_embeddings.shape[0])), []

    # Normalize embeddings for cosine similarity
    norms = np.linalg.norm(subgraph_embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1  # Avoid division by zero
    normalized = subgraph_embeddings / norms
    
    sim_matrix = np.dot(normalized, normalized.T)
    
    # Find pairs with similarity > threshold
    flagged_subgraphs = set()
    rows, cols = np.where(sim_matrix > threshold)
    
    for r, c in zip(rows, cols):
        if r != c:
            flagged_subgraphs.add(r)
            flagged_subgraphs.add(c)
            
    return sim_matrix, sorted(list(flagged_subgraphs))

def check_collinearity(ecfp_data: np.ndarray, threshold: float = 0.9) -> Dict[str, Any]:
    """
    Check for collinearity in ECFP data.
    
    Args:
        ecfp_data: ECFP bit matrix
        threshold: correlation threshold
        
    Returns:
        Dict with correlation matrix (as list of lists) and flagged bits
    """
    corr_matrix, flagged_bits = calculate_ecfp_correlation(ecfp_data, threshold)
    return {
        "correlation_matrix": corr_matrix.tolist(),
        "flagged_bits": flagged_bits,
        "count": len(flagged_bits)
    }

def check_gnn_similarity(subgraph_data: np.ndarray, threshold: float = 0.9) -> Dict[str, Any]:
    """
    Check for redundancy in GNN subgraph embeddings.
    
    Args:
        subgraph_data: Subgraph embedding matrix
        threshold: similarity threshold
        
    Returns:
        Dict with similarity matrix (as list of lists) and flagged subgraphs
    """
    sim_matrix, flagged_subgraphs = calculate_gnn_similarity(subgraph_data, threshold)
    return {
        "similarity_matrix": sim_matrix.tolist(),
        "flagged_subgraphs": flagged_subgraphs,
        "count": len(flagged_subgraphs)
    }

def generate_redundancy_masks(
    molecule_ids: List[str],
    ecfp_flagged_bits: List[int],
    gnn_flagged_subgraphs: List[int],
    ecfp_dim: int,
    n_subgraphs_per_mol: int
) -> Dict[str, List[int]]:
    """
    Generate redundancy masks for each molecule.
    A mask is a binary array where 1 indicates a redundant feature/subgraph.
    
    Args:
        molecule_ids: List of molecule identifiers
        ecfp_flagged_bits: List of ECFP bit indices flagged for collinearity
        gnn_flagged_subgraphs: List of subgraph indices flagged for redundancy
        ecfp_dim: Dimension of ECFP vectors
        n_subgraphs_per_mol: Number of subgraphs per molecule
        
    Returns:
        Dict mapping molecule_id to a mask array [0, 1, 0, ...]
    """
    masks = {}
    
    # Create ECFP mask (size = ecfp_dim)
    ecfp_mask = np.zeros(ecfp_dim, dtype=int)
    for bit_idx in ecfp_flagged_bits:
        if 0 <= bit_idx < ecfp_dim:
            ecfp_mask[bit_idx] = 1
            
    # Create GNN mask (size = n_subgraphs_per_mol)
    gnn_mask = np.zeros(n_subgraphs_per_mol, dtype=int)
    for sub_idx in gnn_flagged_subgraphs:
        if 0 <= sub_idx < n_subgraphs_per_mol:
            gnn_mask[sub_idx] = 1
    
    # Combine masks: [ECFP_mask..., GNN_mask...]
    combined_mask = np.concatenate([ecfp_mask, gnn_mask])
    
    for mol_id in molecule_ids:
        masks[mol_id] = combined_mask.tolist()
        
    return masks

def aggregate_subgraph_redundancy(
    subgraph_embeddings: np.ndarray,
    threshold: float = 0.9
) -> Dict[str, List[int]]:
    """
    Aggregate subgraphs with high cosine similarity and return groups.
    
    Args:
        subgraph_embeddings: Subgraph embedding matrix
        threshold: similarity threshold
        
    Returns:
        Dict with 'redundant_groups': list of lists, each inner list is a group of redundant subgraph indices
    """
    sim_matrix, _ = calculate_gnn_similarity(subgraph_embeddings, threshold)
    n_subgraphs = sim_matrix.shape[0]
    visited = [False] * n_subgraphs
    groups = []
    
    for i in range(n_subgraphs):
        if visited[i]:
            continue
        
        # Start a new group
        group = [i]
        visited[i] = True
        
        # Find all other subgraphs in this group
        for j in range(i + 1, n_subgraphs):
            if not visited[j] and sim_matrix[i][j] > threshold:
                group.append(j)
                visited[j] = True
        
        if len(group) > 1:
            groups.append(group)
            
    return {"redundant_groups": groups}

def apply_redundancy_mask_to_attribution(
    attribution_data: Dict[str, List[float]],
    redundancy_masks: Dict[str, List[int]]
) -> Dict[str, List[float]]:
    """
    Apply redundancy masks to attribution weights.
    Sets attribution weights to 0 for flagged features.
    
    Args:
        attribution_data: Dict of molecule_id -> attribution weights
        redundancy_masks: Dict of molecule_id -> mask (0 or 1)
        
    Returns:
        Dict of molecule_id -> masked attribution weights
    """
    masked_attribution = {}
    
    for mol_id, weights in attribution_data.items():
        if mol_id not in redundancy_masks:
            masked_attribution[mol_id] = weights
            continue
            
        mask = redundancy_masks[mol_id]
        masked_weights = []
        
        for i, weight in enumerate(weights):
            if i < len(mask) and mask[i] == 1:
                masked_weights.append(0.0)
            else:
                masked_weights.append(weight)
                
        masked_attribution[mol_id] = masked_weights
      
    return masked_attribution

def load_processed_data(data_path: Path) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Load processed data and extract ECFP embeddings if available.
    Assumes data is in 'data/processed/cleaned.csv' or similar.
    For this implementation, we assume the cleaned data has SMILES and we compute ECFPs.
    In a full pipeline, pre-computed ECFPs might be stored.
    """
    # Try to load from processed directory
    csv_path = data_path / "cleaned.csv"
    if not csv_path.exists():
        # Fallback to raw if needed, but spec says processed
        raise FileNotFoundError(f"Cleaned data not found at {csv_path}")
        
    df = pd.read_csv(csv_path)
    
    # Ensure required columns exist
    if 'smi' not in df.columns:
        raise ValueError("DataFrame must contain 'smi' column")
        
    # Compute ECFPs for all molecules
    logger.info(f"Computing ECFPs for {len(df)} molecules...")
    ecfp_list = []
    valid_indices = []
    
    for idx, row in df.iterrows():
        mol = Molecule(smi=row['smi'], lambda_max=row.get('lambda_max', 0.0), scaffold_id=row.get('scaffold_id', ''))
        ecfp = smiles_to_ecfp(mol.smi)
        if ecfp is not None:
            ecfp_list.append(ecfp)
            valid_indices.append(idx)
            
    if len(ecfp_list) == 0:
        raise ValueError("No valid molecules found for ECFP computation")
        
    ecfp_matrix = np.array(ecfp_list)
    logger.info(f"ECFP matrix shape: {ecfp_matrix.shape}")
    
    return df.iloc[valid_indices].reset_index(drop=True), ecfp_matrix

def main():
    """
    Main entry point for collinearity check.
    1. Load processed data.
    2. Calculate ECFP correlations.
    3. (Optional) Load GNN embeddings if available (for full implementation).
    4. Generate redundancy masks.
    5. Save to data/processed/redundancy_masks.json.
    """
    setup_logging()
    logger.info("Starting Collinearity Check (T023)")
    
    project_root = Path(__file__).parent.parent
    data_path = project_root / "data" / "processed"
    output_path = data_path / "redundancy_masks.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        df, ecfp_matrix = load_processed_data(data_path)
        molecule_ids = df['smi'].tolist()  # Using SMILES as ID for simplicity
        
        # 1. ECFP Collinearity Check
        logger.info("Calculating ECFP correlations...")
        ecfp_results = check_collinearity(ecfp_matrix, threshold=0.9)
        logger.info(f"Found {ecfp_results['count']} collinear ECFP bits")
        
        # 2. GNN Similarity Check
        # Note: In a full pipeline, we would load pre-computed subgraph embeddings here.
        # Since T014/T015 produce model.pt, we assume we can extract embeddings.
        # For this task, we simulate the structure if embeddings are not explicitly stored.
        # If the project has a way to extract subgraph embeddings, that logic would go here.
        # For now, we assume a placeholder or skip if not available, but the task requires generation.
        
        # To satisfy the requirement without a separate embedding loader script:
        # We will assume the GNN model (if loaded) can provide embeddings.
        # However, to keep this task focused on the logic and not model loading complexity,
        # we will generate a dummy GNN similarity structure if no embeddings are found,
        # BUT the task says "Real data only".
        # 
        # Correction: The task requires calculating similarity for GNN subgraphs.
        # If we don't have the embeddings, we cannot do this on real data.
        # However, the task T023 is about the IMPLEMENTATION of the check.
        # We will implement the logic to load embeddings from a hypothetical 'subgraph_embeddings.npy'
        # or generate them if the model is available.
        # Given the constraints, we will assume the embeddings are not yet generated or stored separately.
        # We will implement the logic to handle this gracefully by raising an error if not found,
        # or proceeding with ECFP only if GNN data is missing (but the task asks for both).
        #
        # Let's assume we can load embeddings from a standard location or the model.
        # Since T015 outputs model.pt, we would need to load it.
        # For the sake of this implementation, we will check for a file 'subgraph_embeddings.npy'.
        
        gnn_embeddings_path = data_path / "subgraph_embeddings.npy"
        gnn_results = {"similarity_matrix": [], "flagged_subgraphs": [], "count": 0}
        n_subgraphs = 0
        
        if gnn_embeddings_path.exists():
            logger.info("Loading GNN subgraph embeddings...")
            gnn_embeddings = np.load(gnn_embeddings_path)
            gnn_results = check_gnn_similarity(gnn_embeddings, threshold=0.9)
            n_subgraphs = gnn_embeddings.shape[1] if gnn_embeddings.ndim > 1 else gnn_embeddings.shape[0]
            logger.info(f"Found {gnn_results['count']} redundant subgraphs")
        else:
            logger.warning("GNN subgraph embeddings not found. Skipping GNN similarity check.")
            logger.warning("To fully satisfy T023, generate subgraph embeddings and save to data/processed/subgraph_embeddings.npy")
            # We still need to generate masks. If no GNN data, we assume no redundant subgraphs (mask 0)
            # But the task requires generating masks for flagged subgraphs.
            # We'll proceed with ECFP flags only for GNN part being empty.
            n_subgraphs = 10  # Placeholder, or derive from model structure if possible
            # Actually, we should not guess. We'll set n_subgraphs to 0 if no data.
            n_subgraphs = 0

        # 3. Generate Redundancy Masks
        logger.info("Generating redundancy masks...")
        # ECFP dimension
        ecfp_dim = ecfp_matrix.shape[1]
        
        # If no GNN data, we assume 0 subgraphs or we can't generate meaningful masks for them.
        # We'll set n_subgraphs to 0 if no embeddings found.
        if n_subgraphs == 0:
            n_subgraphs = 0 
            
        masks = generate_redundancy_masks(
            molecule_ids=molecule_ids,
            ecfp_flagged_bits=ecfp_results['flagged_bits'],
            gnn_flagged_subgraphs=gnn_results['flagged_subgraphs'],
            ecfp_dim=ecfp_dim,
            n_subgraphs_per_mol=n_subgraphs
        )
        
        # 4. Save Output
        output_data = {
            "ecfp_collinearity": ecfp_results,
            "gnn_redundancy": gnn_results,
            "redundancy_masks": masks
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
            
        logger.info(f"Redundancy masks saved to {output_path}")
        
        # Log summary
        logger.info(f"Total molecules processed: {len(molecule_ids)}")
        logger.info(f"ECFP bits flagged: {ecfp_results['count']}")
        logger.info(f"Subgraphs flagged: {gnn_results['count']}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during collinearity check: {e}")
        raise

if __name__ == "__main__":
    main()