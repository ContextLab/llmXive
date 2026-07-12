import os
import logging
import networkx as nx
import pandas as pd
from typing import Dict, Any
from src.services.ingest import fetch_sample_ids, fetch_and_build_subgraph

logger = logging.getLogger(__name__)

def save_graph_to_parquet(G: nx.Graph, path: str):
    """
    Save graph to parquet format (node table).
    """
    nodes_data = []
    for node_id, attr in G.nodes(data=True):
        nodes_data.append({
            'id': node_id,
            'title': attr.get('title'),
            'citation_count': attr.get('citation_count', 0),
            'embedding_vector': attr.get('embedding_vector'),
            'primary_cluster': attr.get('primary_cluster'),
            'topic_cluster': attr.get('topic_cluster')
        })
    
    df = pd.DataFrame(nodes_data)
    df.to_parquet(path, index=False)
    logger.info(f"Saved graph to {path}")

def main():
    """
    Main entry point for saving the graph.
    """
    # This would be called from a script
    pass
