"""
Script to save the final analysis dataset combining citations, novelty scores, and clusters.

This script aggregates data from:
1. The processed graph with bridging coefficients and primary clusters (US1)
2. The embedding-based novelty scores and topic clusters (US2)

The final output is saved as a Parquet file for efficient storage and analysis.
"""
import os
import sys
import logging
import pandas as pd
import networkx as nx
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.lib import config
from src.services.ingest import fetch_and_build_subgraph
from src.services.save_graph import save_graph_to_parquet
from src.services.embeddings import generate_embeddings_for_dataset, compute_novelty_scores
from src.services.clustering import assign_topic_clusters_to_dataframe

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_graph_data() -> Optional[nx.Graph]:
    """
    Load the processed graph from the intermediate Parquet file.
    
    Returns:
        networkx.Graph: The graph with bridging coefficients and primary clusters,
                       or None if the file doesn't exist or loading fails.
    """
    input_path = Path(config.DATA_PROCESSED_DIR) / "subgraph_with_clusters.parquet"
    
    if not input_path.exists():
        logger.warning(f"Intermediate graph file not found at {input_path}. "
                     "Attempting to rebuild from scratch...")
        try:
            G = fetch_and_build_subgraph(target_size=1000)
            save_graph_to_parquet(G, output_path=input_path)
            logger.info(f"Rebuilt and saved graph to {input_path}")
            return G
        except Exception as e:
            logger.error(f"Failed to rebuild graph: {e}")
            return None
    
    try:
        # Load the graph from Parquet
        df = pd.read_parquet(input_path)
        G = nx.Graph()
        
        # Reconstruct graph from DataFrame
        # Assuming the DataFrame has columns: id, title, citation_count, 
        # embedding_vector, primary_cluster, topic_cluster, bridging_coefficient
        for _, row in df.iterrows():
            G.add_node(
                row['id'],
                title=row.get('title', ''),
                citation_count=row.get('citation_count', 0),
                primary_cluster=row.get('primary_cluster', -1),
                bridging_coefficient=row.get('bridging_coefficient', 0.0)
            )
        
        logger.info(f"Loaded graph with {G.number_of_nodes()} nodes from {input_path}")
        return G
    except Exception as e:
        logger.error(f"Failed to load graph from {input_path}: {e}")
        return None

