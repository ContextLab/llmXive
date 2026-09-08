import os
import sys
import logging
import pandas as pd
import networkx as nx
from pathlib import Path
from src.lib import config
from src.services.ingest import save_graph_to_parquet
from src.services.embeddings import generate_embeddings_for_dataset
from src.services.clustering import assign_topic_clusters_to_dataframe
from src.services.analysis import run_full_analysis

logger = logging.getLogger(__name__)

def load_graph_data() -> pd.DataFrame:
    """
    Load the graph data from the processed parquet file.
    """
    path = Path(config.get_data_path()) / "processed" / "subgraph_with_clusters.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Graph data not found at {path}")
    return pd.read_parquet(path)

def merge_novelty_data(df_graph: pd.DataFrame, df_novelty: pd.DataFrame) -> pd.DataFrame:
    """
    Merge graph data with novelty scores.
    """
    # Assuming df_novelty has 'id' and 'novelty_score'
    merged = df_graph.merge(df_novelty[['id', 'novelty_score']], on='id', how='left')
    return merged

def save_final_dataset(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the final analysis dataset to parquet.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Final dataset saved to {output_path}")

def main():
    """
    Main entry point to save the final dataset.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Load graph
    df_graph = load_graph_data()
    
    # Generate embeddings and novelty (simplified for this script)
    # In a real pipeline, this would be done in separate steps
    # For this task, we assume novelty is already computed or we compute it here
    # Since T020/T022 are completed, we call the service
    from src.services.embeddings import process_nodes_for_embeddings, compute_novelty_scores, save_excluded_nodes
    
    # Prepare data for embeddings
    df_valid, excluded_df = process_nodes_for_embeddings(df_graph)
    if not df_valid.empty:
        embeddings = generate_embeddings_for_dataset(df_valid)
        novelty_scores = compute_novelty_scores(df_valid, embeddings)
        df_graph.loc[df_valid.index, 'novelty_score'] = novelty_scores
        # Merge excluded back with null novelty
        if not excluded_df.empty:
            excluded_df['novelty_score'] = None
            df_graph = pd.concat([df_graph, excluded_df], ignore_index=True)
    
    # Save final dataset
    output_path = Path(config.get_data_path()) / "processed" / "final_analysis_dataset.parquet"
    save_final_dataset(df_graph, str(output_path))
    
    logger.info("Final dataset generation complete.")

if __name__ == "__main__":
    main()
