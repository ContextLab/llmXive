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
    # Assuming df has columns: cell_type, motif_id, q_value_adj
    pivot = df.pivot(index='cell_type', columns='motif_id', values='q_value_adj').fillna(0)
    from scipy.spatial.distance import pdist, squareform
    dist = squareform(pdist(pivot, metric='euclidean'))
    return pd.DataFrame(dist, index=pivot.index, columns=pivot.index)

def cluster_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Cluster the matrix using hierarchical clustering."""
    from scipy.cluster.hierarchy import linkage, leaves_list
    # Pivot
    pivot = df.pivot(index='cell_type', columns='motif_id', values='q_value_adj').fillna(0)
    # Linkage
    Z = linkage(pivot, method='average')
    # Get order
    order = leaves_list(Z)
    ordered_index = pivot.index[order]
    return pivot.reindex(ordered_index)

def generate_heatmap(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """Generate a heatmap of the enrichment matrix."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    path = output_path or DATA_PROCESSED_DIR / "heatmap.png"
    path.parent.mkdir(parents=True, exist_ok=True)

    clustered_df = cluster_matrix(df)

    plt.figure(figsize=(10, 8))
    sns.heatmap(clustered_df, cmap='viridis', annot=False, cbar=True)
    plt.title("Motif Enrichment Heatmap (q-values)")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()

    logger.info(f"Heatmap saved to {path}")
    return path

def main() -> None:
    """Entry point for CLI."""
    logging.basicConfig(level=logging.INFO)
    try:
        df = load_enrichment_matrix()
        generate_heatmap(df)
        print("Visualization complete.")
    except Exception as e:
        logger.error(f"Visualization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
