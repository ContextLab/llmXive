import os
import sys
import json
import logging
from pathlib import Path
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CORRELATION_THRESHOLD = 0.9
SIMILARITY_THRESHOLD = 0.9
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
REDUNDANCY_MASKS_FILE = PROCESSED_DIR / "redundancy_masks.json"
RAW_ATTRIBUTION_FILE = PROCESSED_DIR / "raw_attribution.json"
MASKED_ATTRIBUTION_FILE = PROCESSED_DIR / "masked_attribution.json"


def calculate_ecfp_correlation(ecfp_matrix: np.ndarray) -> np.ndarray:
    """
    Calculate Pearson correlation matrix for ECFP bits.
    
    Args:
        ecfp_matrix: Binary matrix of shape (n_molecules, n_bits)
        
    Returns:
        Correlation matrix of shape (n_bits, n_bits)
    """
    if ecfp_matrix.shape[0] < 2:
        logger.warning("Not enough samples to calculate correlation")
        return np.eye(ecfp_matrix.shape[1])
    
    # Normalize to avoid division by zero for constant bits
    std = np.std(ecfp_matrix, axis=0, ddof=1)
    std[std == 0] = 1
    
    normalized = (ecfp_matrix - np.mean(ecfp_matrix, axis=0)) / std
    corr_matrix = np.dot(normalized.T, normalized) / (normalized.shape[0] - 1)
    return corr_matrix