def merge_novelty_data(graph_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge novelty scores and topic clusters into the main dataset.
    
    Args:
        graph_df: DataFrame containing graph data with node attributes.
        
    Returns:
        pd.DataFrame: DataFrame with added novelty_score and topic_cluster columns.
    """
    if graph_df.empty:
        logger.warning("Input DataFrame is empty, cannot merge novelty data.")
        return graph_df
    
    # Filter nodes with valid titles for embedding processing
    valid_nodes_df = graph_df[graph_df['title'].notna() & (graph_df['title'] != '')].copy()
    
    if valid_nodes_df.empty:
        logger.warning("No valid nodes with titles found for novelty calculation.")
        # Add default values for all nodes
        graph_df['novelty_score'] = 0.0
        graph_df['topic_cluster'] = -1
        return graph_df
    
    logger.info(f"Processing {len(valid_nodes_df)} nodes for novelty calculation...")
    
    # Generate embeddings for valid nodes
    embeddings = generate_embeddings_for_dataset(valid_nodes_df)
    
    if embeddings is None or len(embeddings) == 0:
        logger.warning("Failed to generate embeddings, using default novelty scores.")
        graph_df['novelty_score'] = 0.0
        graph_df['topic_cluster'] = -1
        return graph_df
    
    # Compute novelty scores
    novelty_results = compute_novelty_scores(valid_nodes_df, embeddings)
    
    if novelty_results is None or 'novelty_score' not in novelty_results.columns:
        logger.warning("Failed to compute novelty scores, using defaults.")
        graph_df['novelty_score'] = 0.0
        graph_df['topic_cluster'] = -1
        return graph_df
    
    # Merge results back to the main DataFrame
    # Create a mapping from node_id to novelty_score and topic_cluster
    novelty_map = novelty_results.set_index('id')[['novelty_score', 'topic_cluster']].to_dict('index')
    
    graph_df['novelty_score'] = graph_df['id'].map(
        lambda x: novelty_map.get(x, {}).get('novelty_score', 0.0)
    )
    graph_df['topic_cluster'] = graph_df['id'].map(
        lambda x: novelty_map.get(x, {}).get('topic_cluster', -1)
    )
    
    # For nodes without valid titles, assign default values
    graph_df.loc[graph_df['novelty_score'].isna(), 'novelty_score'] = 0.0
    graph_df.loc[graph_df['topic_cluster'].isna(), 'topic_cluster'] = -1
    
    logger.info(f"Merged novelty data: {graph_df['novelty_score'].notna().sum()} nodes with scores")
    return graph_df

def save_final_dataset(df: pd.DataFrame, output_path: Path) -> bool:
    """
    Save the final analysis dataset to Parquet format.
    
    Args:
        df: DataFrame containing the final analysis data.
        output_path: Path where the Parquet file will be saved.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to Parquet
        df.to_parquet(output_path, index=False)
        
        logger.info(f"Successfully saved final dataset to {output_path}")
        logger.info(f"Dataset shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")
        
        # Log summary statistics
        logger.info(f"Nodes with citation_count > 0: {(df['citation_count'] > 0).sum()}")
        logger.info(f"Nodes with novelty_score > 0: {(df['novelty_score'] > 0).sum()}")
        logger.info(f"Unique primary clusters: {df['primary_cluster'].nunique()}")
        logger.info(f"Unique topic clusters: {df['topic_cluster'].nunique()}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to save final dataset to {output_path}: {e}")
        return False

def main():
    """
    Main entry point for the final dataset generation pipeline.
    
    This function:
    1. Loads the processed graph with bridging coefficients
    2. Merges novelty scores and topic clusters
    3. Saves the combined dataset to Parquet
    """
    logger.info("Starting final dataset generation...")
    
    # Load graph data
    G = load_graph_data()
    if G is None:
        logger.error("Failed to load graph data. Aborting.")
        sys.exit(1)
    
    # Convert graph to DataFrame
    try:
        nodes_data = []
        for node_id, attrs in G.nodes(data=True):
            nodes_data.append({
                'id': node_id,
                'title': attrs.get('title', ''),
                'citation_count': attrs.get('citation_count', 0),
                'primary_cluster': attrs.get('primary_cluster', -1),
                'bridging_coefficient': attrs.get('bridging_coefficient', 0.0)
            })
        
        graph_df = pd.DataFrame(nodes_data)
        logger.info(f"Converted graph to DataFrame with {len(graph_df)} rows")
    except Exception as e:
        logger.error(f"Failed to convert graph to DataFrame: {e}")
        sys.exit(1)
    
    # Merge novelty data
    final_df = merge_novelty_data(graph_df)
    
    if final_df.empty:
        logger.error("Final dataset is empty. Aborting.")
        sys.exit(1)
    
    # Ensure required columns exist
    required_columns = [
        'id', 'title', 'citation_count', 'primary_cluster', 
        'bridging_coefficient', 'novelty_score', 'topic_cluster'
    ]
    
    missing_cols = [col for col in required_columns if col not in final_df.columns]
    if missing_cols:
        logger.warning(f"Missing required columns: {missing_cols}. Adding with default values.")
        for col in missing_cols:
            final_df[col] = 0 if col in ['citation_count', 'bridging_coefficient', 'novelty_score'] else -1
    
    # Save final dataset
    output_path = Path(config.DATA_PROCESSED_DIR) / "final_analysis_dataset.parquet"
    success = save_final_dataset(final_df, output_path)
    
    if not success:
        logger.error("Failed to save final dataset.")
        sys.exit(1)
    
    logger.info("Final dataset generation completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
