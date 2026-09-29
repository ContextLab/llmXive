"""
Temporal Holdout Split Implementation for Network Traffic Anomaly Detection.

This module implements the temporal split logic required to prevent data leakage
in graph-based anomaly detection. It loads raw flows, splits them by timestamp,
constructs a graph ONLY on the training subset, and validates that no edges
connect to nodes that appear exclusively in the test period.

Outputs:
  - data/processed/train_split.csv
  - data/processed/test_split.csv
  - data/processed/graph_train_split.graphml
"""

import os
import json
import logging
import hashlib
from typing import List, Dict, Any, Tuple, Optional, Set
import networkx as nx
import numpy as np
import pandas as pd
from datetime import datetime

# Import project utilities
from utils.seed import set_seed, get_seed_value
from utils.memory_monitor import enforce_memory_limit, get_peak_memory_mb

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_raw_flows(raw_data_dir: str = "data/raw") -> pd.DataFrame:
    """
    Load raw network flow data from CSV files in the raw_data_dir.
    Expects files like 'CTU-13-Scenario-1.csv' or similar.
    Returns a consolidated DataFrame.
    """
    flow_files = [f for f in os.listdir(raw_data_dir) if f.endswith('.csv')]
    if not flow_files:
        raise FileNotFoundError(f"No CSV files found in {raw_data_dir}. Ensure T007a/T007b completed successfully.")

    dfs = []
    for file in flow_files:
        logger.info(f"Loading flow file: {file}")
        df = pd.read_csv(os.path.join(raw_data_dir, file))
        
        # Ensure timestamp column exists and is datetime
        if 'Start time' in df.columns:
            df['timestamp'] = pd.to_datetime(df['Start time'], errors='coerce')
        elif 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        else:
            # Fallback: try to find a time-like column
            time_cols = [c for c in df.columns if 'time' in c.lower() or 'date' in c.lower()]
            if time_cols:
                df['timestamp'] = pd.to_datetime(df[time_cols[0]], errors='coerce')
            else:
                raise ValueError(f"Could not find a timestamp column in {file}. Columns: {df.columns.tolist()}")
        
        # Drop rows with invalid timestamps
        initial_count = len(df)
        df = df.dropna(subset=['timestamp'])
        dropped = initial_count - len(df)
        if dropped > 0:
            logger.warning(f"Dropped {dropped} rows with invalid timestamps in {file}")
        
        dfs.append(df)

    if not dfs:
        raise ValueError("No valid flow data loaded.")

    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Loaded {len(combined_df)} total flows.")
    return combined_df

