import os
import logging
import networkx as nx
import pandas as pd
from typing import Dict, Any
from src.services.ingest import fetch_sample_ids, fetch_and_build_subgraph
from src.lib import config

logger = logging.getLogger(__name__)

def save_graph_to_parquet(
    G: nx.Graph,
    clusters: Dict[Any, int],
    bridging_coeffs: Dict[Any, float],
    output_path: str
) -> None:
    """
    Convert the NetworkX graph with cluster and bridging data into a pandas DataFrame
    and save it as a Parquet file.

    Args:
        G: The networkx graph object.
        clusters: Dictionary mapping node_id -> primary_cluster_id.
        bridging_coeffs: Dictionary mapping node_id -> bridging_coefficient.
        output_path: File path for the output parquet file.
    """
    logger.info(f"Converting graph with {G.number_of_nodes()} nodes to DataFrame...")

    node_data = []
    for node_id, data in G.nodes(data=True):
        node_data.append({
            'id': node_id,
            'title': data.get('title', ''),
            'citation_count': data.get('citation_count', 0),
            'primary_cluster': clusters.get(node_id, -1),
            'topic_cluster': data.get('topic_cluster', -1),
            'bridging_coefficient': bridging_coeffs.get(node_id, 0.0)
        })

    df = pd.DataFrame(node_data)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    logger.info(f"Saving processed graph to {output_path}...")
    df.to_parquet(output_path, index=False)
    logger.info(f"Successfully saved {len(df)} rows to {output_path}")

def main() -> None:
    """
    Main entry point to fetch data, compute clusters/coefficients, and save the result.
    This function orchestrates the full pipeline for T016.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # 1. Fetch sample IDs (degree-stratified)
        logger.info("Fetching sample IDs from OpenAlex...")
        sample_ids = fetch_sample_ids()
        if not sample_ids:
            logger.error("No sample IDs fetched. Aborting.")
            return

        # 2. Build the subgraph with node attributes
        logger.info("Building subgraph from OpenAlex data...")
        G = fetch_and_build_subgraph(sample_ids)

        if G.number_of_nodes() == 0:
            logger.error("Graph is empty. Aborting.")
            return

        # 3. Compute Clusters (Louvain)
        logger.info("Running Louvain clustering...")
        from src.models.graph_utils import louvain_cluster
        clusters = louvain_cluster(G)

        # 4. Compute Bridging Coefficients
        logger.info("Calculating bridging coefficients...")
        from src.models.graph_utils import calc_bridging
        bridging_coeffs = calc_bridging(G, clusters)

        # 5. Save to Parquet
        output_path = config.DATA_PROCESSED_PATH / "subgraph_with_clusters.parquet"
        save_graph_to_parquet(G, clusters, bridging_coeffs, str(output_path))

        logger.info("Pipeline completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        raise
