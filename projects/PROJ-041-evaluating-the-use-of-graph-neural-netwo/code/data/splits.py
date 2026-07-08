"""
Data splitting module.
Implements Temporal Holdout validation strategy.
"""
import os
import json
import logging
from typing import List, Dict, Any, Tuple, Optional

import networkx as nx
import numpy as np

logger = logging.getLogger(__name__)

def create_temporal_split(data_path: str, train_ratio: float = 0.8) -> Tuple[str, str]:
    """
    Implements Temporal Holdout validation strategy.
    
    Splits a time-windowed graph dataset into train and test sets based on
    the temporal dimension (edge timestamps).
    
    Strategy:
    1. Load the input GraphML file.
    2. Identify edges with 'timestamp' or 'time' attributes.
    3. Sort edges chronologically.
    4. Split edges: First `train_ratio` (majority) -> Train, Remaining -> Test.
    5. Create subgraphs for Train and Test sets.
    6. Save artifacts to `data/processed/`.
    
    Args:
        data_path: Path to the input graph file (e.g., data/processed/graph_subsampled.graphml).
        train_ratio: Float between 0 and 1. Default 0.8 (80% train, 20% test).
        
    Returns:
        Tuple of (train_path, test_path) relative to project root.
        
    Raises:
        ValueError: If no temporal attributes are found on edges.
        FileNotFoundError: If input file does not exist.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Input graph file not found: {data_path}")
    
    logger.info(f"Loading graph from {data_path} for temporal split (train_ratio={train_ratio})")
    G = nx.read_graphml(data_path)
    
    # Identify temporal attribute
    edge_timestamps = []
    temporal_attr = None
    
    # Check common attribute names
    candidates = ['timestamp', 'time', 'ts', 'start_time', 'flow_start']
    for attr in candidates:
        if attr in G.edges():
            temporal_attr = attr
            break
    
    if temporal_attr is None:
        # If no explicit timestamp, check if edges have a 'time' attribute or similar
        # If strictly no time info, we cannot do a temporal split.
        # However, for network traffic, usually 'time' or 'timestamp' exists.
        # If missing, we might need to fallback to edge index order if the graph
        # was constructed sequentially, but strictly speaking, temporal split requires time.
        # Let's check if we can derive it from edge data or if we must fail.
        # Per strict requirements, we need time.
        # If the graph was built from time-ordered flows, the edge list order in GraphML 
        # might preserve insertion order, but relying on that is risky.
        # Let's assume the attribute exists as per data-model.md expectations for NetFlow.
        
        # Fallback: Try to find any attribute that looks like a number across all edges
        first_edge = next(iter(G.edges(data=True)), None)
        if first_edge:
            _, _, attrs = first_edge
            for k, v in attrs.items():
                if isinstance(v, (int, float)) and k not in ['weight', 'count']:
                    # Heuristic: might be time if not weight
                    # But we need to be sure. Let's raise a clear error if no standard key found.
                    pass
        
        raise ValueError(
            f"Temporal split failed: No temporal attribute found on edges. "
            f"Expected one of: {candidates}. "
            f"Available attributes: {list(first_edge[2].keys()) if first_edge else []}. "
            f"Ensure the input graph preserves flow timestamps."
        )
    
    # Extract edges with timestamps
    edges_with_time = []
    for u, v, data in G.edges(data=True):
        if temporal_attr in data:
            ts = data[temporal_attr]
            # Handle potential string timestamps if necessary, assuming numeric for now
            edges_with_time.append((u, v, data, float(ts)))
        else:
            # If some edges lack timestamp, we must decide: exclude or error?
            # For strict temporal split, we exclude edges without time or fail.
            # Let's exclude them from the split logic but log a warning.
            logger.warning(f"Edge ({u}, {v}) missing {temporal_attr}, excluding from split.")
    
    if not edges_with_time:
        raise ValueError("No edges found with temporal attributes after filtering.")
    
    # Sort by timestamp
    edges_with_time.sort(key=lambda x: x[3])
    
    # Calculate split index
    total_edges = len(edges_with_time)
    split_idx = int(total_edges * train_ratio)
    
    train_edges = edges_with_time[:split_idx]
    test_edges = edges_with_time[split_idx:]
    
    logger.info(f"Temporal split: {len(train_edges)} edges for train, {len(test_edges)} edges for test")
    
    # Create Train Graph
    G_train = nx.Graph()
    # Add all nodes first to preserve isolated nodes if any (though unlikely in flow graph)
    G_train.add_nodes_from(G.nodes(data=True))
    for u, v, data, _ in train_edges:
        G_train.add_edge(u, v, **data)
        
    # Create Test Graph
    G_test = nx.Graph()
    G_test.add_nodes_from(G.nodes(data=True))
    for u, v, data, _ in test_edges:
        G_test.add_edge(u, v, **data)
    
    # Determine output paths
    base_name = os.path.basename(data_path)
    name_without_ext = os.path.splitext(base_name)[0]
    output_dir = os.path.join("data", "processed")
    os.makedirs(output_dir, exist_ok=True)
    
    train_path = os.path.join(output_dir, f"{name_without_ext}_train.graphml")
    test_path = os.path.join(output_dir, f"{name_without_ext}_test.graphml")
    
    # Write graphs
    nx.write_graphml(G_train, train_path)
    nx.write_graphml(G_test, test_path)
    
    logger.info(f"Saved train graph to {train_path}")
    logger.info(f"Saved test graph to {test_path}")
    
    return train_path, test_path

def main():
    """
    Entry point for running temporal split from command line or script.
    Reads config from code/config.yaml if available, otherwise uses defaults.
    """
    import yaml
    import sys
    
    # Default config
    config_path = "code/config.yaml"
    data_input = "data/processed/graph_subsampled.graphml" # Default fallback
    train_ratio = 0.8
    
    # Try to load config
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            if config and 'temporal_split_ratio' in config:
                train_ratio = config['temporal_split_ratio']
                logger.info(f"Using temporal_split_ratio from config: {train_ratio}")
    
    # Try to find the most recent processed graph if default not found
    processed_dir = "data/processed"
    if not os.path.exists(data_input) or not os.path.exists(data_input):
        # Look for graph files
        files = [f for f in os.listdir(processed_dir) if f.endswith('.graphml') and 'train' not in f and 'test' not in f]
        if files:
            # Pick the first one (or sort by time if needed)
            data_input = os.path.join(processed_dir, sorted(files)[0])
            logger.info(f"Found graph file: {data_input}")
        else:
            logger.error(f"No input graph found at {data_input} and no other graph files in {processed_dir}")
            sys.exit(1)
    
    try:
        train_p, test_p = create_temporal_split(data_input, train_ratio)
        print(f"SUCCESS: Created splits.")
        print(f"Train: {train_p}")
        print(f"Test: {test_p}")
    except Exception as e:
        logger.error(f"Temporal split failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
