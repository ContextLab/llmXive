"""
Script to save the processed graph with clusters and bridging coefficients to Parquet.
Implements Task T016.
"""
import logging
import sys
from pathlib import Path

# Import from existing API surface
from src.services.ingest import fetch_and_build_subgraph, save_graph_to_parquet
from src.models.graph_utils import louvain_cluster, calc_bridging
from src.lib.config import ensure_directories, get_processed_data_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the graph saving pipeline.
    1. Fetch and build the subgraph (ingestion).
    2. Run Louvain clustering.
    3. Calculate bridging coefficients.
    4. Save to Parquet.
    """
    logger.info("Starting graph saving pipeline (T016)...")

    # Ensure output directories exist
    ensure_directories()
    output_path = get_processed_data_path("subgraph_with_clusters.parquet")
    logger.info(f"Output path: {output_path}")

    try:
        # Step 1: Fetch and build subgraph
        # This function handles streaming ingestion and sampling as per T040/T012a/T012
        logger.info("Fetching and building subgraph...")
        G = fetch_and_build_subgraph()
        
        if G is None or G.number_of_nodes() == 0:
            logger.error("Failed to build subgraph. Graph is empty or None.")
            sys.exit(1)
        
        logger.info(f"Subgraph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Step 2: Run Louvain clustering (T013)
        logger.info("Running Louvain community detection...")
        clusters = louvain_cluster(G)
        logger.info(f"Found {len(set(clusters.values()))} clusters")

        # Step 3: Calculate bridging coefficients (T014)
        logger.info("Calculating bridging coefficients...")
        bridging_coeffs = calc_bridging(G, clusters)
        logger.info(f"Calculated bridging coefficients for {len(bridging_coeffs)} nodes")

        # Step 4: Save to Parquet (T016)
        logger.info(f"Saving graph to {output_path}...")
        save_graph_to_parquet(G, clusters, bridging_coeffs, output_path)
        
        logger.info("Graph saved successfully.")
        logger.info(f"Artifact integrity will be verified by the global hash mechanism in Phase 5.")
        
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())