import os
import sys
import logging
import hashlib
import tracemalloc
import random
import networkx as nx
import pandas as pd
from typing import Optional, Tuple, Dict, Any

from utils.seed import set_seed, get_seed_value
from utils.memory_monitor import enforce_memory_limit, MemoryLimitExceededError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def build_graph_from_csv(csv_path: str) -> nx.Graph:
    """
    Build a directed graph from a CSV of netflow records.
    Nodes are IPs, edges are flows. Edge weight is packet count.
    """
    logger.info(f"Building graph from {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Ensure required columns exist
    required_cols = ['src_ip', 'dst_ip', 'packets']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    G = nx.Graph()
    
    # Add edges with attributes
    for _, row in df.iterrows():
        src = str(row['src_ip'])
        dst = str(row['dst_ip'])
        weight = int(row['packets'])
        
        if weight < 0:
            logger.warning(f"Negative packet count found at row {_, src, dst}, setting to 0")
            weight = 0
      
        G.add_edge(src, dst, weight=weight, packet_count=weight)
        
        # Ensure nodes have attributes if needed (e.g., label if present)
        if 'label' in df.columns:
            label = row['label']
            if src not in G.nodes:
                G.nodes[src]['label'] = label
            if dst not in G.nodes:
                G.nodes[dst]['label'] = label
    
    logger.info(f"Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G

def extract_lcc(G: nx.Graph) -> nx.Graph:
    """Extract the Largest Connected Component."""
    logger.info("Extracting Largest Connected Component (LCC)")
    if nx.is_connected(G):
        logger.info("Graph is already connected.")
        return G.copy()
    
    largest_cc = max(nx.connected_components(G), key=len)
    lcc_graph = G.subgraph(largest_cc).copy()
    logger.info(f"LCC extracted: {lcc_graph.number_of_nodes()} nodes, {lcc_graph.number_of_edges()} edges")
    return lcc_graph

def subsample_graph(G: nx.Graph, max_nodes: int = 5000) -> nx.Graph:
    """
    Subsample graph to max_nodes using degree centrality.
    Tie-breaking: sort by degree desc, then by IP string asc.
    """
    if G.number_of_nodes() <= max_nodes:
        logger.info(f"Graph has {G.number_of_nodes()} nodes, no subsampling needed.")
        return G.copy()
    
    logger.info(f"Subsampling graph from {G.number_of_nodes()} to {max_nodes} nodes by degree.")
    
    # Calculate degree
    degrees = dict(G.degree())
    
    # Sort nodes: primary by degree (desc), secondary by IP string (asc)
    sorted_nodes = sorted(degrees.items(), key=lambda x: (-x[1], x[0]))
    
    # Select top N nodes
    top_nodes = [node for node, _ in sorted_nodes[:max_nodes]]
    
    # Create subgraph
    subsampled = G.subgraph(top_nodes).copy()
    logger.info(f"Subsampled graph: {subsampled.number_of_nodes()} nodes, {subsampled.number_of_edges()} edges")
    return subsampled

def validate_graph(G: nx.Graph) -> bool:
    """Validate graph properties: non-negative weights, no missing labels if expected."""
    logger.info("Validating graph...")
    for u, v, data in G.edges(data=True):
        if 'weight' in data and data['weight'] < 0:
            logger.error(f"Negative weight found on edge ({u}, {v})")
            return False
    logger.info("Graph validation passed.")
    return True

def write_graph_with_hash(G: nx.Graph, output_path: str) -> str:
    """
    Write graph to GraphML and create a sidecar .hash file with SHA256.
    Returns the hash string.
    """
    logger.info(f"Writing graph to {output_path}")
    nx.write_graphml(G, output_path)
    
    # Calculate hash
    file_hash = calculate_sha256(output_path)
    
    # Write sidecar
    hash_path = output_path + ".hash"
    with open(hash_path, 'w') as f:
        f.write(file_hash)
    
    logger.info(f"Graph written. SHA256: {file_hash}")
    logger.info(f"Hash sidecar written to {hash_path}")
    return file_hash

def preprocess_graph(input_csv: str, scenario: str, max_nodes: int = 5000) -> Dict[str, str]:
    """
    Full preprocessing pipeline:
    1. Build graph from CSV
    2. Extract LCC if needed
    3. Subsample if needed
    4. Validate
    5. Write to GraphML with hash sidecar
    
    Returns a dict of output paths.
    """
    set_seed(get_seed_value()) # Ensure deterministic behavior
    
    raw_path = f"data/processed/graph_{scenario}_raw.graphml"
    lcc_path = f"data/processed/graph_{scenario}_lcc.graphml"
    final_path = f"data/processed/graph_{scenario}_subsampled.graphml"
    
    # 1. Build Raw Graph
    G = build_graph_from_csv(input_csv)
    write_graph_with_hash(G, raw_path)
    
    # 2. Check constraints
    needs_lcc = G.number_of_nodes() > max_nodes
    if needs_lcc:
        G = extract_lcc(G)
        write_graph_with_hash(G, lcc_path)
    
    # 3. Subsample if still too large
    if G.number_of_nodes() > max_nodes:
        G = subsample_graph(G, max_nodes)
    else:
        # If LCC was small enough, we might not need a new file, but task T017 implies
        # writing the final subsampled artifact. If no subsampling happened, 
        # we can copy the LCC or Raw to the final path to ensure the artifact exists.
        # To be safe and consistent with the flow, we write the current state to final_path.
        pass
    
    # 4. Validate
    if not validate_graph(G):
        raise ValueError("Graph validation failed after processing.")
    
    # 5. Write Final
    final_hash = write_graph_with_hash(G, final_path)
    
    return {
        "raw": raw_path,
        "lcc": lcc_path if needs_lcc else None,
        "final": final_path,
        "hash": final_hash
    }

def main():
    """
    CLI entry point for preprocess_graph.
    Expects arguments: input_csv scenario
    """
    if len(sys.argv) < 3:
        logger.error("Usage: python preprocess.py <input_csv> <scenario>")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    scenario = sys.argv[2]
    
    if not os.path.exists(input_csv):
        logger.error(f"Input file not found: {input_csv}")
        sys.exit(1)
    
    try:
        results = preprocess_graph(input_csv, scenario)
        logger.info(f"Preprocessing complete. Final artifact: {results['final']}")
    except MemoryLimitExceededError as e:
        logger.error(f"Memory limit exceeded: {e}")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Error during preprocessing: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()