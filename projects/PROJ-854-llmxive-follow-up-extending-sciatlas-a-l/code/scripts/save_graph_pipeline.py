"""
Pipeline script to fetch, build, cluster, and save the graph.

This script orchestrates the full ingestion pipeline for User Story 1:
1. Fetch sample IDs from OpenAlex
2. Build subgraph with snowball sampling
3. Compute Louvain clusters and bridging coefficients
4. Save to parquet

Output: data/processed/subgraph_with_clusters.parquet
"""
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.ingest import fetch_and_build_subgraph, save_graph_to_parquet
from src.models.graph_utils import louvain_cluster, calc_bridging
from src.lib.config import ensure_directories, get_processed_data_path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the graph save pipeline."""
    try:
        logger.info("Starting graph ingestion and save pipeline")
        
        # Ensure directories exist
        ensure_directories()
        
        # Step 1: Fetch and build subgraph
        logger.info("Fetching and building subgraph...")
        G = fetch_and_build_subgraph(target_size=1000)
        
        if G.number_of_nodes() == 0:
            raise RuntimeError("Failed to build subgraph: no nodes collected")
        
        logger.info(f"Built subgraph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        
        # Step 2: Assign structural clusters (Louvain)
        logger.info("Running Louvain community detection...")
        clusters = louvain_cluster(G)
        
        # Step 3: Calculate bridging coefficients
        logger.info("Calculating bridging coefficients...")
        calc_bridging(G, clusters)
        
        # Step 4: Save to parquet
        logger.info("Saving graph to parquet...")
        output_path = save_graph_to_parquet(G, clusters)
        
        logger.info(f"Pipeline completed successfully. Output: {output_path}")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        logger.exception("Traceback:")
        return 1

if __name__ == "__main__":
    sys.exit(main())