def create_temporal_split(df: pd.DataFrame, train_ratio: float = 0.8, seed: Optional[int] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split flows into train and test sets based on timestamp.
    
    Logic:
    1. Sort by timestamp.
    2. Split into Train (first train_ratio) and Test (remaining).
    
    Args:
        df: DataFrame with a 'timestamp' column.
        train_ratio: Fraction of data to use for training (e.g., 0.8).
        seed: Random seed (not used for temporal split, but kept for API consistency).
    
    Returns:
        Tuple of (train_df, test_df)
    """
    if seed is not None:
        set_seed(seed)
    
    df_sorted = df.sort_values(by='timestamp').reset_index(drop=True)
    split_idx = int(len(df_sorted) * train_ratio)
    
    train_df = df_sorted.iloc[:split_idx].copy()
    test_df = df_sorted.iloc[split_idx:].copy()
    
    logger.info(f"Temporal Split: Train={len(train_df)} ({len(train_df)/len(df_sorted):.2%}), "
                f"Test={len(test_df)} ({len(test_df)/len(df_sorted):.2%})")
    
    return train_df, test_df

def build_graph_from_train_flows(train_df: pd.DataFrame) -> nx.DiGraph:
    """
    Construct a directed graph ONLY from the training flows.
    
    Nodes: Unique IP addresses (source and destination).
    Edges: Directed edges from src_ip to dst_ip for each flow.
    Edge Attributes:
        - weight: Number of flows (aggregated).
        - packets: Sum of packets (or count if not available).
        - bytes: Sum of bytes.
    
    Node Attributes:
        - type: 'src' or 'dst' (inferred from edge direction).
        - first_seen: Earliest timestamp in train set.
    
    CRITICAL: This function must NOT see test data.
    """
    logger.info("Building graph from training flows only...")
    
    # Identify source and destination columns
    src_col = None
    dst_col = None
    packets_col = None
    bytes_col = None
    
    # Heuristic column detection
    cols = train_df.columns.str.lower()
    if 'src ip' in cols or 'src_ip' in cols:
        src_col = 'src ip' if 'src ip' in cols else 'src_ip'
    elif 'source ip' in cols:
        src_col = 'source ip'
    elif 'src' in cols:
        src_col = 'src'
        
    if 'dst ip' in cols or 'dst_ip' in cols:
        dst_col = 'dst ip' if 'dst ip' in cols else 'dst_ip'
    elif 'dest ip' in cols:
        dst_col = 'dest ip'
    elif 'dst' in cols:
        dst_col = 'dst'
    
    if 'packets' in cols:
        packets_col = 'packets'
    elif 'pkt' in cols:
        packets_col = 'pkt'
        
    if 'bytes' in cols:
        bytes_col = 'bytes'
    elif 'byt' in cols:
        bytes_col = 'byt'
    
    if not src_col or not dst_col:
        raise ValueError("Could not identify source/destination IP columns.")
    
    # Aggregate edges
    edge_data = train_df.groupby([src_col, dst_col]).agg({
        packets_col: 'sum' if packets_col else 'count',
        bytes_col: 'sum' if bytes_col else 1,
        'timestamp': 'min'
    }).reset_index()
    
    # Rename columns for graph attributes
    edge_data['weight'] = 1.0 # Base weight per unique edge pair
    if packets_col:
        edge_data['packets'] = edge_data[packets_col]
    if bytes_col:
        edge_data['bytes'] = edge_data[bytes_col]
    
    G = nx.DiGraph()
    
    # Add edges and attributes
    for _, row in edge_data.iterrows():
        src = str(row[src_col])
        dst = str(row[dst_col])
        G.add_edge(src, dst, weight=row.get('weight', 1.0))
        
        # Add node attributes if not exists
        if src not in G.nodes:
            G.add_node(src, type='src', first_seen=row['timestamp'])
        if dst not in G.nodes:
            G.add_node(dst, type='dst', first_seen=row['timestamp'])
    
    logger.info(f"Graph constructed: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.")
    return G

def validate_no_leakage(train_df: pd.DataFrame, test_df: pd.DataFrame, G: nx.DiGraph) -> bool:
    """
    Validate that no edges in the Train graph connect to nodes that appear ONLY in the Test period.
    
    Logic:
    1. Identify nodes that appear in Test but NOT in Train.
    2. Check if any edges in G (train graph) connect to these 'test-only' nodes.
    3. If yes, leakage detected -> raise error.
    
    Note: Since we built G ONLY from train_df, theoretically no test-only nodes should exist in G.
    However, this check validates the integrity of the split logic and data consistency.
    """
    logger.info("Validating temporal leakage...")
    
    # Get all IPs in train and test
    src_col = 'src ip' if 'src ip' in train_df.columns else ('src_ip' if 'src_ip' in train_df.columns else None)
    dst_col = 'dst ip' if 'dst ip' in train_df.columns else ('dst_ip' if 'dst_ip' in train_df.columns else None)
    
    if not src_col or not dst_col:
        logger.warning("Could not find IP columns for leakage check.")
        return True
    
    train_nodes = set(train_df[src_col].astype(str).unique()) | set(train_df[dst_col].astype(str).unique())
    test_nodes = set(test_df[src_col].astype(str).unique()) | set(test_df[dst_col].astype(str).unique())
    
    test_only_nodes = test_nodes - train_nodes
    
    if not test_only_nodes:
        logger.info("No nodes appear exclusively in the test set. Leakage check passed.")
        return True
    
    # Check edges in G
    leakage_found = False
    for u, v in G.edges():
        if u in test_only_nodes or v in test_only_nodes:
            logger.error(f"LEAKAGE DETECTED: Edge ({u}, {v}) connects to test-only node.")
            leakage_found = True
            
    if leakage_found:
        raise ValueError("Temporal leakage detected: Train graph contains edges to nodes exclusive to Test set.")
    
    logger.info("Leakage validation passed.")
    return True

def save_splits(train_df: pd.DataFrame, test_df: pd.DataFrame, output_dir: str = "data/processed") -> Tuple[str, str]:
    """
    Save train and test splits to CSV files.
    
    Outputs:
      - data/processed/train_split.csv
      - data/processed/test_split.csv
    """
    if not os.makedirs(output_dir, exist_ok=True):
        os.makedirs(output_dir)
    
    train_path = os.path.join(output_dir, "train_split.csv")
    test_path = os.path.join(output_dir, "test_split.csv")
    
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    logger.info(f"Saved splits: {train_path}, {test_path}")
    return train_path, test_path

def save_graph(G: nx.DiGraph, output_path: str = "data/processed/graph_train_split.graphml") -> str:
    """
    Save the constructed graph to a GraphML file.
    
    Output:
      - data/processed/graph_train_split.graphml
    """
    nx.write_graphml(G, output_path)
    logger.info(f"Saved graph: {output_path}")
    return output_path

def main():
    """
    Main entry point for the Temporal Holdout Split task.
    """
    logger.info("Starting Temporal Holdout Split (T009)...")
    
    # 1. Load Raw Flows
    try:
        raw_df = load_raw_flows("data/raw")
    except FileNotFoundError as e:
        logger.error(f"Data ingestion failed. Ensure T007a/T007b are complete: {e}")
        raise
    
    # 2. Create Temporal Split
    train_df, test_df = create_temporal_split(raw_df, train_ratio=0.8)
    
    # 3. Build Graph ONLY on Train subset
    G = build_graph_from_train_flows(train_df)
    
    # 4. Validate No Leakage
    validate_no_leakage(train_df, test_df, G)
    
    # 5. Save Outputs
    save_splits(train_df, test_df)
    graph_path = save_graph(G)
    
    logger.info("T009 completed successfully.")
    logger.info(f"Artifacts created: data/processed/train_split.csv, data/processed/test_split.csv, {graph_path}")

if __name__ == "__main__":
    main()
