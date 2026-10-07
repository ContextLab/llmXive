import os
import sys
import logging
import json
import hashlib
import networkx as nx
from typing import Optional, Tuple, Dict, Any

from utils.seed import set_seed
from utils.memory_monitor import enforce_memory_limit, get_peak_memory_mb

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_graph_safe(graph_path: str) -> nx.DiGraph:
    """
    Safely load a graph from a GraphML file.
    
    Args:
        graph_path: Path to the GraphML file.
        
    Returns:
        networkx.DiGraph object.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        nx.NetworkXError: If the file is invalid.
    """
    if not os.path.exists(graph_path):
        raise FileNotFoundError(f"Graph file not found: {graph_path}")
    
    logger.info(f"Loading graph from {graph_path}")
    try:
        # Use DiGraph to preserve directionality as per task T013b
        G = nx.read_graphml(graph_path, node_type=str)
        logger.info(f"Successfully loaded graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        return G
    except Exception as e:
        logger.error(f"Failed to load graph from {graph_path}: {e}")
        raise

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def write_graph_with_hash(graph: nx.DiGraph, output_path: str) -> str:
    """
    Write graph to GraphML and create a sidecar hash file.
    
    Args:
        graph: The graph to write.
        output_path: Path for the output GraphML file.
        
    Returns:
        The calculated SHA256 hash string.
    """
    logger.info(f"Writing graph to {output_path}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write graph
    nx.write_graphml(graph, output_path)
    
    # Calculate hash
    file_hash = calculate_sha256(output_path)
    
    # Write hash sidecar
    hash_path = output_path + ".hash"
    with open(hash_path, "w") as f:
        f.write(file_hash)
    
    logger.info(f"Graph written to {output_path} with hash {file_hash}")
    return file_hash

def extract_lcc(raw_graph_path: str, output_path: str, seed: int = 42) -> str:
    """
    Extract the Largest Connected Component (LCC) from a directed graph.
    
    For directed graphs, we treat the graph as undirected to find the largest
    weakly connected component.
    
    Args:
        raw_graph_path: Path to the input raw graph (GraphML).
        output_path: Path to write the LCC graph (GraphML).
        seed: Random seed for deterministic tie-breaking if needed.
        
    Returns:
        The SHA256 hash of the output file.
        
    Note:
        This task implements T008a: LCC Extraction.
        It is a helper invoked by T008d (Subsampling Orchestration).
    """
    set_seed(seed)
    
    logger.info(f"Starting LCC extraction from {raw_graph_path}")
    
    # Load the raw graph
    G_raw = load_graph_safe(raw_graph_path)
    
    if G_raw.number_of_nodes() == 0:
        raise ValueError("Input graph is empty. Cannot extract LCC.")
    
    # Convert to undirected to find weakly connected components
    G_undirected = G_raw.to_undirected()
    
    # Find all weakly connected components
    try:
        components = list(nx.weakly_connected_components(G_raw))
    except Exception as e:
        logger.error(f"Failed to find connected components: {e}")
        raise
    
    if not components:
        raise ValueError("No connected components found in the graph.")
    
    # Identify the largest component
    lcc_nodes = max(components, key=len)
    lcc_size = len(lcc_nodes)
    total_nodes = G_raw.number_of_nodes()
    
    logger.info(f"Total nodes: {total_nodes}, LCC nodes: {lcc_size} ({100.0 * lcc_size / total_nodes:.2f}%)")
    
    # Extract the subgraph
    G_lcc = G_raw.subgraph(lcc_nodes).copy()
    
    # Write the LCC graph with hash
    hash_val = write_graph_with_hash(G_lcc, output_path)
    
    logger.info(f"LCC extraction complete. Output: {output_path}")
    return hash_val

def degree_based_subsample(input_graph_path: str, output_path: str, target_nodes: int = 5000, seed: int = 42) -> str:
    """
    Perform degree-based subsampling if the graph is still too large after LCC.
    
    Retains nodes with the highest degree centrality.
    Tie-breaking: Sort by degree (desc), then by IP string (asc).
    
    Args:
        input_graph_path: Path to the input graph (usually LCC).
        output_path: Path to write the subsampled graph.
        target_nodes: Maximum number of nodes to retain.
        seed: Random seed for determinism.
        
    Returns:
        The SHA256 hash of the output file.
        
    Note:
        This task implements T008b: Degree-Based Subsampling.
        It is a helper invoked by T008d.
    """
    set_seed(seed)
    
    logger.info(f"Starting degree-based subsampling from {input_graph_path} (target: {target_nodes} nodes)")
    
    G_in = load_graph_safe(input_graph_path)
    
    if G_in.number_of_nodes() <= target_nodes:
        logger.info(f"Graph already has {G_in.number_of_nodes()} nodes, which is <= {target_nodes}. Copying to output.")
        # Just copy the file if no subsampling needed
        hash_val = write_graph_with_hash(G_in, output_path)
        return hash_val
    
    # Calculate degree for all nodes
    # For directed graphs, we consider total degree (in + out) for centrality
    degrees = G_in.degree()
    degree_dict = dict(degrees)
    
    # Sort nodes:
    # 1. By degree descending
    # 2. By node ID (IP string) ascending for tie-breaking
    sorted_nodes = sorted(
        degree_dict.keys(),
        key=lambda x: (-degree_dict[x], x)
    )
    
    # Select top nodes
    selected_nodes = set(sorted_nodes[:target_nodes])
    
    logger.info(f"Selected {len(selected_nodes)} nodes based on degree centrality.")
    
    # Extract subgraph
    G_sub = G_in.subgraph(selected_nodes).copy()
    
    # Write output
    hash_val = write_graph_with_hash(G_sub, output_path)
    
    logger.info(f"Degree-based subsampling complete. Output: {output_path}")
    return hash_val

def run_subsampling_orchestration(raw_graph_path: str, lcc_output_path: str, final_output_path: str, target_nodes: int = 5000, seed: int = 42) -> Dict[str, Any]:
    """
    Orchestrate the full subsampling flow: LCC -> Degree Subsampling.
    
    Logic:
    1. Check if node_count > 5000.
    2. If yes, extract LCC.
    3. If LCC node_count > 5000, perform degree-based subsampling.
    4. Write final graph.
    
    Args:
        raw_graph_path: Path to the raw graph.
        lcc_output_path: Path to write the LCC graph.
        final_output_path: Path to write the final subsampled graph.
        target_nodes: Maximum allowed nodes (default 5000).
        seed: Random seed.
        
    Returns:
        Dictionary with status and file paths.
        
    Note:
        This implements T008d: Subsampling Orchestration.
    """
    set_seed(seed)
    
    logger.info(f"Starting subsampling orchestration for {raw_graph_path}")
    
    G_raw = load_graph_safe(raw_graph_path)
    initial_nodes = G_raw.number_of_nodes()
    
    result = {
        "input_file": raw_graph_path,
        "initial_nodes": initial_nodes,
        "target_nodes": target_nodes,
        "steps": []
    }
    
    if initial_nodes <= target_nodes:
        logger.info(f"Graph has {initial_nodes} nodes (<= {target_nodes}). No subsampling needed.")
        write_graph_with_hash(G_raw, final_output_path)
        result["final_file"] = final_output_path
        result["final_nodes"] = initial_nodes
        result["status"] = "no_subsampling_needed"
        return result
    
    # Step 1: Extract LCC
    logger.info(f"Graph exceeds {target_nodes} nodes. Extracting LCC...")
    extract_lcc(raw_graph_path, lcc_output_path, seed)
    result["steps"].append({"step": "lcc_extraction", "output": lcc_output_path})
    
    G_lcc = load_graph_safe(lcc_output_path)
    lcc_nodes = G_lcc.number_of_nodes()
    result["lcc_nodes"] = lcc_nodes
    
    if lcc_nodes <= target_nodes:
        logger.info(f"LCC has {lcc_nodes} nodes (<= {target_nodes}). Using LCC as final.")
        # Copy LCC to final output
        write_graph_with_hash(G_lcc, final_output_path)
        result["final_file"] = final_output_path
        result["final_nodes"] = lcc_nodes
        result["status"] = "lcc_sufficient"
        return result
    
    # Step 2: Degree-based subsampling
    logger.info(f"LCC exceeds {target_nodes} nodes. Performing degree-based subsampling...")
    degree_based_subsample(lcc_output_path, final_output_path, target_nodes, seed)
    result["steps"].append({"step": "degree_subsampling", "output": final_output_path})
    
    G_final = load_graph_safe(final_output_path)
    result["final_nodes"] = G_final.number_of_nodes()
    result["final_file"] = final_output_path
    result["status"] = "subsampled"
    
    logger.info(f"Orchestration complete. Final nodes: {result['final_nodes']}")
    return result

def main():
    """
    Main entry point for T008a (LCC Extraction) and orchestration.
    This script can be called directly to process a specific scenario or
    invoked by the orchestrator logic.
    
    Usage:
        python code/data/subsample_orchestrator.py --input <path> --output <path> --mode lcc|subsample|orchestrate
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Graph Subsampling and LCC Extraction")
    parser.add_argument("--input", type=str, required=True, help="Path to input raw graph")
    parser.add_argument("--output", type=str, required=True, help="Path to output graph")
    parser.add_argument("--lcc-output", type=str, default=None, help="Path to intermediate LCC graph (required for orchestrate mode)")
    parser.add_argument("--mode", type=str, choices=["lcc", "subsample", "orchestrate"], default="lcc", help="Operation mode")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--target-nodes", type=int, default=5000, help="Target node count for subsampling")
    
    args = parser.parse_args()
    
    try:
        if args.mode == "lcc":
            hash_val = extract_lcc(args.input, args.output, args.seed)
            print(f"LCC extracted. Hash: {hash_val}")
        elif args.mode == "subsample":
            hash_val = degree_based_subsample(args.input, args.output, args.target_nodes, args.seed)
            print(f"Subsampling complete. Hash: {hash_val}")
        elif args.mode == "orchestrate":
            if not args.lcc_output:
                raise ValueError("--lcc-output is required for orchestrate mode")
            result = run_subsampling_orchestration(
                args.input, args.lcc_output, args.output, args.target_nodes, args.seed
            )
            print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Error during execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()