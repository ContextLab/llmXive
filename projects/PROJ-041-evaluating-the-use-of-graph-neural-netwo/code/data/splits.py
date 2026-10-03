import os
import json
import logging
import hashlib
from typing import List, Dict, Any, Tuple, Optional, Set
import networkx as nx
import pandas as pd
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_raw_flows(raw_dir: str) -> pd.DataFrame:
    """
    Load all CSV flow files from data/raw/ into a single DataFrame.
    Expects files like ctu13_scenario_*.csv or bot-iot_v3.csv.
    Must contain a 'timestamp' column.
    """
    flow_files = [f for f in os.listdir(raw_dir) if f.endswith('.csv')]
    if not flow_files:
        raise FileNotFoundError(f"No CSV files found in {raw_dir}")

    dfs = []
    for f in flow_files:
        path = os.path.join(raw_dir, f)
        logger.info(f"Loading {f}...")
        df = pd.read_csv(path)
        if 'timestamp' not in df.columns:
            # Try to infer timestamp column if named differently (e.g., 'time', 'StartTime')
            ts_cols = [c for c in df.columns if 'time' in c.lower()]
            if ts_cols:
                df = df.rename(columns={ts_cols[0]: 'timestamp'})
            else:
                raise ValueError(f"File {f} has no 'timestamp' column and no obvious alternative.")
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)
    logger.info(f"Loaded {len(combined)} total flows.")
    return combined

def create_temporal_split(df: pd.DataFrame, train_ratio: float, seed: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Sort flows by timestamp and split into train/test based on train_ratio.
    Returns train_df, test_df.
    """
    if 'timestamp' not in df.columns:
        raise ValueError("DataFrame must have 'timestamp' column for temporal split.")

    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])

    df_sorted = df.sort_values('timestamp').reset_index(drop=True)
    split_idx = int(len(df_sorted) * train_ratio)

    train_df = df_sorted.iloc[:split_idx].copy()
    test_df = df_sorted.iloc[split_idx:].copy()

    logger.info(f"Temporal split: Train={len(train_df)}, Test={len(test_df)} (ratio={train_ratio})")
    return train_df, test_df

def build_graph_from_train_flows(train_df: pd.DataFrame) -> nx.DiGraph:
    """
    Build a directed graph from train flows.
    Nodes: unique IPs (src_ip, dst_ip)
    Edges: (src_ip, dst_ip) with weight = count of flows (or sum of bytes/packets)
    """
    G = nx.DiGraph()

    # Aggregate edges by (src, dst)
    edge_counts = train_df.groupby(['src_ip', 'dst_ip']).size().reset_index(name='weight')

    for _, row in edge_counts.iterrows():
        src = str(row['src_ip'])
        dst = str(row['dst_ip'])
        G.add_edge(src, dst, weight=int(row['weight']))

    logger.info(f"Built graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    return G

def validate_no_leakage(train_df: pd.DataFrame, test_df: pd.DataFrame, G: nx.DiGraph) -> bool:
    """
    Validate that no edge in the Train graph connects to a node that appears ONLY in Test.
    Returns True if valid (no leakage), False otherwise.
    """
    # Nodes that appear ONLY in test (i.e., in test but not in train)
    train_nodes = set(train_df['src_ip'].unique()) | set(train_df['dst_ip'].unique())
    test_nodes = set(test_df['src_ip'].unique()) | set(test_df['dst_ip'].unique())
    test_only_nodes = test_nodes - train_nodes

    if not test_only_nodes:
        logger.info("No nodes appear only in test set; leakage check passed trivially.")
        return True

    # Check edges in G: if any edge has a destination or source in test_only_nodes, it's leakage
    leakage_found = False
    for u, v in G.edges():
        if u in test_only_nodes or v in test_only_nodes:
            logger.warning(f"Leakage detected: edge ({u}, {v}) connects to test-only node.")
            leakage_found = True
            break

    if leakage_found:
        logger.error("Temporal leakage detected: Train graph contains nodes exclusive to Test period.")
        return False
    else:
        logger.info("Leakage validation passed: No train graph edges connect to test-only nodes.")
        return True

def save_splits(train_df: pd.DataFrame, test_df: pd.DataFrame, output_dir: str):
    """
    Save train and test splits to CSV files.
    """
    os.makedirs(output_dir, exist_ok=True)
    train_path = os.path.join(output_dir, 'train_split.csv')
    test_path = os.path.join(output_dir, 'test_split.csv')

    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    logger.info(f"Saved splits: {train_path}, {test_path}")

def save_graph(G: nx.DiGraph, output_path: str):
    """
    Save graph to GraphML format.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    nx.write_graphml(G, output_path)
    logger.info(f"Saved graph: {output_path}")

def main():
    """
    Main entry point for T009: Temporal Holdout Split.
    1. Load config.yaml for temporal_split_ratio and seed.
    2. Load raw flows from data/raw/.
    3. Split into train/test.
    4. Build graph ONLY on train flows.
    5. Validate no leakage.
    6. Save train_split.csv, test_split.csv, and graph_train_split.graphml.
    """
    config_path = 'code/config.yaml'
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    train_ratio = config.get('temporal_split_ratio', 0.8)
    seed = config.get('seed', 42)
    raw_dir = 'data/raw'
    processed_dir = 'data/processed'

    logger.info(f"Starting Temporal Holdout Split (T009) with ratio={train_ratio}, seed={seed}")

    # Load raw flows
    flows = load_raw_flows(raw_dir)

    # Create temporal split
    train_df, test_df = create_temporal_split(flows, train_ratio, seed)

    # Build graph on train flows ONLY
    G_train = build_graph_from_train_flows(train_df)

    # Validate no leakage
    is_valid = validate_no_leakage(train_df, test_df, G_train)
    if not is_valid:
        raise RuntimeError("Temporal leakage detected. Aborting T009.")

    # Save outputs
    save_splits(train_df, test_df, processed_dir)
    graph_output = os.path.join(processed_dir, 'graph_train_split.graphml')
    save_graph(G_train, graph_output)

    logger.info("T009 completed successfully.")

if __name__ == '__main__':
    main()
