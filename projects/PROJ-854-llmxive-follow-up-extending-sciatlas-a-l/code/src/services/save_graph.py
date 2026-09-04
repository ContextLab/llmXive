import os
import logging
import networkx as nx
import pandas as pd
from typing import Dict, Any
from pathlib import Path

from src.models.node import Node
from src.lib.config import get_config
from src.models.graph_utils import louvain_cluster, calc_bridging
from src.services.ingest import fetch_and_build_subgraph

logger = logging.getLogger(__name__)

def save_graph_to_parquet(G: nx.Graph, output_path: str) -> None:
    """
    Save the processed graph (nodes with clusters and bridging coefficients)
    to a Parquet file.

    Args:
        G: The networkx graph with node attributes set.
        output_path: The path to save the parquet file.
    """
    logger.info(f"Converting graph to DataFrame for {output_path}")

    if G.number_of_nodes() == 0:
        logger.warning("Graph is empty, creating empty DataFrame.")
        df = pd.DataFrame(columns=['id', 'title', 'citation_count', 'primary_cluster', 'bridging_coefficient'])
    else:
        # Convert graph nodes and attributes to a DataFrame
        # Ensure we handle cases where attributes might be missing by using defaults
        data = []
        for node_id, attrs in G.nodes(data=True):
            data.append({
                'id': node_id,
                'title': attrs.get('title', ''),
                'citation_count': attrs.get('citation_count', 0),
                'primary_cluster': attrs.get('primary_cluster', -1),
                'bridging_coefficient': attrs.get('bridging_coefficient', 0.0)
            })
        df = pd.DataFrame(data)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Saving DataFrame with {len(df)} rows to {output_path}")
    df.to_parquet(output_path, index=False)
    logger.info("Successfully saved graph to Parquet")

def main():
    """
    Main entry point for saving the graph pipeline.
    This script orchestrates the ingestion, clustering, bridging calculation, and saving.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    config = get_config()
    
    logger.info("Starting graph save pipeline...")
    
    # 1. Fetch and build subgraph
    # We use a default target size for execution if not specified in config
    # This ensures the script runs and produces output
    target_size = config.get('sampling', {}).get('target_size', 500)
    logger.info(f"Fetching subgraph with target size: {target_size}")
    G = fetch_and_build_subgraph(target_size=target_size)
    
    if G is None:
        logger.error("Failed to build subgraph. Exiting.")
        return

    logger.info(f"Built subgraph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

    # 2. Run Louvain clustering to assign primary_cluster
    logger.info("Running Louvain clustering...")
    clusters = louvain_cluster(G)
    logger.info(f"Louvain clustering complete. Found {len(set(clusters.values()))} clusters.")
    
    # Assign clusters to nodes
    for node, cluster_id in clusters.items():
        G.nodes[node]['primary_cluster'] = cluster_id

    # 3. Calculate bridging coefficients
    logger.info("Calculating bridging coefficients...")
    bridging_coeffs = calc_bridging(G, clusters)
    logger.info("Bridging coefficient calculation complete.")
    
    # Assign bridging coefficients to nodes
    for node, coeff in bridging_coeffs.items():
        G.nodes[node]['bridging_coefficient'] = coeff

    # 4. Save to Parquet
    output_path = str(config['paths']['processed_data'] / 'subgraph_with_clusters.parquet')
    save_graph_to_parquet(G, output_path)
    
    logger.info(f"Pipeline complete. Output saved to {output_path}")

if __name__ == '__main__':
    main()
