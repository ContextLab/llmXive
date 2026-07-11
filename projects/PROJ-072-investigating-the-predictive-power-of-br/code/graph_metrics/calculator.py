import os
import sys
import logging
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import scipy.stats as stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CORRELATION_THRESHOLD = 0.8
PCA_VARIANCE_THRESHOLD = 0.95
DATA_PROCESSED_DIR = Path("data/processed")
DATA_METADATA_DIR = Path("data/metadata")

def load_connectivity_matrix(subject_id: str, data_dir: Path = DATA_PROCESSED_DIR) -> np.ndarray:
    """Load a connectivity matrix for a given subject."""
    matrix_path = data_dir / f"{subject_id}_matrix.npy"
    if not matrix_path.exists():
        raise FileNotFoundError(f"Matrix not found for subject {subject_id} at {matrix_path}")
    return np.load(matrix_path)

def compute_global_efficiency(matrix: np.ndarray) -> float:
    """Compute global efficiency of a graph."""
    # Ensure matrix is symmetric
    matrix = (matrix + matrix.T) / 2
    # Set diagonal to 0
    np.fill_diagonal(matrix, 0)
    
    G = nx.from_numpy_array(matrix)
    try:
        return nx.global_efficiency(G)
    except Exception as e:
        logger.warning(f"Could not compute global efficiency: {e}")
        return 0.0

def compute_local_efficiency(matrix: np.ndarray) -> float:
    """Compute local efficiency of a graph."""
    matrix = (matrix + matrix.T) / 2
    np.fill_diagonal(matrix, 0)
    
    G = nx.from_numpy_array(matrix)
    try:
        return nx.local_efficiency(G)
    except Exception as e:
        logger.warning(f"Could not compute local efficiency: {e}")
        return 0.0

def compute_modularity(matrix: np.ndarray) -> float:
    """Compute modularity using Louvain method."""
    matrix = (matrix + matrix.T) / 2
    np.fill_diagonal(matrix, 0)
    
    G = nx.from_numpy_array(matrix)
    try:
        # Use louvain_communities from networkx (available in newer versions)
        # or fallback to community detection if needed
        if hasattr(nx, 'community'):
            from networkx.algorithms import community
            communities = community.louvain_communities(G, seed=42)
            return community.modularity(G, communities)
        else:
            # Fallback: simple approximation or return 0
            logger.warning("Louvain community detection not available, returning 0.0")
            return 0.0
    except Exception as e:
        logger.warning(f"Could not compute modularity: {e}")
        return 0.0

def compute_betweenness_centrality(matrix: np.ndarray) -> Dict[int, float]:
    """Compute betweenness centrality for all nodes."""
    matrix = (matrix + matrix.T) / 2
    np.fill_diagonal(matrix, 0)
    
    G = nx.from_numpy_array(matrix)
    try:
        return nx.betweenness_centrality(G)
    except Exception as e:
        logger.warning(f"Could not compute betweenness centrality: {e}")
        return {i: 0.0 for i in range(matrix.shape[0])}

def extract_regional_centrality(matrix: np.ndarray, region_indices: List[int]) -> Dict[str, float]:
    """Extract centrality for specific regions (e.g., prefrontal, hippocampal)."""
    centrality = compute_betweenness_centrality(matrix)
    result = {}
    for idx in region_indices:
        if idx in centrality:
            result[f"node_{idx}"] = centrality[idx]
    return result

def extract_features_for_subject(subject_id: str, data_dir: Path = DATA_PROCESSED_DIR) -> Dict[str, Any]:
    """Extract all graph metrics for a single subject."""
    matrix = load_connectivity_matrix(subject_id, data_dir)
    
    features = {
        "subject_id": subject_id,
        "global_efficiency": compute_global_efficiency(matrix),
        "local_efficiency": compute_local_efficiency(matrix),
        "modularity": compute_modularity(matrix),
        "betweenness_centrality_mean": np.mean(list(compute_betweenness_centrality(matrix).values())),
        "betweenness_centrality_std": np.std(list(compute_betweenness_centrality(matrix).values())),
    }
    
    # Prefrontal and Hippocampal ROIs (example indices, adjust based on atlas)
    # Assuming AAL atlas: Prefrontal ~ 1-10, Hippocampal ~ 25-30 (adjust as needed)
    prefrontal_indices = list(range(0, 10))
    hippocampal_indices = list(range(24, 30))
    
    prefrontal_cent = extract_regional_centrality(matrix, prefrontal_indices)
    hippocampal_cent = extract_regional_centrality(matrix, hippocampal_indices)
    
    # Average centrality for these regions
    features["prefrontal_centrality"] = np.mean(list(prefrontal_cent.values())) if prefrontal_cent else 0.0
    features["hippocampal_centrality"] = np.mean(list(hippocampal_cent.values())) if hippocampal_cent else 0.0
    
    return features

