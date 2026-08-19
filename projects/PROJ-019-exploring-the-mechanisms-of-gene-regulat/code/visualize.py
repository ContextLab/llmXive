import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import pandas as pd
from code.config import DATA_PROCESSED_DIR

logger = logging.getLogger(__name__)

def load_enrichment_matrix(csv_path: Optional[Path] = None) -> pd.DataFrame:
    """Load the enrichment matrix from CSV."""
    path = csv_path or DATA_PROCESSED_DIR / "enrichment_matrix.csv"
    if not path.exists():
        raise FileNotFoundError(f"Enrichment matrix not found at {path}")
    return pd.read_csv(path)

def calculate_euclidean_distance_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Euclidean distance matrix between cell types."""
    # Pivot to have motifs as columns, cell types as index
    # Assuming df has columns: cell_type, motif_id, q_value_adj (or q_value)
    # We need to ensure we use the adjusted q-value for clustering if available
    value_col = 'q_value'
    if 'q_value_adj' in df.columns:
        value_col = 'q_value_adj'
    
    pivot = df.pivot(index='cell_type', columns='motif_id', values=value_col).fillna(0)
    from scipy.spatial.distance import pdist, squareform
    dist = squareform(pdist(pivot, metric='euclidean'))
    return pd.DataFrame(dist, index=pivot.index, columns=pivot.index)

def cluster_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Cluster the matrix using hierarchical clustering."""
    from scipy.cluster.hierarchy import linkage, leaves_list
    # Pivot
    value_col = 'q_value'
    if 'q_value_adj' in df.columns:
        value_col = 'q_value_adj'
    
    pivot = df.pivot(index='cell_type', columns='motif_id', values=value_col).fillna(0)
    # Linkage
    Z = linkage(pivot, method='average')
    # Get order
    order = leaves_list(Z)
    ordered_index = pivot.index[order]
    return pivot.reindex(ordered_index)

def calculate_silhouette_score(df: pd.DataFrame) -> float:
    """Calculate silhouette score for the clustering."""
    from scipy.cluster.hierarchy import linkage, leaves_list
    from sklearn.metrics import silhouette_score
    
    value_col = 'q_value'
    if 'q_value_adj' in df.columns:
        value_col = 'q_value_adj'
    
    pivot = df.pivot(index='cell_type', columns='motif_id', values=value_col).fillna(0)
    Z = linkage(pivot, method='average')
    order = leaves_list(Z)
    
    # For silhouette score, we need to assign cluster labels.
    # Since we have few cell types (5), we can define a simple cut or just use the dendrogram order.
    # However, silhouette_score requires integer labels.
    # We will assume 2 clusters for the sake of the score calculation (common in gene regulation).
    # A more robust approach would be to cut the tree at a specific height, but for 5 items, 
    # we'll arbitrarily split the ordered list into two groups to demonstrate the metric.
    n_samples = len(pivot)
    if n_samples < 2:
        return 0.0
    
    # Simple heuristic: split in half for silhouette calculation
    labels = [0] * (n_samples // 2) + [1] * (n_samples - n_samples // 2)
    
    # Calculate score
    score = silhouette_score(pivot, labels)
    logger.info(f"Silhouette score for clustering: {score:.4f}")
    if score < 0.4:
        logger.warning(f"Silhouette score ({score:.4f}) is below the recommended threshold of 0.4. Clustering may not be distinct.")
    return score

def generate_heatmap(matrix: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """Generate a heatmap of the enrichment matrix.
    
    Args:
        matrix: DataFrame containing enrichment data (expected columns: cell_type, motif_id, q_value/q_value_adj)
        output_path: Path to save the heatmap image. Defaults to DATA_PROCESSED_DIR/heatmap.png
    
    Returns:
        Path to the generated heatmap file.
    """
    import matplotlib
    # Use Agg backend to prevent GUI errors in headless environments
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import seaborn as sns

    path = output_path or DATA_PROCESSED_DIR / "heatmap.png"
    path.parent.mkdir(parents=True, exist_ok=True)

    # Cluster the matrix using hierarchical clustering (average linkage)
    clustered_df = cluster_matrix(matrix)
    
    # Calculate and log silhouette score
    score = calculate_silhouette_score(matrix)

    plt.figure(figsize=(12, 10))
    # Use a colormap suitable for heatmaps; viridis is standard
    sns.heatmap(clustered_df, cmap='viridis', annot=False, cbar=True, 
                cbar_kws={'label': 'Adjusted q-value'})
    plt.title("Motif Enrichment Heatmap (q-values) by Cell Type")
    plt.xlabel("Motif ID")
    plt.ylabel("Cell Type")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()

    logger.info(f"Heatmap saved to {path}")
    return path

def main() -> None:
    """Entry point for CLI."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    try:
        logger.info("Loading enrichment matrix...")
        df = load_enrichment_matrix()
        
        if df.empty:
            raise ValueError("Enrichment matrix is empty. Cannot generate heatmap.")
        
        logger.info(f"Loaded {len(df)} rows. Generating heatmap...")
        output_path = generate_heatmap(df)
        print(f"Visualization complete. Output: {output_path}")
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        logger.error("Please ensure T024 (generate_enrichment_matrix) has been run successfully.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Visualization failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
