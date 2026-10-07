import os
import sys
import logging
import hashlib
import tracemalloc
import random
import pandas as pd
import networkx as nx
from typing import Optional, Dict, Any, Tuple

# Import shared utilities from the project API
from utils.seed import set_seed, get_seed_value
from utils.memory_monitor import (
    MemoryLimitExceededError,
    start_monitoring,
    stop_monitoring,
    get_peak_memory_mb,
    enforce_memory_limit_check,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MEMORY_LIMIT_MB = 7000  # 7GB
INPUT_DIR = "data/processed"
OUTPUT_DIR = "data/processed"


def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def build_graph_from_csv(
    input_path: str,
    output_path: str,
    src_col: str = "src_ip",
    dst_col: str = "dst_ip",
    weight_col: str = "packet_count",
    seed: Optional[int] = None,
) -> Tuple[nx.DiGraph, Dict[str, Any]]:
    """
    Construct a directed graph from a processed NetFlow parquet/CSV file.

    Nodes are unique IPs (source and destination).
    Edges represent flows from source to destination.
    Edge weights are derived from the specified weight column (e.g., packet count).

    Args:
        input_path: Path to the input parquet/CSV file (output of T013a).
        output_path: Path to write the resulting GraphML file.
        src_col: Name of the source IP column.
        dst_col: Name of the destination IP column.
        weight_col: Name of the column to use as edge weight.
        seed: Random seed for reproducibility (if needed for tie-breaking).

    Returns:
        Tuple of (constructed nx.DiGraph, metadata dict).
    """
    if seed is not None:
        set_seed(seed)

    logger.info(f"Loading flows from {input_path}...")
    if input_path.endswith(".parquet"):
        df = pd.read_parquet(input_path)
    else:
        df = pd.read_csv(input_path)

    # Basic validation
    required_cols = [src_col, dst_col, weight_col]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Input file missing required columns: {missing}")

    # Ensure weight column is numeric
    df[weight_col] = pd.to_numeric(df[weight_col], errors="coerce").fillna(0)

    logger.info(f"Constructing directed graph with {len(df)} flow records...")
    G = nx.DiGraph()

    # Add edges
    # Using a dictionary to aggregate weights if multiple edges exist between same nodes
    edge_weights = {}
    for _, row in df.iterrows():
        src = str(row[src_col])
        dst = str(row[dst_col])
        weight = float(row[weight_col])

        if src == dst:
            continue  # Skip self-loops for network traffic graphs

        edge_key = (src, dst)
        if edge_key in edge_weights:
            edge_weights[edge_key] += weight
        else:
            edge_weights[edge_key] = weight
            # Add nodes implicitly by adding edge, but ensure attributes if needed
            if src not in G:
                G.add_node(src)
            if dst not in G:
                G.add_node(dst)

    # Add aggregated edges
    for (src, dst), weight in edge_weights.items():
        G.add_edge(src, dst, weight=weight)

    # Metadata
    metadata = {
        "num_nodes": G.number_of_nodes(),
        "num_edges": G.number_of_edges(),
        "source_file": os.path.basename(input_path),
        "avg_degree": sum(dict(G.degree()).values()) / G.number_of_nodes()
        if G.number_of_nodes() > 0
        else 0,
    }

    logger.info(
        f"Graph constructed: {metadata['num_nodes']} nodes, "
        f"{metadata['num_edges']} edges."
    )

    # Validate graph
    validate_graph(G)

    # Write to disk
    write_graph_with_hash(G, output_path)

    return G, metadata


def validate_graph(G: nx.DiGraph) -> bool:
    """
    Validate the constructed graph against basic integrity checks.

    Args:
        G: The networkx DiGraph to validate.

    Returns:
        True if valid, raises ValueError otherwise.
    """
    if G.number_of_nodes() == 0:
        raise ValueError("Constructed graph has no nodes.")
    if G.number_of_edges() == 0:
        raise ValueError("Constructed graph has no edges.")

    # Check for NaN weights
    for u, v, data in G.edges(data=True):
        if "weight" in data:
            w = data["weight"]
            if pd.isna(w) or w < 0:
                raise ValueError(f"Invalid weight {w} for edge ({u}, {v})")

    logger.info("Graph validation passed.")
    return True


def write_graph_with_hash(G: nx.DiGraph, output_path: str) -> str:
    """
    Write the graph to a GraphML file and create a sidecar hash file.

    Args:
        G: The networkx DiGraph to write.
        output_path: Path to the output .graphml file.

    Returns:
        The SHA256 hash of the written file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    nx.write_graphml(G, output_path)
    logger.info(f"Wrote graph to {output_path}")

    # Calculate and write hash
    file_hash = calculate_sha256(output_path)
    hash_path = output_path + ".hash"
    with open(hash_path, "w") as f:
        f.write(file_hash)
    logger.info(f"Wrote hash to {hash_path}: {file_hash}")

    return file_hash


def preprocess_graph(
    input_path: str,
    output_path: str,
    memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Main orchestration function to preprocess a flow file into a graph.
    Wraps graph construction with memory monitoring.

    Args:
        input_path: Path to input parquet file (T013a output).
        output_path: Path to output GraphML file.
        memory_limit_mb: Maximum allowed memory in MB.
        seed: Random seed.

    Returns:
        Metadata dictionary about the constructed graph.
    """
    scenario = os.path.splitext(os.path.basename(input_path))[0]
    # Ensure output name follows convention: graph_{scenario}_raw.graphml
    if not output_path.endswith(".graphml"):
        output_path = os.path.join(
            os.path.dirname(output_path) or ".",
            f"graph_{scenario}_raw.graphml",
        )

    if seed is None:
        seed = get_seed_value()

    logger.info(f"Starting graph construction for scenario: {scenario}")
    logger.info(f"Memory limit: {memory_limit_mb} MB")

    start_monitoring()

    try:
        G, metadata = build_graph_from_csv(
            input_path=input_path,
            output_path=output_path,
            seed=seed,
        )

        peak_mem = get_peak_memory_mb()
        logger.info(f"Peak memory usage: {peak_mem:.2f} MB")

        if peak_mem > memory_limit_mb:
            raise MemoryLimitExceededError(
                f"Peak memory {peak_mem:.2f} MB exceeded limit {memory_limit_mb} MB"
            )

        metadata["peak_memory_mb"] = peak_mem
        metadata["seed"] = seed
        metadata["memory_limit_mb"] = memory_limit_mb

        logger.info(f"Graph construction successful for {scenario}.")
        return metadata

    except MemoryLimitExceededError:
        logger.error("Memory limit exceeded during graph construction.")
        stop_monitoring()
        raise
    except Exception as e:
        logger.error(f"Error during graph construction: {e}")
        stop_monitoring()
        raise
    finally:
        stop_monitoring()


def main():
    """
    Entry point for running the graph builder from command line.
    Expects an input parquet file path as the first argument.
    """
    if len(sys.argv) < 2:
        logger.error("Usage: python preprocess.py <input_parquet_path> [output_path]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)

    if output_file is None:
        # Derive output path
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(OUTPUT_DIR, f"graph_{base_name}_raw.graphml")

    try:
        meta = preprocess_graph(input_file, output_file)
        logger.info("Preprocessing completed successfully.")
        logger.info(f"Metadata: {meta}")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()