def check_collinearity(features_df: pd.DataFrame, threshold: float = CORRELATION_THRESHOLD) -> Tuple[List[str], pd.DataFrame]:
    """
    Check for collinearity among features (Pearson r > threshold).
    Returns a list of features to drop and the reduced DataFrame.
    """
    numeric_cols = features_df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) < 2:
        return [], features_df
    
    corr_matrix = features_df[numeric_cols].corr().abs()
    
    # Select upper triangle of correlation matrix
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    
    # Find features with correlation greater than threshold
    to_drop = [column for column in upper.columns if any(upper[column] > threshold)]
    
    if to_drop:
        logger.warning(f"Collinearity detected. Dropping features: {to_drop}")
        # Drop the redundant features
        reduced_df = features_df.drop(columns=to_drop)
        return to_drop, reduced_df
    
    return [], features_df

def apply_pca(features_df: pd.DataFrame, variance_threshold: float = PCA_VARIANCE_THRESHOLD) -> Tuple[pd.DataFrame, Any]:
    """
    Apply PCA to reduce dimensionality if collinearity is found.
    Returns the reduced DataFrame and the PCA object.
    """
    from sklearn.decomposition import PCA
    
    numeric_cols = features_df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        return features_df, None
    
    X = features_df[numeric_cols].values
    
    pca = PCA(variance_threshold, random_state=42)
    X_pca = pca.fit_transform(X)
    
    # Create new DataFrame with PCA components
    pca_columns = [f"pca_component_{i+1}" for i in range(X_pca.shape[1])]
    pca_df = pd.DataFrame(X_pca, columns=pca_columns, index=features_df.index)
    
    # Keep non-numeric columns (like subject_id)
    non_numeric_cols = features_df.select_dtypes(exclude=[np.number]).columns.tolist()
    for col in non_numeric_cols:
        pca_df[col] = features_df[col]
    
    logger.info(f"PCA applied. Explained variance ratio: {pca.explained_variance_ratio_}")
    return pca_df, pca

def run_collinearity_check_and_reduction(features_df: pd.DataFrame, 
                                         log_path: Path = DATA_METADATA_DIR / "collinearity_log.txt",
                                         pca_output_path: Path = DATA_PROCESSED_DIR / "features_pca.csv") -> pd.DataFrame:
    """
    Main function to run collinearity check and apply PCA if needed.
    Returns the final features DataFrame.
    """
    DATA_METADATA_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting collinearity check...")
    
    # Check for collinearity
    dropped_features, reduced_df = check_collinearity(features_df)
    
    if dropped_features:
        # Log dropped features
        with open(log_path, 'w') as f:
            f.write("Collinearity Check Results\n")
            f.write(f"Threshold: {CORRELATION_THRESHOLD}\n")
            f.write(f"Dropped features: {dropped_features}\n")
            f.write("Reason: Pearson correlation > 0.8\n")
        logger.info(f"Dropped features logged to {log_path}")
        
        # Apply PCA to the reduced features (if still collinear or just to reduce dimensionality)
        # We apply PCA if we still have many features or if the user prefers PCA over dropping
        # Here, we apply PCA to the reduced_df to further compress if needed
        final_df, pca_model = apply_pca(reduced_df)
        
        if pca_model is not None:
            final_df.to_csv(pca_output_path, index=False)
            logger.info(f"PCA-reduced features saved to {pca_output_path}")
            return final_df
        else:
            reduced_df.to_csv(pca_output_path.replace('_pca.csv', '_dropped.csv'), index=False)
            return reduced_df
    else:
        logger.info("No collinearity detected above threshold. No reduction needed.")
        # Save the original features as is, or we could still apply PCA if desired
        # For now, we return the original features
        return features_df

def extract_features_pipeline(subject_ids: List[str], 
                              data_dir: Path = DATA_PROCESSED_DIR,
                              output_path: Path = DATA_PROCESSED_DIR / "features.csv") -> pd.DataFrame:
    """
    Extract features for all subjects and handle collinearity.
    """
    features_list = []
    for sid in subject_ids:
        try:
            feats = extract_features_for_subject(sid, data_dir)
            features_list.append(feats)
        except Exception as e:
            logger.error(f"Failed to extract features for {sid}: {e}")
    
    if not features_list:
        raise ValueError("No features extracted for any subject.")
    
    df = pd.DataFrame(features_list)
    df.to_csv(output_path, index=False)
    logger.info(f"Features saved to {output_path}")
    
    # Run collinearity check and reduction
    final_df = run_collinearity_check_and_reduction(df)
    return final_df

def run_graph_metrics_pipeline(subject_ids: List[str], 
                               data_dir: Path = DATA_PROCESSED_DIR) -> pd.DataFrame:
    """
    Main pipeline to run graph metrics and handle collinearity.
    """
    return extract_features_pipeline(subject_ids, data_dir)

def main():
    """Main entry point for testing or CLI."""
    # Example usage
    subject_ids = ["sub-001", "sub-002"]  # Replace with real subject IDs
    try:
        final_features = run_graph_metrics_pipeline(subject_ids)
        print(final_features.head())
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
