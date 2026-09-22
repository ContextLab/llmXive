import os
import sys
import logging
import pandas as pd
import networkx as nx
from pathlib import Path

# Ensure code/ is in path for imports
code_root = Path(__file__).resolve().parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.models.config import DATA_PATH, ARTIFACT_PATH
from src.services.ingest import save_graph_to_parquet
from src.services.embeddings import compute_novelty_scores, load_embedding_model, process_nodes_for_embeddings, filter_valid_nodes
from src.services.clustering import assign_topic_clusters_to_dataframe, compute_cluster_centroids

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_graph_data(graph_path: str) -> nx.Graph:
    """
    Load the processed graph with clusters and bridging coefficients from Parquet.
    """
    logger.info(f"Loading graph data from {graph_path}")
    if not os.path.exists(graph_path):
        raise FileNotFoundError(f"Graph data file not found: {graph_path}")
    
    # Load the dataframe from parquet
    df = pd.read_parquet(graph_path)
    
    # Reconstruct NetworkX graph from dataframe
    G = nx.Graph()
    for _, row in df.iterrows():
        G.add_node(row['id'], **{k: v for k, v in row.items() if k != 'id'})
    
    # Add edges (assuming edges are stored in a separate way or reconstructed)
    # For this implementation, we assume the graph structure is preserved in the node attributes
    # In a real scenario, edges would be loaded from a separate file or reconstructed
    # Here we just return the graph with node attributes
    
    logger.info(f"Loaded graph with {G.number_of_nodes()} nodes")
    return G, df

def merge_novelty_data(G: nx.Graph, df: pd.DataFrame, novelty_scores: pd.Series) -> pd.DataFrame:
    """
    Merge novelty scores into the main dataframe.
    """
    logger.info("Merging novelty scores into dataset")
    
    # Create a dataframe from the novelty series
    novelty_df = novelty_scores.reset_index()
    novelty_df.columns = ['id', 'novelty_score']
    
    # Merge with the main dataframe
    merged_df = pd.merge(df, novelty_df, on='id', how='left')
    
    # Handle any missing novelty scores (should be rare)
    merged_df['novelty_score'] = merged_df['novelty_score'].fillna(0.0)
    
    logger.info(f"Merged dataset has {len(merged_df)} rows")
    return merged_df

def save_final_dataset(df: pd.DataFrame, output_path: str):
    """
    Save the final analysis dataset with all required columns to Parquet.
    """
    logger.info(f"Saving final dataset to {output_path}")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save to Parquet
    df.to_parquet(output_path, index=False)
    
    logger.info(f"Successfully saved final dataset with {len(df)} rows to {output_path}")
    
    # Log summary statistics
    logger.info(f"Dataset columns: {list(df.columns)}")
    logger.info(f"Sample rows:\n{df.head()}")

def main():
    """
    Main function to generate the final analysis dataset.
    """
    try:
        # Define paths
        graph_path = os.path.join(DATA_PATH, 'processed', 'subgraph_with_clusters.parquet')
        output_path = os.path.join(DATA_PATH, 'processed', 'final_analysis_dataset.parquet')
        
        # Step 1: Load the graph data with clusters and bridging coefficients
        G, df = load_graph_data(graph_path)
        
        # Step 2: Prepare data for embeddings and novelty calculation
        logger.info("Preparing data for embedding and novelty calculation")
        valid_nodes, excluded_nodes = filter_valid_nodes(df)
        
        if not valid_nodes.empty:
            # Step 3: Generate embeddings for valid nodes
            logger.info("Generating embeddings for valid nodes")
            model = load_embedding_model()
            
            # Process nodes for embeddings
            texts, node_ids = process_nodes_for_embeddings(valid_nodes)
            
            # Generate embeddings in batches
            embeddings = []
            batch_size = 64
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                batch_embeddings = model.encode(batch_texts, convert_to_numpy=True)
                embeddings.extend(batch_embeddings)
            
            embeddings = np.array(embeddings)
            
            # Step 4: Assign topic clusters
            logger.info("Assigning topic clusters")
            topic_clusters = assign_topic_clusters_to_dataframe(embeddings, k=100)
            
            # Update the dataframe with topic clusters
            df.loc[valid_nodes.index, 'topic_cluster'] = topic_clusters
            
            # Step 5: Compute cluster centroids
            logger.info("Computing cluster centroids")
            centroids = compute_cluster_centroids(embeddings, topic_clusters)
            
            # Step 6: Compute novelty scores
            logger.info("Computing novelty scores")
            novelty_scores = compute_novelty_scores(embeddings, topic_clusters, centroids)
            
            # Create a series for merging
            novelty_series = pd.Series(novelty_scores, index=node_ids)
            
            # Step 7: Merge novelty scores into the main dataframe
            df = merge_novelty_data(G, df, novelty_series)
        else:
            logger.warning("No valid nodes found for embedding and novelty calculation")
            df['novelty_score'] = 0.0
            df['topic_cluster'] = -1
        
        # Step 8: Save the final dataset
        save_final_dataset(df, output_path)
        
        logger.info("Final dataset generation completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
