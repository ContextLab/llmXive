import os
import sys
import logging
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path
from scipy import stats

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# AAL Atlas region indices for Prefrontal and Hippocampal (approximate)
# AAL has 90 regions. Prefrontal: 1-32 (approx), Hippocampal: 65-72 (approx)
# We will use specific indices based on standard AAL mapping if known, otherwise generic.
# Standard AAL:
# Prefrontal Cortex (PFC): often regions 1-32 (Frontal_Sup, Frontal_Mid, etc.)
# Hippocampus: regions 65-68 (Hippocampus_L/R) and 69-72 (Parahippocampal)
# Let's define a robust set.
PFC_INDICES = list(range(0, 32)) # 0-indexed: 1-32
HIPPO_INDICES = list(range(64, 72)) # 0-indexed: 65-72

def load_connectivity_matrix(matrix_path):
    """Load a connectivity matrix from .npy file."""
    if not os.path.exists(matrix_path):
        raise FileNotFoundError(f"Matrix file not found: {matrix_path}")
    matrix = np.load(matrix_path)
    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError(f"Matrix must be square. Got shape {matrix.shape}")
    return matrix

def compute_global_efficiency(matrix):
    """Compute Global Efficiency of the graph."""
    # Create graph from matrix (undirected, weighted)
    # Threshold small values to avoid noise? Usually keep all for correlation.
    G = nx.from_numpy_array(matrix)
    try:
        return nx.global_efficiency(G)
    except nx.NetworkXError:
        return 0.0

def compute_local_efficiency(matrix):
    """Compute Local Efficiency of the graph."""
    G = nx.from_numpy_array(matrix)
    try:
        return nx.local_efficiency(G)
    except nx.NetworkXError:
        return 0.0

def compute_modularity(matrix):
    """Compute Modularity using Louvain method (via community detection)."""
    G = nx.from_numpy_array(matrix)
    try:
        # Use python-louvain if available, otherwise fallback or error
        try:
            import community
            partition = community.best_partition(G)
            # Calculate modularity
            mod = community.modularity(partition, G)
            return mod
        except ImportError:
            # Fallback: simple approximation or 0 if not available
            # But BCTPy or networkx community is preferred.
            # Since BCTPy is in requirements, we assume it's available.
            # If not, we try networkx algorithms.
            from networkx.algorithms.community import modularity
            from networkx.algorithms.community import greedy_modularity_communities
            communities = greedy_modularity_communities(G)
            return modularity(G, communities)
    except Exception as e:
        logger.warning(f"Modularity calculation failed: {e}. Returning 0.0")
        return 0.0

def compute_betweenness_centrality(matrix):
    """Compute Betweenness Centrality for all nodes."""
    G = nx.from_numpy_array(matrix)
    try:
        return nx.betweenness_centrality(G)
    except nx.NetworkXError:
        return {i: 0.0 for i in range(matrix.shape[0])}

def extract_regional_centrality(matrix, region_indices):
    """Extract mean centrality for a specific set of region indices."""
    centrality = compute_betweenness_centrality(matrix)
    if not centrality:
        return 0.0
    indices = [i for i in region_indices if i < len(centrality)]
    if not indices:
        return 0.0
    values = [centrality[i] for i in indices]
    return np.mean(values)

def extract_features_for_subject(matrix):
    """
    Extract all graph metrics for a single subject's matrix.
    Returns a dict of features.
    """
    try:
        global_eff = compute_global_efficiency(matrix)
        local_eff = compute_local_efficiency(matrix)
        mod = compute_modularity(matrix)
        
        pfc_cent = extract_regional_centrality(matrix, PFC_INDICES)
        hippo_cent = extract_regional_centrality(matrix, HIPPO_INDICES)
        
        return {
            'global_efficiency': global_eff,
            'local_efficiency': local_eff,
            'modularity': mod,
            'prefrontal_centrality': pfc_cent,
            'hippocampal_centrality': hippo_cent
        }
    except Exception as e:
        logger.error(f"Error extracting features: {e}")
        return None

def check_collinearity(X, threshold=0.8):
    """
    Check for collinearity (r > threshold).
    If found, apply PCA and return reduced data.
    Returns: (X_processed, used_columns, log_message)
    """
    n_features = X.shape[1]
    used_columns = [f'col_{i}' for i in range(n_features)] # Placeholder names
    
    # Compute correlation matrix
    if n_features < 2:
        return X, used_columns, "No collinearity check needed (< 2 features)."
    
    corr_matrix = np.corrcoef(X.T)
    
    # Check for high correlation
    high_corr_pairs = []
    for i in range(n_features):
        for j in range(i+1, n_features):
            if abs(corr_matrix[i, j]) > threshold:
                high_corr_pairs.append((i, j, corr_matrix[i, j]))
    
    if not high_corr_pairs:
        return X, used_columns, "No collinearity detected."
    
    log_msg = f"Collinearity detected ({len(high_corr_pairs)} pairs > {threshold}). Applying PCA.\n"
    for i, j, r in high_corr_pairs:
        log_msg += f"  Features {i} and {j}: r={r:.4f}\n"
    
    # Apply PCA
    from sklearn.decomposition import PCA
    # Keep enough components to explain 95% variance or all if n_features is small
    pca = PCA()
    X_reduced = pca.fit_transform(X)
    
    # Log variance explained
    log_msg += f"PCA components kept: {pca.n_components_}\n"
    log_msg += f"Variance explained: {np.sum(pca.explained_variance_ratio_):.4f}\n"
    
    # Return reduced X and new column names
    new_cols = [f'PC{i+1}' for i in range(X_reduced.shape[1])]
    return X_reduced, new_cols, log_msg

def run_graph_metrics_pipeline():
    """
    Main pipeline entry point for T022.
    Calls assemble_features logic.
    """
    from graph_metrics.assemble_features import assemble_features
    return assemble_features()

def main():
    try:
        output_path = run_graph_metrics_pipeline()
        logger.info(f"Pipeline complete. Output: {output_path}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
