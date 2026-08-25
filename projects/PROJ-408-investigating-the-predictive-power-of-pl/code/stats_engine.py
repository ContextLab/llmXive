import logging
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set, Union
import numpy as np
import pandas as pd
from scipy.spatial.distance import squareform, pdist
from scipy.stats import pearsonr
from itertools import combinations

from config import get_config
from logging_config import get_logger

logger = get_logger(__name__)

def load_distance_matrix(path: Union[str, Path]) -> np.ndarray:
    """
    Loads a distance matrix from a CSV file.
    Expects a square matrix with headers and index.
    """
    df = pd.read_csv(path, index_col=0)
    return df.values.astype(float)

def calculate_jaccard_dissimilarity_matrix(
    metabolite_profiles: Dict[str, Set[str]],
    species_order: Optional[List[str]] = None
) -> Tuple[np.ndarray, List[str]]:
    """
    Calculates the Jaccard dissimilarity matrix from binary metabolite presence/absence.
    
    Args:
        metabolite_profiles: Dict mapping species_id to set of metabolite IDs.
        species_order: Optional list of species IDs to enforce row/column order.
    
    Returns:
        Tuple of (distance_matrix, species_order)
    """
    if not species_order:
        species_order = sorted(metabolite_profiles.keys())
    
    # Create binary matrix
    all_metabolites = set()
    for s in species_order:
        if s in metabolite_profiles:
            all_metabolites.update(metabolite_profiles[s])
    
    all_metabolites = sorted(list(all_metabolites))
    
    binary_matrix = np.zeros((len(species_order), len(all_metabolites)), dtype=bool)
    
    for i, species in enumerate(species_order):
        if species in metabolite_profiles:
            for j, metab in enumerate(all_metabolites):
                if metab in metabolite_profiles[species]:
                    binary_matrix[i, j] = True
    
    # Calculate Jaccard distance (1 - Jaccard similarity)
    # pdist returns condensed distance matrix
    distances = pdist(binary_matrix, metric='jaccard')
    full_matrix = squareform(distances)
    
    return full_matrix, species_order

def run_mantel_test(
    matrix1: np.ndarray,
    matrix2: np.ndarray,
    n_permutations: int = 999,
    method: str = "pearson"
) -> Dict[str, float]:
    """
    Performs a Mantel test between two distance matrices.
    
    Args:
        matrix1: First distance matrix (n x n)
        matrix2: Second distance matrix (n x n)
        n_permutations: Number of permutations for p-value calculation
        method: Correlation method ('pearson' or 'spearman')
    
    Returns:
        Dict with 'r', 'p_value', and 'null_distribution' (list of r values)
    """
    if matrix1.shape != matrix2.shape:
        raise ValueError("Matrices must have the same shape")
    
    n = matrix1.shape[0]
    if n == 0:
        return {"r": 0.0, "p_value": 1.0, "null_distribution": []}

    # Flatten upper triangle (excluding diagonal)
    # We use squareform to get the condensed vector if it's not already
    # Assuming inputs are full square matrices
    v1 = squareform(matrix1)
    v2 = squareform(matrix2)
    
    # Calculate observed correlation
    if method == "pearson":
        r_obs, _ = pearsonr(v1, v2)
    elif method == "spearman":
        from scipy.stats import spearmanr
        r_obs, _ = spearmanr(v1, v2)
    else:
        raise ValueError(f"Unsupported method: {method}")
    
    # Permutation test
    null_dist = []
    np.random.seed(get_config().get("random_seed", 42))
    
    for _ in range(n_permutations):
        # Permute rows and columns of matrix2 simultaneously
        # Equivalent to permuting the labels
        perm_indices = np.random.permutation(n)
        p_matrix2 = matrix2[np.ix_(perm_indices, perm_indices)]
        v2_perm = squareform(p_matrix2)
        
        if method == "pearson":
            r_perm, _ = pearsonr(v1, v2_perm)
        else:
            from scipy.stats import spearmanr
            r_perm, _ = spearmanr(v1, v2_perm)
        
        null_dist.append(r_perm)
    
    # Calculate p-value (two-tailed)
    # Count how many permuted r's are as extreme or more extreme than observed
    count_extreme = sum(1 for r in null_dist if abs(r) >= abs(r_obs))
    p_value = (count_extreme + 1) / (n_permutations + 1)
    
    return {
        "r": float(r_obs),
        "p_value": float(p_value),
        "null_distribution": [float(x) for x in null_dist]
    }

