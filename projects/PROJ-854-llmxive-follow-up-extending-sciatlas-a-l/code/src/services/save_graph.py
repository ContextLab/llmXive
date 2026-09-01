import os
import logging
import networkx as nx
import pandas as pd
from typing import Dict, Any
from pathlib import Path
from src.services.ingest import fetch_sample_ids, fetch_and_build_subgraph
from src.models.graph_utils import louvain_cluster, calc_bridging
from src.lib.config import DATA_PATH

logger = logging.getLogger(__name__)

def save_graph_to_parquet(graph: nx.Graph, output_path: str) -> None:
    """
    Convert a NetworkX graph with node attributes to a Pandas DataFrame
    and save it as a Parquet file.

    Args:
        graph: The NetworkX graph containing node attributes (id, title, citation_count,
               embedding_vector, primary_cluster, topic_cluster, bridging_coefficient).
        output_path: The full path where the Parquet file will be saved.
    """
    logger.info(f"Converting graph with {graph.number_of_nodes()} nodes to DataFrame...")

    # Extract nodes and their attributes
    nodes_data = []
    for node_id, attrs in graph.nodes(data=True):
        node_record = {
            'id': node_id,
            'title': attrs.get('title', ''),
            'citation_count': attrs.get('citation_count', 0),
            'embedding_vector': attrs.get('embedding_vector', None),
            'primary_cluster': attrs.get('primary_cluster', -1),
            'topic_cluster': attrs.get('topic_cluster', -1),
            'bridging_coefficient': attrs.get('bridging_coefficient', 0.0),
        }
        nodes_data.append(node_record)

    df = pd.DataFrame(nodes_data)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Saving DataFrame to {output_path}...")
    df.to_parquet(output_path, index=False)
    logger.info(f"Successfully saved graph data to {output_path}")

def main() -> None:
    """
    Main entry point for the graph saving pipeline.
    Fetches a sample subgraph, computes clusters and bridging coefficients,
    and saves the result to data/processed/subgraph_with_clusters.parquet.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting graph saving pipeline...")

    # 1. Fetch sample IDs
    sample_ids = fetch_sample_ids(target_size=500)
    if not sample_ids:
        logger.error("No sample IDs retrieved. Exiting.")
        return

    logger.info(f"Retrieved {len(sample_ids)} sample IDs.")

    # 2. Build the subgraph
    graph = fetch_and_build_subgraph(sample_ids)
    if graph is None or graph.number_of_nodes() == 0:
        logger.error("Failed to build subgraph or graph is empty. Exiting.")
        return

    logger.info(f"Built subgraph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.")

    # 3. Compute Louvain clusters (primary_cluster)
    logger.info("Computing Louvain clusters...")
    clusters = louvain_cluster(graph)
    for node_id, cluster_id in clusters.items():
        graph.nodes[node_id]['primary_cluster'] = cluster_id
    logger.info(f"Assigned primary clusters to {len(clusters)} nodes.")

    # 4. Compute bridging coefficients
    logger.info("Computing bridging coefficients...")
    bridging_coeffs = calc_bridging(graph, clusters)
    for node_id, coeff in bridging_coeffs.items():
        graph.nodes[node_id]['bridging_coefficient'] = coeff
    logger.info(f"Computed bridging coefficients for {len(bridging_coeffs)} nodes.")

    # Define output path
    output_path = str(Path(DATA_PATH) / "processed" / "subgraph_with_clusters.parquet")

    # 5. Save to Parquet
    save_graph_to_parquet(graph, output_path)

    logger.info("Graph saving pipeline completed successfully.")

if __name__ == "__main__":
    main()
