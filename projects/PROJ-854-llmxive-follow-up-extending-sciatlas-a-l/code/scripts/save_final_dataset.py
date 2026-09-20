"""
Script to save the final analysis dataset by merging graph data with novelty scores.

This script performs the final step of User Story 2, combining:
1. Structural data (clusters, bridging coefficients) from T016
2. Text-based data (topic clusters, novelty scores) from T022

Output: data/processed/final_analysis_dataset.parquet
"""
import os
import sys
import logging
import pandas as pd
import networkx as nx
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.lib.config import get_processed_data_path, get_raw_data_path, ensure_directories
from src.services.embeddings import compute_novelty_scores, assign_topic_clusters_to_dataframe, load_embedding_model, process_nodes_for_embeddings
from src.services.clustering import perform_kmeans_clustering, compute_cluster_centroids

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_graph_data():
    """
    Load the processed graph data with structural clusters and bridging coefficients.
    
    Returns:
        pd.DataFrame: Graph data with columns: id, title, citation_count, 
                    primary_cluster, bridging_coefficient
    """
    input_path = get_processed_data_path() / "subgraph_with_clusters.parquet"
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {input_path}. "
            "Please ensure T016 (save_graph) has been executed successfully."
        )
    
    logger.info(f"Loading graph data from {input_path}")
    df = pd.read_parquet(input_path)
    
    # Validate required columns
    required_cols = ['id', 'title', 'citation_count', 'primary_cluster', 'bridging_coefficient']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input data: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} nodes with structural data")
    return df

def merge_novelty_data(graph_df):
    """
    Compute embeddings, topic clusters, and novelty scores, then merge with graph data.
    
    Args:
        graph_df (pd.DataFrame): Graph data with structural metrics.
        
    Returns:
        pd.DataFrame: Final dataset with all metrics.
    """
    logger.info("Starting novelty score computation pipeline")
    
    # Step 1: Filter valid nodes and process titles
    valid_nodes, excluded_nodes = process_nodes_for_embeddings(graph_df)
    
    if len(excluded_nodes) > 0:
        logger.warning(f"Excluded {len(excluded_nodes)} nodes due to empty/null titles")
    
    if len(valid_nodes) == 0:
        raise ValueError("No valid nodes found for embedding generation. Cannot proceed.")
    
    # Step 2: Load model and generate embeddings
    logger.info("Loading embedding model (all-MiniLM-L6-v2)...")
    model = load_embedding_model()
    
    logger.info(f"Generating embeddings for {len(valid_nodes)} nodes (batch size 64)...")
    embeddings = model.encode(valid_nodes['title'].tolist(), batch_size=64, show_progress_bar=True)
    
    # Step 3: Assign topic clusters (k-means)
    logger.info("Performing k-means clustering (k=100) on embeddings...")
    topic_clusters = perform_kmeans_clustering(embeddings, k=100)
    
    # Step 4: Compute cluster centroids
    logger.info("Computing cluster centroids for novelty calculation...")
    centroids = compute_cluster_centroids(embeddings, topic_clusters)
    
    # Step 5: Compute novelty scores (min distance to OTHER cluster centroids)
    logger.info("Computing novelty scores (min distance to other cluster centroids)...")
    novelty_scores = compute_novelty_scores(embeddings, centroids, topic_clusters)
    
    # Step 6: Construct result DataFrame
    result_df = valid_nodes.copy()
    result_df['topic_cluster'] = topic_clusters
    result_df['novelty_score'] = novelty_scores
    
    # Step 7: Merge with original graph data (including excluded nodes)
    # We use a left join to preserve all original nodes, filling missing novelty data with NaN
    final_df = graph_df.merge(
        result_df[['id', 'topic_cluster', 'novelty_score']], 
        on='id', 
        how='left'
    )
    
    # Handle excluded nodes: they should have null novelty scores
    # (already handled by left join, but explicit check for clarity)
    excluded_ids = set(excluded_nodes['id'].tolist())
    null_mask = final_df['id'].isin(excluded_ids)
    if null_mask.any():
        logger.info(f"Ensuring {null_mask.sum()} excluded nodes have null novelty scores")
    
    logger.info(f"Merged dataset: {len(final_df)} nodes, {len(final_df.columns)} columns")
    return final_df

def save_final_dataset(df, output_filename="final_analysis_dataset.parquet"):
    """
    Save the final dataset to parquet format.
    
    Args:
        df (pd.DataFrame): The final merged dataset.
        output_filename (str): Name of the output file.
    """
    output_path = get_processed_data_path() / output_filename
    
    logger.info(f"Saving final dataset to {output_path}")
    
    # Ensure directory exists
    ensure_directories()
    
    # Save to parquet
    df.to_parquet(output_path, index=False)
    
    # Verify file exists and size
    if not output_path.exists():
        raise RuntimeError(f"Failed to write file: {output_path}")
    
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"Successfully saved {len(df)} rows to {output_path} ({file_size_mb:.2f} MB)")
    
    # Log column summary
    logger.info("Dataset columns:")
    for col in df.columns:
        logger.info(f"  - {col}: {df[col].dtype} (nulls: {df[col].isnull().sum()})")
    
    return output_path

def main():
    """Main entry point for the script."""
    try:
        logger.info("Starting final dataset generation pipeline")
        
        # 1. Load structural data
        graph_df = load_graph_data()
        
        # 2. Merge with novelty data
        final_df = merge_novelty_data(graph_df)
        
        # 3. Save result
        output_path = save_final_dataset(final_df)
        
        logger.info(f"Pipeline completed successfully. Output: {output_path}")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during pipeline execution: {e}")
        logger.exception("Traceback:")
        return 1

if __name__ == "__main__":
    sys.exit(main())
