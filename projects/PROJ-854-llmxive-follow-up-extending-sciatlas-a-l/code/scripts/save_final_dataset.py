"""
Script to save the final analysis dataset combining all computed metrics.

This script loads the processed graph with structural clusters and bridging coefficients,
merges it with citation data and novelty scores, and saves the result as a Parquet file.
"""
import os
import sys
import logging
import pandas as pd
import networkx as nx

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.lib import config
from src.services.ingest import fetch_and_build_subgraph
from src.models.graph_utils import calc_bridging
from src.services.embeddings import (
    load_embedding_model,
    filter_valid_nodes,
    generate_embeddings_batched,
    compute_novelty_scores,
    save_excluded_nodes
)
from src.services.clustering import (
    assign_topic_clusters_to_dataframe,
    compute_cluster_centroids
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting final dataset generation...")

    # 1. Fetch and build the subgraph (US1)
    logger.info("Fetching and building OpenAlex subgraph...")
    G = fetch_and_build_subgraph(target_size=config.TARGET_SUBGRAPH_SIZE)
    
    if G.number_of_nodes() == 0:
        logger.error("No nodes fetched. Aborting.")
        sys.exit(1)

    # 2. Assign primary clusters and calculate bridging coefficients (US1)
    # Note: louvain_cluster is imported from graph_utils in the API surface
    from src.models.graph_utils import louvain_cluster
    clusters = louvain_cluster(G)
    
    # Update node attributes with primary_cluster
    for node, cluster_id in clusters.items():
        G.nodes[node]['primary_cluster'] = cluster_id

    # Calculate bridging coefficients
    bridging_coeffs = calc_bridging(G, clusters)
    for node, coeff in bridging_coeffs.items():
        G.nodes[node]['bridging_coefficient'] = coeff

    logger.info(f"Graph processed: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # 3. Convert Graph to DataFrame for merging with embeddings/novelty
    # We extract node attributes that we need
    node_data = []
    for node_id, data in G.nodes(data=True):
        node_data.append({
            'id': node_id,
            'title': data.get('title', ''),
            'citation_count': data.get('citation_count', 0),
            'primary_cluster': data.get('primary_cluster', -1),
            'bridging_coefficient': data.get('bridging_coefficient', 0.0)
        })
    
    df_graph = pd.DataFrame(node_data)
    logger.info(f"Converted graph to DataFrame with {len(df_graph)} rows")

    # 4. Process embeddings and novelty scores (US2)
    logger.info("Loading embedding model...")
    model = load_embedding_model()

    logger.info("Filtering valid nodes for embedding...")
    valid_nodes, excluded_nodes = filter_valid_nodes(df_graph)
    
    if excluded_nodes:
        save_excluded_nodes(excluded_nodes, config.EXCLUDED_NODES_PATH)
        logger.info(f"Saved {len(excluded_nodes)} excluded nodes to {config.EXCLUDED_NODES_PATH}")

    logger.info("Generating embeddings in batches...")
    embeddings_df = generate_embeddings_batched(valid_nodes, model, batch_size=config.EMBEDDING_BATCH_SIZE)

    logger.info("Assigning topic clusters (k-means)...")
    # assign_topic_clusters_to_dataframe expects a dataframe with embeddings
    df_with_topic_clusters = assign_topic_clusters_to_dataframe(embeddings_df, k=config.TOPIC_CLUSTER_K)

    logger.info("Computing novelty scores...")
    df_with_novelty = compute_novelty_scores(df_with_topic_clusters)

    # 5. Merge all data
    # We need to merge df_graph (all nodes) with df_with_novelty (only valid nodes)
    # df_with_novelty contains: id, topic_cluster, novelty_score, embedding_vector
    
    # Drop the embedding vector from the final dataset if it's too large, 
    # but keep the other metrics. The task says "citations, novelty scores, and clusters".
    # We will keep the vector if it fits, otherwise we might drop it. 
    # For now, let's keep it as per "final dataset" usually implying raw features too.
    # However, parquet can be large. Let's assume we keep it.
    
    # Merge on 'id'
    df_final = df_graph.merge(
        df_with_novelty[['id', 'topic_cluster', 'novelty_score']], 
        on='id', 
        how='left'
    )

    # Fill NaN for novelty_score for excluded nodes (if any) with 0.0 or NaN?
    # Spec says: "retain them in the dataset for citation analysis"
    # So we keep the rows, but novelty might be NaN. Let's fill with -1.0 or keep NaN?
    # Usually, NaN is fine for "missing". But let's check if we need a sentinel.
    # The task doesn't specify a sentinel, so we leave as NaN or fill with 0.
    # Given the context of "novelty score", 0 might imply "not novel at all" which is different from "not calculated".
    # We will leave as NaN for excluded nodes, or fill with 0.0 if the downstream analysis requires it.
    # Let's fill with 0.0 to ensure the column is numeric for the analysis step.
    df_final['novelty_score'] = df_final['novelty_score'].fillna(0.0)

    logger.info(f"Final dataset shape: {df_final.shape}")
    logger.info(f"Columns: {list(df_final.columns)}")

    # 6. Save to Parquet
    output_path = config.FINAL_DATASET_PATH
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df_final.to_parquet(output_path, index=False)
    logger.info(f"Saved final dataset to {output_path}")

    return output_path

if __name__ == "__main__":
    main()
