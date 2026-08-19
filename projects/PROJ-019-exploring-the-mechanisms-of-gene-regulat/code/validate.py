import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd
import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.metrics import silhouette_score

from code.config import DATA_PROCESSED_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_enrichment_results(filepath: Optional[Path] = None) -> pd.DataFrame:
    """Load the enrichment matrix from the processed directory."""
    if filepath is None:
        filepath = DATA_PROCESSED_DIR / "enrichment_matrix.csv"
    
    if not filepath.exists():
        raise FileNotFoundError(f"Enrichment matrix not found at {filepath}")
    
    logger.info(f"Loading enrichment results from {filepath}")
    df = pd.read_csv(filepath)
    return df

def get_top_motifs_per_cell_type(df: pd.DataFrame, q_threshold: float = 0.05) -> Dict[str, List[Dict[str, Any]]]:
    """Filter and group top enriched motifs by cell type."""
    if 'q_value' not in df.columns or 'cell_type' not in df.columns or 'motif_id' not in df.columns:
        raise ValueError("DataFrame must contain 'q_value', 'cell_type', and 'motif_id' columns")
    
    filtered = df[df['q_value'] < q_threshold]
    grouped = filtered.groupby('cell_type')
    
    result = {}
    for cell_type, group in grouped:
        # Sort by q_value ascending (most significant first)
        sorted_group = group.sort_values('q_value')
        result[cell_type] = sorted_group[['motif_id', 'q_value']].to_dict('records')
    
    return result

def calculate_silhouette_score_from_heatmap_data(df: pd.DataFrame) -> float:
    """
    Compute the silhouette score for the clustering of cell types based on motif enrichment.
    
    This function:
    1. Pivots the enrichment matrix to have cell types as rows and motifs as columns.
    2. Computes Euclidean distances between cell types.
    3. Performs hierarchical clustering (average linkage) to assign cluster labels.
    4. Calculates the silhouette score.
    
    Args:
        df: The enrichment DataFrame with columns: motif_id, cell_type, p_value, q_value.
    
    Returns:
        float: The silhouette score.
    """
    logger.info("Calculating silhouette score from enrichment matrix...")
    
    # Pivot to get matrix: Rows = Cell Types, Columns = Motifs, Values = q_value (or p_value)
    # We use q_value for clustering as it represents the adjusted significance
    try:
        pivot_df = df.pivot_table(index='cell_type', columns='motif_id', values='q_value', aggfunc='mean')
    except ValueError as e:
        logger.error(f"Failed to pivot data: {e}")
        raise
    
    # Ensure we have numeric data
    pivot_df = pivot_df.fillna(0)
    
    if pivot_df.shape[0] < 2:
        logger.warning("Not enough cell types to calculate silhouette score (need >= 2).")
        return -1.0
    
    # Compute distance matrix (Euclidean)
    # Note: silhouette_score expects data points (rows) and computes distance internally,
    # but we need labels. We will generate labels via linkage.
    X = pivot_df.values
    
    # Hierarchical clustering to get labels
    # We use 'average' linkage as per spec requirement for T028
    dist_matrix = squareform(pdist(X, metric='euclidean'))
    
    # Linkage matrix
    linkage_matrix = linkage(dist_matrix, method='average')
    
    # Determine number of clusters. 
    # Since we have 5 cell types, we might expect them to cluster into 2-3 groups.
    # We'll use a heuristic or fixed number if known. For silhouette score, 
    # we need at least 2 clusters. Let's assume 2 clusters for the score calculation
    # if the data naturally separates, or we can try to find optimal k.
    # However, to be deterministic and simple for this step, we'll try to split into 2 clusters
    # if we have > 1 point, or use a dynamic approach if possible.
    # Given the small sample size (5 cell types), let's try to find the best k in [2, 5-1]
    # But silhouette score requires labels. Let's assume 2 clusters for now as a baseline
    # or use the dendrogram cut.
    
    # A common approach when k is unknown is to try a range, but for a single metric return:
    # Let's assume the clustering structure suggests 2 main groups for gene regulation (e.g., embryonic vs somatic)
    # or simply cut at a height that gives 2 clusters.
    num_clusters = min(2, len(X)) # Ensure at least 2 if possible, but max 2 for small N? 
    # Actually, silhouette score is most meaningful with > 2 clusters, but 2 is the minimum.
    # Let's try to cut to 2 clusters if we have enough points.
    
    if len(X) < 2:
        return -1.0
    
    # We will cut the tree to form 2 clusters.
    # If the data is very uniform, this might be arbitrary, but it's a standard baseline.
    labels = fcluster(linkage_matrix, t=2, criterion='maxclust')
    
    # Calculate silhouette score
    # Labels must be 0-indexed or 1-indexed, fcluster returns 1-indexed.
    # silhouette_score handles this fine.
    score = silhouette_score(X, labels, metric='euclidean')
    
    logger.info(f"Silhouette score calculated: {score:.4f}")
    return score

def validate_motifs(df: pd.DataFrame, top_motifs: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Validate motifs by checking overlap with ChIP-seq data (placeholder for T030 logic).
    Returns a summary of validation stats.
    """
    logger.info("Validating motifs against ChIP-seq data...")
    # This function is a placeholder for the actual ChIP-seq overlap logic
    # which will be implemented in T030.
    # For T031, we just ensure the function signature exists and logs.
    return {
        "status": "pending",
        "message": "ChIP-seq overlap calculation pending T030 implementation"
    }

def generate_top_motifs_summary(df: pd.DataFrame, q_threshold: float = 0.05) -> Dict[str, Any]:
    """Generate a summary of top motifs per cell type."""
    top_motifs = get_top_motifs_per_cell_type(df, q_threshold)
    return top_motifs

def main():
    """
    Main entry point for T031: Compute silhouette score from heatmap data.
    This script reads the enrichment matrix, calculates the silhouette score,
    and logs the result. It does NOT exit with error code 1 if score < 0.4.
    """
    logger.info("Starting T031: Silhouette Score Calculation")
    
    try:
        # Load data
        df = load_enrichment_results()
        
        # Calculate silhouette score
        score = calculate_silhouette_score_from_heatmap_data(df)
        
        # Log the result
        if score < 0.4:
            logger.warning(f"Silhouette score ({score:.4f}) is below the threshold of 0.4. Clustering quality may be low.")
        else:
            logger.info(f"Silhouette score ({score:.4f}) meets the threshold of 0.4.")
        
        # Optional: Save score to a small JSON file for downstream tasks (T032)
        # The task description says "log the result", but T032 needs the value.
        # We will save it to data/processed/silhouette_score.json to be consumed by main.py
        output_path = DATA_PROCESSED_DIR / "silhouette_score.json"
        with open(output_path, 'w') as f:
            json.dump({"silhouette_score": round(score, 2)}, f)
        logger.info(f"Silhouette score saved to {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during silhouette score calculation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()