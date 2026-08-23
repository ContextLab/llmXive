import os
import sys
import logging
import hashlib
import tracemalloc
import random
import networkx as nx
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List

# Import project utilities
from utils.memory_monitor import (
    start_monitoring,
    stop_monitoring,
    get_peak_memory_mb,
    MemoryLimitExceededError,
    check_memory_limit,
)
from utils.seed import set_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_MB = MEMORY_LIMIT_GB * 1024
MAX_NODES = 5000


def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def build_graph_from_csv(csv_path: str) -> nx.DiGraph:
    """
    Build a directed graph from a NetFlow CSV.
    Nodes: IPs (source and destination)
    Edges: Flows (source -> dest)
    Attributes: weight (packet count), label (anomaly/normal if available)
    """
    logger.info(f"Building graph from {csv_path}")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    # Load data
    df = pd.read_csv(csv_path)

    # Ensure required columns exist
    required_cols = ["src_ip", "dst_ip"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    G = nx.DiGraph()

    # Add nodes
    nodes = set(df["src_ip"].unique()) | set(df["dst_ip"].unique())
    G.add_nodes_from(nodes)

    # Add edges with attributes
    # Aggregate flows to edges: sum packet counts, count flows
    edge_data = df.groupby(["src_ip", "dst_ip"]).agg(
        {"packets": "sum", "bytes": "sum", "flow_id": "count"}
    ).reset_index()

    edge_data.columns = ["src_ip", "dst_ip", "weight_packets", "weight_bytes", "flow_count"]

    for _, row in edge_data.iterrows():
        src, dst = row["src_ip"], row["dst_ip"]
        # Add edge attributes
        G.add_edge(
            src,
            dst,
            weight_packets=int(row["weight_packets"]),
            weight_bytes=int(row["weight_bytes"]),
            flow_count=int(row["flow_count"]),
        )

    # Add anomaly labels to nodes if available
    if "label" in df.columns:
        # Aggregate label per node (e.g., if any flow involving node is anomaly, mark node)
        node_labels = {}
        for _, row in df.iterrows():
            src, dst = row["src_ip"], row["dst_ip"]
            label = row["label"]
            if src not in node_labels:
                node_labels[src] = label
            elif node_labels[src] == 0 and label == 1:
                node_labels[src] = 1
            if dst not in node_labels:
                node_labels[dst] = label
            elif node_labels[dst] == 0 and label == 1:
                node_labels[dst] = 1

        nx.set_node_attributes(G, node_labels, "label")

    logger.info(f"Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def extract_lcc(G: nx.DiGraph) -> nx.DiGraph:
    """Extract the Largest Connected Component (LCC) of the graph."""
    logger.info("Extracting Largest Connected Component (LCC)")
    # For directed graphs, we consider the underlying undirected graph for connectivity
    if not nx.is_strongly_connected(G):
        undirected_G = G.to_undirected()
        lcc_nodes = max(nx.connected_components(undirected_G), key=len)
        G_lcc = G.subgraph(lcc_nodes).copy()
        logger.info(f"LCC extracted: {G_lcc.number_of_nodes()} nodes, {G_lcc.number_of_edges()} edges")
        return G_lcc
    else:
        logger.info("Graph is already strongly connected, returning original")
        return G


def subsample_graph(G: nx.DiGraph, max_nodes: int = MAX_NODES) -> nx.DiGraph:
    """
    Randomly subsample nodes and edges to reach max_nodes.
    Preserves the structure of the LCC.
    """
    logger.info(f"Subsampling graph to {max_nodes} nodes")
    if G.number_of_nodes() <= max_nodes:
        return G

    # Randomly select nodes to keep
    all_nodes = list(G.nodes())
    random.shuffle(all_nodes)
    selected_nodes = set(all_nodes[:max_nodes])

    # Create subgraph
    G_sub = G.subgraph(selected_nodes).copy()

    # If subgraph has fewer nodes than expected (due to isolation), try to add back edges
    # But for simplicity, we just return the subgraph
    logger.info(f"Subsampled graph: {G_sub.number_of_nodes()} nodes, {G_sub.number_of_edges()} edges")
    return G_sub


def validate_graph(G: nx.DiGraph) -> None:
    """Validate graph properties: non-negative integer weights, etc."""
    logger.info("Validating graph properties")
    for u, v, data in G.edges(data=True):
        if "weight_packets" in data:
            if not isinstance(data["weight_packets"], int) or data["weight_packets"] < 0:
                raise ValueError(f"Invalid weight_packets for edge ({u}, {v}): {data['weight_packets']}")
        if "weight_bytes" in data:
            if not isinstance(data["weight_bytes"], int) or data["weight_bytes"] < 0:
                raise ValueError(f"Invalid weight_bytes for edge ({u}, {v}): {data['weight_bytes']}")

    # Check node labels if present
    if "label" in G.nodes(data=True)[0][1]:
        for node, data in G.nodes(data=True):
            if "label" in data:
                if data["label"] not in [0, 1]:
                    logger.warning(f"Node {node} has unexpected label: {data['label']}")

    logger.info("Graph validation passed")


def write_graph_with_hash(G: nx.DiGraph, output_path: str) -> str:
    """
    Write graph to file and generate SHA256 hash sidecar.
    Returns the hash string.
    """
    logger.info(f"Writing graph to {output_path}")
    nx.write_graphml(G, output_path)

    # Calculate and write hash
    hash_value = calculate_sha256(output_path)
    hash_path = output_path + ".hash"
    with open(hash_path, "w") as f:
        f.write(hash_value)

    logger.info(f"Graph written with hash: {hash_value}")
    return hash_value


def preprocess_graph(
    csv_path: str,
    scenario_name: str,
    output_dir: str = "data/processed",
    memory_limit_mb: float = MEMORY_LIMIT_MB,
) -> Tuple[str, str]:
    """
    Main preprocessing pipeline:
    1. Build graph from CSV.
    2. Check memory and node count.
    3. Extract LCC if needed.
    4. Subsample if needed.
    5. Validate.
    6. Write output with hash sidecar.
    Returns: (output_path, hash_value)
    """
    set_seed(42)  # Ensure reproducibility

    os.makedirs(output_dir, exist_ok=True)

    # Start memory monitoring
    start_monitoring()

    try:
        # Step 1: Build graph
        G_raw = build_graph_from_csv(csv_path)
        node_count = G_raw.number_of_nodes()
        logger.info(f"Initial graph: {node_count} nodes")

        # Step 2: Check memory usage
        peak_mem = get_peak_memory_mb()
        logger.info(f"Peak memory after build: {peak_mem:.2f} MB")

        # Step 3: Apply subsampling logic based on thresholds
        G_final = G_raw
        if node_count > MAX_NODES or peak_mem > memory_limit_mb:
            logger.info("Thresholds exceeded, applying LCC and subsampling")
            G_final = extract_lcc(G_raw)
            if G_final.number_of_nodes() > MAX_NODES:
                G_final = subsample_graph(G_final, MAX_NODES)
        else:
            logger.info("Thresholds not exceeded, retaining graph as-is")

        # Step 4: Validate
        validate_graph(G_final)

        # Step 5: Write output
        output_path = os.path.join(output_dir, f"graph_{scenario_name}_subsampled.graphml")
        hash_value = write_graph_with_hash(G_final, output_path)

        # Stop monitoring
        stop_monitoring()
        final_peak_mem = get_peak_memory_mb()
        logger.info(f"Final peak memory: {final_peak_mem:.2f} MB")

        return output_path, hash_value

    except MemoryLimitExceededError as e:
        stop_monitoring()
        logger.error(f"Memory limit exceeded: {e}")
        raise
    except Exception as e:
        stop_monitoring()
        logger.error(f"Preprocessing failed: {e}")
        raise


def main():
    """CLI entry point for preprocessing."""
    import argparse

    parser = argparse.ArgumentParser(description="Preprocess NetFlow data into graphs")
    parser.add_argument("--csv", type=str, required=True, help="Path to input CSV file")
    parser.add_argument("--scenario", type=str, required=True, help="Scenario name for output files")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Output directory")
    args = parser.parse_args()

    preprocess_graph(args.csv, args.scenario, args.output_dir)
    logger.info("Preprocessing completed successfully")


if __name__ == "__main__":
    main()