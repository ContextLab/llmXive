import logging
import sys
from pathlib import Path

from src.services.ingest import fetch_and_build_subgraph, save_graph_to_parquet
from src.models.graph_utils import louvain_cluster, calc_bridging
from src.lib import config


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """
    Main entry point for the save graph pipeline.
    Executes: Fetch -> Cluster -> Calculate Bridging -> Save
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    # Parameters
    sample_size = 1000
    logger.info(f"Starting pipeline with sample size: {sample_size}")

    try:
        # 1. Fetch and Build Subgraph (T012)
        logger.info("Step 1: Fetching and building subgraph...")
        graph = fetch_and_build_subgraph(sample_size=sample_size)

        if graph is None or len(graph.nodes()) == 0:
            logger.error("Graph is empty after fetching. Aborting.")
            sys.exit(1)

        logger.info(f"Graph loaded: {len(graph.nodes())} nodes, {len(graph.edges())} edges")

        # 2. Cluster Nodes (T013)
        logger.info("Step 2: Running Louvain clustering...")
        clusters = louvain_cluster(graph)
        logger.info(f"Clustering complete. {len(set(clusters.values()))} clusters found.")

        # 3. Calculate Bridging Coefficients (T014)
        logger.info("Step 3: Calculating bridging coefficients...")
        calc_bridging(graph, clusters)
        logger.info("Bridging coefficients calculated.")

        # 4. Save to Parquet (T016)
        logger.info("Step 4: Saving graph to Parquet...")
        output_path = config.get_data_path() / "processed" / "subgraph_with_clusters.parquet"
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert graph to dataframe and save
        nodes_data = []
        for node_id, data in graph.nodes(data=True):
            nodes_data.append({
                'id': node_id,
                'title': data.get('title', ''),
                'citation_count': data.get('citation_count', 0),
                'primary_cluster': data.get('primary_cluster'),
                'bridging_coefficient': data.get('bridging_coefficient', 0.0)
            })
        
        import pandas as pd
        df = pd.DataFrame(nodes_data)
        df.to_parquet(str(output_path), index=False)

        logger.info(f"Successfully saved graph to {output_path}")
        logger.info(f"Saved {len(df)} nodes.")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