def calculate_gnn_similarity(subgraph_embeddings: np.ndarray) -> np.ndarray:
    """
    Calculate cosine similarity matrix for GNN subgraph embeddings.
    
    Args:
        subgraph_embeddings: Matrix of shape (n_subgraphs, embedding_dim)
        
    Returns:
        Similarity matrix of shape (n_subgraphs, n_subgraphs)
    """
    if subgraph_embeddings.shape[0] == 0:
        return np.array([]).reshape(0, 0)
        
    # Normalize embeddings
    norms = np.linalg.norm(subgraph_embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1
    normalized = subgraph_embeddings / norms
    
    # Cosine similarity
    similarity_matrix = np.dot(normalized, normalized.T)
    return similarity_matrix


def check_collinearity(ecfp_matrix: np.ndarray) -> tuple:
    """
    Check for ECFP bit collinearity (Pearson r >= 0.9).
    
    Args:
        ecfp_matrix: Binary matrix of ECFP bits
        
    Returns:
        Tuple of (collinear_pairs, collinearity_flags)
        collinear_pairs: List of (bit_i, bit_j) tuples
        collinearity_flags: Boolean array indicating collinear bits
    """
    corr_matrix = calculate_ecfp_correlation(ecfp_matrix)
    n_bits = corr_matrix.shape[0]
    
    collinear_pairs = []
    collinearity_flags = np.zeros(n_bits, dtype=bool)
    
    # Upper triangle (excluding diagonal)
    for i in range(n_bits):
        for j in range(i + 1, n_bits):
            if abs(corr_matrix[i, j]) >= CORRELATION_THRESHOLD:
                collinear_pairs.append((i, j))
                collinearity_flags[i] = True
                collinearity_flags[j] = True
    
    logger.info(f"Found {len(collinear_pairs)} collinear ECFP bit pairs")
    return collinear_pairs, collinearity_flags


def check_gnn_similarity(subgraph_embeddings: np.ndarray) -> tuple:
    """
    Check for GNN subgraph redundancy (cosine similarity > 0.9).
    
    Args:
        subgraph_embeddings: Matrix of subgraph embeddings
        
    Returns:
        Tuple of (redundant_pairs, redundancy_flags)
        redundant_pairs: List of (subgraph_i, subgraph_j) tuples
        redundancy_flags: Boolean array indicating redundant subgraphs
    """
    similarity_matrix = calculate_gnn_similarity(subgraph_embeddings)
    n_subgraphs = similarity_matrix.shape[0]
    
    redundant_pairs = []
    redundancy_flags = np.zeros(n_subgraphs, dtype=bool)
    
    # Upper triangle (excluding diagonal)
    for i in range(n_subgraphs):
        for j in range(i + 1, n_subgraphs):
            if similarity_matrix[i, j] > SIMILARITY_THRESHOLD:
                redundant_pairs.append((i, j))
                redundancy_flags[i] = True
                redundancy_flags[j] = True
    
    logger.info(f"Found {len(redundant_pairs)} redundant GNN subgraph pairs")
    return redundant_pairs, redundancy_flags


def generate_redundancy_masks(ecfp_matrix: np.ndarray, 
                              subgraph_embeddings: np.ndarray = None) -> dict:
    """
    Generate redundancy masks for molecules based on collinearity and redundancy.
    
    Args:
        ecfp_matrix: ECFP bit matrix
        subgraph_embeddings: Optional GNN subgraph embeddings
        
    Returns:
        Dictionary mapping molecule_id to mask array
    """
    # Check ECFP collinearity
    _, ecfp_flags = check_collinearity(ecfp_matrix)
    
    # Initialize masks dictionary
    masks = {}
    
    # For each molecule, create a mask based on ECFP flags
    # Assuming rows in ecfp_matrix correspond to molecules
    n_molecules = ecfp_matrix.shape[0]
    n_bits = ecfp_matrix.shape[1]
    
    for i in range(n_molecules):
        # Create a mask where collinear bits are set to 0 (masked out)
        # or we could use the flags to identify which bits to mask
        # Here we create a binary mask: 1 for active, 0 for redundant
        mask = (~ecfp_flags).astype(int)
        masks[str(i)] = mask.tolist()
    
    # If subgraph embeddings are provided, also check GNN redundancy
    if subgraph_embeddings is not None and subgraph_embeddings.shape[0] > 0:
        _, gnn_flags = check_gnn_similarity(subgraph_embeddings)
        
        # Update masks for molecules that have redundant subgraphs
        # This assumes a mapping between subgraph indices and molecule indices
        # For simplicity, we'll assume 1:1 mapping for now
        if len(gnn_flags) == n_molecules:
            for i in range(n_molecules):
                if gnn_flags[i]:
                    # If the molecule has redundant subgraphs, we might want to
                    # adjust its mask or add a flag
                    # For now, we'll just log this
                    logger.warning(f"Molecule {i} has redundant subgraphs")
    
    # Save masks to file
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with open(REDUNDANCY_MASKS_FILE, 'w') as f:
        json.dump(masks, f, indent=2)
    
    logger.info(f"Saved redundancy masks to {REDUNDANCY_MASKS_FILE}")
    return masks


def aggregate_subgraph_redundancy(attribution_weights: np.ndarray,
                                  subgraph_similarity_matrix: np.ndarray) -> np.ndarray:
    """
    Aggregate subgraphs with latent cosine similarity > 0.9 and mask their 
    individual attribution weights to prevent spurious independent effect claims.
    
    This implements the logic for T036: When subgraphs are highly similar (redundant),
    their individual attribution weights should be masked or aggregated to avoid
    claiming independent effects for essentially the same structural feature.
    
    Args:
        attribution_weights: Array of attribution weights for subgraphs (n_subgraphs,)
        subgraph_similarity_matrix: Cosine similarity matrix of subgraph embeddings (n_subgraphs, n_subgraphs)
        
    Returns:
        Modified attribution weights with redundant subgraphs masked (set to 0)
    """
    if attribution_weights.shape[0] == 0:
        return attribution_weights
        
    n_subgraphs = len(attribution_weights)
    masked_weights = attribution_weights.copy()
    
    # Identify redundant subgraph pairs
    redundant_pairs = []
    for i in range(n_subgraphs):
        for j in range(i + 1, n_subgraphs):
            if subgraph_similarity_matrix[i, j] > SIMILARITY_THRESHOLD:
                redundant_pairs.append((i, j))
    
    # Group redundant subgraphs and mask their weights
    # We'll use a union-find approach to group connected redundant subgraphs
    parent = list(range(n_subgraphs))
    
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py
    
    # Union all redundant pairs
    for i, j in redundant_pairs:
        union(i, j)
    
    # Find groups of redundant subgraphs
    groups = {}
    for i in range(n_subgraphs):
        root = find(i)
        if root not in groups:
            groups[root] = []
        groups[root].append(i)
    
    # For each group with more than one subgraph, mask all but the one with highest weight
    # This prevents claiming independent effects for redundant subgraphs
    masked_count = 0
    for root, members in groups.items():
        if len(members) > 1:
            # Find the subgraph with the highest absolute attribution weight
            max_idx = max(members, key=lambda idx: abs(attribution_weights[idx]))
            
            # Mask all other subgraphs in the group
            for idx in members:
                if idx != max_idx:
                    masked_weights[idx] = 0.0
                    masked_count += 1
    
    logger.info(f"Masked {masked_count} redundant subgraph attribution weights out of {n_subgraphs}")
    return masked_weights


def apply_redundancy_mask_to_attribution(attribution_file: str = None,
                                         similarity_file: str = None,
                                         output_file: str = None):
    """
    Load raw attribution weights and subgraph similarity matrix, apply redundancy masking,
    and save the masked attribution.
    
    Args:
        attribution_file: Path to raw attribution JSON file
        similarity_file: Path to subgraph similarity matrix JSON file (optional)
        output_file: Path to output masked attribution JSON file
    """
    if attribution_file is None:
        attribution_file = str(RAW_ATTRIBUTION_FILE)
    if output_file is None:
        output_file = str(MASKED_ATTRIBUTION_FILE)
        
    logger.info(f"Loading raw attribution from {attribution_file}")
    
    # Load raw attribution
    with open(attribution_file, 'r') as f:
        raw_attribution = json.load(f)
    
    # Process each molecule's attribution
    masked_attribution = {}
    
    for mol_id, data in raw_attribution.items():
        if 'subgraph_weights' not in data or 'subgraph_similarity' not in data:
            # If similarity data is missing, just copy the weights
            masked_attribution[mol_id] = data
            continue
            
        weights = np.array(data['subgraph_weights'])
        similarity = np.array(data['subgraph_similarity'])
        
        # Apply redundancy aggregation
        masked_weights = aggregate_subgraph_redundancy(weights, similarity)
        
        # Create masked attribution entry
        masked_data = data.copy()
        masked_data['subgraph_weights'] = masked_weights.tolist()
        masked_data['was_masked'] = not np.array_equal(weights, masked_weights)
        masked_attribution[mol_id] = masked_data
    
    # Save masked attribution
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(masked_attribution, f, indent=2)
    
    logger.info(f"Saved masked attribution to {output_path}")
    return masked_attribution


def main():
    """Main entry point for collinearity check and subgraph redundancy aggregation."""
    parser = argparse.ArgumentParser(description='Check collinearity and aggregate subgraph redundancy')
    parser.add_argument('--ecfp-file', type=str, help='Path to ECFP matrix file (NPZ)')
    parser.add_argument('--embeddings-file', type=str, help='Path to GNN embeddings file (NPZ)')
    parser.add_argument('--attribution-file', type=str, default=None, help='Path to raw attribution file')
    parser.add_argument('--similarity-file', type=str, default=None, help='Path to subgraph similarity file')
    parser.add_argument('--output-file', type=str, default=None, help='Path to output masked attribution file')
    
    args = parser.parse_args()
    
    # If attribution and similarity files are provided, apply redundancy masking
    if args.attribution_file or Path(RAW_ATTRIBUTION_FILE).exists():
        attr_file = args.attribution_file if args.attribution_file else str(RAW_ATTRIBUTION_FILE)
        
        if Path(attr_file).exists():
            apply_redundancy_mask_to_attribution(
                attribution_file=attr_file,
                output_file=args.output_file
            )
        else:
            logger.warning(f"Raw attribution file not found: {attr_file}")
    else:
        # If no attribution file, just generate redundancy masks from ECFP/embeddings
        if args.ecfp_file and Path(args.ecfp_file).exists():
            ecfp_matrix = np.load(args.ecfp_file)['arr_0']
            subgraph_embeddings = None
            if args.embeddings_file and Path(args.embeddings_file).exists():
                subgraph_embeddings = np.load(args.embeddings_file)['arr_0']
            
            generate_redundancy_masks(ecfp_matrix, subgraph_embeddings)
        else:
            logger.info("No ECFP file provided, skipping mask generation")
    
    logger.info("Collinearity check and subgraph redundancy aggregation complete")


if __name__ == '__main__':
    main()