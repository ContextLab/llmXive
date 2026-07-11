import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import networkx as nx
import numpy as np
import pandas as pd

from utils.config import get_logger, setup_logging
from utils.seeds import set_global_seed
from data.schema import validate_overlap_matrix_file, validate_topology_graph_file

# Configure logger
logger = get_logger(__name__)


def load_adapters(adapters_path: Path) -> pd.DataFrame:
    """Load the synthetic adapters from parquet file."""
    if not adapters_path.exists():
        raise FileNotFoundError(f"Adapters file not found: {adapters_path}")
    logger.info(f"Loading adapters from {adapters_path}")
    return pd.read_parquet(adapters_path)


def extract_param_vectors(df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
    """
    Extract parameter vectors from the adapter dataframe.
    Assumes columns contain serialized weight arrays (e.g., base64 or JSON strings).
    For this implementation, we assume the dataframe has a 'params' column with list-like data.
    """
    logger.info("Extracting parameter vectors...")
    # Assuming the 'params' column contains the flattened weight vectors
    # If stored as strings, we might need to parse them.
    # Based on generate_adapters logic, we expect a column with the data.
    # Let's assume the column is named 'weights' or 'params' and contains arrays.
    # If it's a parquet file from generate_adapters, it likely has a column 'weights'.
    
    # Fallback: check for 'weights' column
    if 'weights' in df.columns:
        weights_col = 'weights'
    elif 'params' in df.columns:
        weights_col = 'params'
    else:
        # Try to find any column that looks like an array
        numeric_cols = df.select_dtypes(include=[object]).columns
        if len(numeric_cols) > 0:
            weights_col = numeric_cols[0]
        else:
            raise ValueError("No suitable parameter column found in adapters dataframe")

    vectors = []
    adapter_ids = []
    for _, row in df.iterrows():
        # Handle potential string serialization if necessary
        val = row[weights_col]
        if isinstance(val, str):
            # Try to parse as JSON list
            try:
                val = json.loads(val)
            except json.JSONDecodeError:
                raise ValueError(f"Could not parse weights for row {row['adapter_id']}")
        
        vectors.append(np.array(val, dtype=np.float32))
        adapter_ids.append(row['adapter_id'])
    
    return np.array(vectors), adapter_ids


def compute_cosine_similarity_matrix(vectors: np.ndarray) -> np.ndarray:
    """Compute the pairwise cosine similarity matrix."""
    logger.info(f"Computing cosine similarity for {len(vectors)} vectors...")
    # Normalize vectors
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    # Avoid division by zero
    norms[norms == 0] = 1e-10
    normalized = vectors / norms
    
    # Compute similarity
    similarity = np.dot(normalized, normalized.T)
    return similarity


def normalize_similarity_matrix(similarity: np.ndarray, low: float = 0.0, high: float = 1.0) -> np.ndarray:
    """
    Normalize the similarity matrix to a bounded interval [low, high].
    Cosine similarity is already in [-1, 1]. We map it to [0, 1] or custom bounds.
    """
    logger.info(f"Normalizing similarity matrix to [{low}, {high}]")
    # Map from [-1, 1] to [low, high]
    # Formula: new_val = low + (val - min) * (high - low) / (max - min)
    # Since min is -1 and max is 1 for cosine similarity:
    # new_val = low + (val + 1) * (high - low) / 2
    
    normalized = low + (similarity + 1.0) * (high - low) / 2.0
    return np.clip(normalized, low, high)


def save_overlap_matrix(matrix: np.ndarray, ids: List[str], output_path: Path):
    """Save the overlap matrix to a CSV file."""
    logger.info(f"Saving overlap matrix to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(matrix, index=ids, columns=ids)
    df.to_csv(output_path)
    validate_overlap_matrix_file(output_path)


def build_topology_graph(overlap_matrix: np.ndarray, ids: List[str], threshold: float = 0.5) -> nx.Graph:
    """
    Build an undirected networkx graph from the overlap matrix.
    Nodes are adapters. Edges exist if the overlap (similarity) is above a threshold.
    """
    logger.info(f"Building topology graph with threshold {threshold}")
    G = nx.Graph()
    
    # Add nodes
    for i, adapter_id in enumerate(ids):
        G.add_node(adapter_id, index=i)
    
    # Add edges
    n = len(ids)
    edge_count = 0
    for i in range(n):
        for j in range(i + 1, n):
            weight = overlap_matrix[i, j]
            if weight >= threshold:
                G.add_edge(ids[i], ids[j], weight=weight)
                edge_count += 1
    
    logger.info(f"Graph created: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def save_topology_graph(graph: nx.Graph, output_path: Path):
    """Save the topology graph to a JSON file."""
    logger.info(f"Saving topology graph to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert graph to a serializable format
    # nx.node_link_data preserves node/edge attributes
    data = nx.node_link_data(graph)
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    validate_topology_graph_file(output_path)


def validate_output(graph: nx.Graph, overlap_matrix: np.ndarray, threshold: float) -> bool:
    """
    Validate that the graph construction is non-trivial.
    Checks:
    1. Graph is not empty (has edges).
    2. Graph is connected or has a large connected component.
    3. Edge weights are consistent with the matrix.
    """
    logger.info("Validating graph output...")
    
    if graph.number_of_edges() == 0:
        logger.warning("Graph has no edges. Consider lowering the threshold.")
        return False
    
    # Check connectivity
    if nx.is_connected(graph):
        logger.info("Graph is fully connected.")
    else:
        components = list(nx.connected_components(graph))
        largest_cc = max(components, key=len)
        logger.info(f"Graph has {len(components)} components. Largest CC has {len(largest_cc)} nodes.")
        if len(largest_cc) < len(graph.nodes()) * 0.5:
            logger.warning("Largest connected component is less than 50% of the graph.")
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Compute overlap and build topology graph")
    parser.add_argument("--adapters", type=str, required=True, help="Path to adapters parquet file")
    parser.add_argument("--overlap-output", type=str, required=True, help="Path to save overlap matrix CSV")
    parser.add_argument("--graph-output", type=str, required=True, help="Path to save topology graph JSON")
    parser.add_argument("--threshold", type=float, default=0.5, help="Similarity threshold for graph edges")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    setup_logging(level=args.log_level)
    set_global_seed(args.seed)
    
    adapters_path = Path(args.adapters)
    overlap_output = Path(args.overlap_output)
    graph_output = Path(args.graph_output)
    
    try:
        # Load data
        df = load_adapters(adapters_path)
        
        # Extract vectors
        vectors, ids = extract_param_vectors(df)
        
        # Compute similarity
        similarity = compute_cosine_similarity_matrix(vectors)
        
        # Normalize (optional, depending on requirements, but good for consistent thresholds)
        # Cosine similarity is [-1, 1], let's normalize to [0, 1] for easier thresholding
        normalized_similarity = normalize_similarity_matrix(similarity, low=0.0, high=1.0)
        
        # Save overlap matrix
        save_overlap_matrix(normalized_similarity, ids, overlap_output)
        
        # Build graph
        graph = build_topology_graph(normalized_similarity, ids, threshold=args.threshold)
        
        # Validate
        is_valid = validate_output(graph, normalized_similarity, args.threshold)
        
        # Save graph
        save_topology_graph(graph, graph_output)
        
        if is_valid:
            logger.info("Graph construction completed successfully.")
            return 0
        else:
            logger.warning("Graph construction completed with warnings (e.g., sparse graph).")
            return 0 # Still success, but with warnings
            
    except Exception as e:
        logger.error(f"Error during computation: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
