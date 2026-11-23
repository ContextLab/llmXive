import os
import logging
import networkx as nx
import pandas as pd
from typing import Dict, Any
from pathlib import Path

from src.lib import config

logger = logging.getLogger(__name__)


def save_graph_to_parquet(graph: nx.Graph, output_path: str) -> None:
    """
    Save a NetworkX graph with node attributes to a Parquet file.

    This function converts the graph into a tabular format suitable for Parquet storage.
    It extracts node attributes (id, title, citation_count, primary_cluster, bridging_coefficient)
    and writes them to the specified output path.

    Args:
        graph: The NetworkX graph to save.
        output_path: The path where the Parquet file will be written.
    """
    if graph is None or len(graph.nodes()) == 0:
        logger.warning("Attempted to save an empty or None graph.")
        # Ensure the output file is created even if empty, or handle as error?
        # Based on task T016a, we expect columns. If empty, we might write an empty DF with schema.
        # However, for T016, we assume we are saving a processed graph.
        # Let's create an empty dataframe with expected columns if graph is empty.
        df = pd.DataFrame(columns=['id', 'title', 'citation_count', 'primary_cluster', 'bridging_coefficient'])
    else:
        nodes_data = []
        for node_id, data in graph.nodes(data=True):
            nodes_data.append({
                'id': node_id,
                'title': data.get('title', ''),
                'citation_count': data.get('citation_count', 0),
                'primary_cluster': data.get('primary_cluster', None),
                'bridging_coefficient': data.get('bridging_coefficient', 0.0)
            })
        df = pd.DataFrame(nodes_data)

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write to Parquet
    df.to_parquet(output_path, index=False)
    logger.info(f"Graph saved to {output_path} with {len(df)} nodes.")


def main():
    """
    Main entry point to run the graph saving pipeline.
    This function is intended to be called as a script.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Configuration
    # Assuming the graph is already processed and available in memory or loaded from a previous step.
    # For this script to be a standalone run-book command as per T016,
    # we need to either load it from a known intermediate location or rebuild it.
    # Based on T012/T013/T014 flow, the graph is built in ingest.py.
    # We will assume the graph is passed via a temporary file or we re-run the fetch logic.
    # However, to keep T016 focused on SAVING, we will assume the graph is loaded from
    # a standard intermediate location if it exists, or we simulate the load for the script to run.
    #
    # CRITICAL: To satisfy T016 (Save processed graph), this script must produce the file.
    # Since the full pipeline might be heavy, and T012 (ingest) builds the graph,
    # we will implement a minimal flow here to ensure the file is written.
    # In a real run-book, this would be chained after T012/T013/T014.
    # For the purpose of this task implementation, we will load the graph from
    # `data/raw/openalex_stream.parquet` if it exists (from T041), or fetch a sample.
    #
    # Let's implement a robust fetch/load logic to ensure the file is created.
    from src.services.ingest import fetch_and_build_subgraph
    from src.models.graph_utils import louvain_cluster, calc_bridging

    sample_size = 1000
    logger.info(f"Fetching and building subgraph with size {sample_size}...")
    
    try:
        graph = fetch_and_build_subgraph(sample_size=sample_size)
        
        if graph is None:
            logger.error("Failed to build subgraph. Exiting.")
            return

        logger.info(f"Graph built with {len(graph.nodes())} nodes and {len(graph.edges())} edges.")

        # Apply Clustering (T013)
        logger.info("Running Louvain clustering...")
        clusters = louvain_cluster(graph)
        
        # Apply Bridging Coefficient (T014)
        logger.info("Calculating bridging coefficients...")
        calc_bridging(graph, clusters)

        # Save to Parquet (T016)
        output_path = config.get_data_path() / "processed" / "subgraph_with_clusters.parquet"
        save_graph_to_parquet(graph, str(output_path))
        
        logger.info(f"Successfully saved graph to {output_path}")

    except Exception as e:
        logger.error(f"Error during graph processing and saving: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
