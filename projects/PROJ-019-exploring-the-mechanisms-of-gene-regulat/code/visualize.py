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
    import matplotlib
    # Use Agg backend to prevent GUI errors in headless environments
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import seaborn as sns

    path = output_path or DATA_PROCESSED_DIR / "heatmap.png"
    path.parent.mkdir(parents=True, exist_ok=True)

    clustered_df = cluster_matrix(df)

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
