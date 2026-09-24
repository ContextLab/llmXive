import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.embeddings import (
    load_embedding_model,
    generate_embeddings_for_dataset,
    assign_topic_clusters_to_dataframe,
    compute_cluster_centroids_from_dataframe,
    compute_novelty_scores,
    get_cluster_statistics
)
from src.lib.config import get_processed_data_path, get_artifacts_path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Running Novelty Calculation Pipeline")
    
    # Paths
    input_path = get_processed_data_path() / "subgraph_with_clusters.parquet"
    output_path = get_processed_data_path() / "final_analysis_dataset.parquet"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Load data
    logger.info(f"Loading data from {input_path}")
    df = pd.read_parquet(input_path)
    
    # Validate required columns
    required_cols = ['id', 'title', 'topic_cluster'] # topic_cluster should be from T021
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        # If topic_cluster is missing, we need to generate it first
        logger.warning(f"Missing columns: {missing_cols}. Will compute embeddings and clusters.")
        if 'title' not in df.columns:
            logger.error("Cannot proceed without 'title' column.")
            sys.exit(1)
    
    # Load Model
    model = load_embedding_model("all-MiniLM-L6-v2")
    
    # Generate Embeddings
    logger.info("Generating embeddings...")
    embeddings = generate_embeddings_for_dataset(df, model, title_col='title', batch_size=64)
    
    if len(embeddings) == 0:
        logger.warning("No embeddings generated. Exiting.")
        sys.exit(0)
    
    # Ensure embeddings align with dataframe (filter_valid_nodes might have dropped rows)
    # Note: generate_embeddings_for_dataset returns embeddings for valid rows only.
    # We need to handle the alignment. 
    # Re-implementing the logic here to ensure alignment with the returned embeddings
    
    from src.services.embeddings import filter_valid_nodes, process_nodes_for_embeddings, generate_embeddings_batched
    
    valid_df, excluded = filter_valid_nodes(df, 'title')
    if excluded:
        excluded_path = get_processed_data_path() / "excluded_nodes.json"
        import json
        os.makedirs(excluded_path.parent, exist_ok=True)
        with open(excluded_path, 'w') as f:
            json.dump(excluded, f, indent=2)
        logger.info(f"Saved {len(excluded)} excluded nodes.")
    
    if valid_df.empty:
        logger.error("No valid nodes remaining after filtering.")
        sys.exit(1)
    
    texts = process_nodes_for_embeddings(valid_df, 'title')
    embeddings = generate_embeddings_batched(model, texts, batch_size=64)
    
    # Assign Topic Clusters (K-Means) if not present or re-compute
    # The task T021 implies this is done. If 'topic_cluster' is missing, do it now.
    if 'topic_cluster' not in valid_df.columns:
        logger.info("Assigning topic clusters via K-Means...")
        valid_df = assign_topic_clusters_to_dataframe(valid_df, embeddings, k=100)
    else:
        # If present, ensure it matches the embeddings (assume alignment is correct from previous step)
        # If the previous step T021 didn't filter nulls, we might have misalignment.
        # For safety, we re-assign based on the embeddings we just generated.
        # However, to respect T021's output, we should check if we need to re-run T021 logic.
        # Given the pipeline flow, we assume T021 produced the dataframe.
        # But since we are re-generating embeddings here, we should re-cluster to be consistent.
        # OR, we assume T021's clusters are based on these embeddings.
        # Let's assume we need to re-cluster to ensure consistency with the embeddings we just computed.
        # Actually, T021 is a separate task. If T021 ran, it saved a parquet. 
        # If that parquet has topic_cluster, we use it. But we generated NEW embeddings.
        # To be safe and consistent with the "run_novelty" step, we re-cluster based on current embeddings.
        logger.info("Re-assigning topic clusters to ensure consistency with current embeddings...")
        valid_df = assign_topic_clusters_to_dataframe(valid_df, embeddings, k=100)
    
    # Compute Centroids
    logger.info("Computing cluster centroids...")
    centroids, cluster_ids = compute_cluster_centroids_from_dataframe(valid_df, embeddings)
    
    # Compute Novelty Scores
    logger.info("Computing novelty scores...")
    novelty_scores = compute_novelty_scores(embeddings, cluster_ids, centroids)
    
    valid_df['novelty_score'] = novelty_scores
    
    # Merge back with original dataframe if we filtered out nulls?
    # The spec says: "Filter out nodes with empty or null titles... and retain them in the dataframe with null novelty scores."
    # So we should keep the original rows, but only valid ones have scores.
    
    # Create a map from id to novelty_score for valid nodes
    novelty_map = valid_df.set_index('id')['novelty_score'].to_dict()
    
    # Assign to original dataframe
    df['novelty_score'] = df['id'].map(novelty_map)
    df['topic_cluster'] = df['id'].map(valid_df.set_index('id')['topic_cluster'].to_dict())
    
    # Save final dataset
    os.makedirs(output_path.parent, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved final dataset to {output_path}")
    
    # Log stats
    stats = get_cluster_statistics(valid_df)
    logger.info(f"Cluster Statistics: {stats}")
    logger.info(f"Novelty Score Range: [{df['novelty_score'].min():.4f}, {df['novelty_score'].max():.4f}]")
    logger.info("Novelty Calculation Pipeline Complete.")

if __name__ == "__main__":
    main()