def run_partial_mantel_test(
    matrix1: np.ndarray,
    matrix2: np.ndarray,
    matrix3: np.ndarray,
    n_permutations: int = 999,
    method: str = "pearson"
) -> Dict[str, float]:
    """
    Performs a Partial Mantel test.
    Tests correlation between matrix1 and matrix2, controlling for matrix3.
    
    Args:
        matrix1: Dependent variable distance matrix (e.g., metabolite)
        matrix2: Independent variable distance matrix (e.g., phylogeny)
        matrix3: Control variable distance matrix (e.g., climate)
        n_permutations: Number of permutations
        method: Correlation method
    
    Returns:
        Dict with 'partial_r', 'p_value', 'standard_r' (optional), and 'null_distribution'
    """
    if not (matrix1.shape == matrix2.shape == matrix3.shape):
        raise ValueError("All matrices must have the same shape")
    
    n = matrix1.shape[0]
    if n == 0:
        return {"partial_r": 0.0, "p_value": 1.0, "null_distribution": []}
    
    # Flatten upper triangles
    v1 = squareform(matrix1)
    v2 = squareform(matrix2)
    v3 = squareform(matrix3)
    
    # Calculate standard correlations
    if method == "pearson":
        r12, _ = pearsonr(v1, v2)
        r13, _ = pearsonr(v1, v3)
        r23, _ = pearsonr(v2, v3)
    else:
        from scipy.stats import spearmanr
        r12, _ = spearmanr(v1, v2)
        r13, _ = spearmanr(v1, v3)
        r23, _ = spearmanr(v2, v3)
    
    # Calculate partial correlation coefficient
    # r12.3 = (r12 - r13*r23) / sqrt((1-r13^2)(1-r23^2))
    denom = np.sqrt((1 - r13**2) * (1 - r23**2))
    if abs(denom) < 1e-10:
        partial_r = 0.0
    else:
        partial_r = (r12 - r13 * r23) / denom
    
    # Permutation test for significance
    # We permute the rows/cols of matrix2 (and thus v2) to break the link with matrix1
    # while maintaining the structure relative to matrix3? 
    # Standard partial Mantel permutation: Permute the rows/cols of one matrix (say M2)
    # and recalculate partial correlation.
    
    null_dist = []
    np.random.seed(get_config().get("random_seed", 42))
    
    for _ in range(n_permutations):
        perm_indices = np.random.permutation(n)
        # Permute M2
        p_matrix2 = matrix2[np.ix_(perm_indices, perm_indices)]
        v2_perm = squareform(p_matrix2)
        
        # Recalculate partial correlation with permuted M2
        if method == "pearson":
            r12_p, _ = pearsonr(v1, v2_perm)
        else:
            from scipy.stats import spearmanr
            r12_p, _ = spearmanr(v1, v2_perm)
        
        # r13 and r23 change because r23 involves M2
        if method == "pearson":
            r13_p, _ = pearsonr(v1, v3) # M3 unchanged
            r23_p, _ = pearsonr(v2_perm, v3)
        else:
            from scipy.stats import spearmanr
            r13_p, _ = spearmanr(v1, v3)
            r23_p, _ = spearmanr(v2_perm, v3)
        
        denom_p = np.sqrt((1 - r13_p**2) * (1 - r23_p**2))
        if abs(denom_p) < 1e-10:
            r_perm = 0.0
        else:
            r_perm = (r12_p - r13_p * r23_p) / denom_p
        
        null_dist.append(r_perm)
    
    # P-value
    count_extreme = sum(1 for r in null_dist if abs(r) >= abs(partial_r))
    p_value = (count_extreme + 1) / (n_permutations + 1)
    
    return {
        "partial_r": float(partial_r),
        "standard_r": float(r12),
        "p_value": float(p_value),
        "null_distribution": [float(x) for x in null_dist]
    }

def save_mantel_results(results: Dict, output_path: Union[str, Path]) -> None:
    """
    Saves Mantel test results to a JSON file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Mantel results saved to {output_path}")