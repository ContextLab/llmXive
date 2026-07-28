import os
import json
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
import networkx as nx
from utils.metrics import calculate_structural_metrics

# Global seed for reproducibility
_global_seed = 42
np.random.seed(_global_seed)
random.seed(_global_seed)

def set_global_seed(seed: int) -> None:
    """Set the global random seed for reproducibility."""
    global _global_seed
    _global_seed = seed
    np.random.seed(seed)
    random.seed(seed)

def generate_erdos_renyi(n: int, p: float, seed: Optional[int] = None) -> nx.Graph:
    """
    Generate an Erdős-Rényi random graph.

    Args:
        n: Number of nodes.
        p: Probability of edge creation.
        seed: Random seed for this specific generation.

    Returns:
        A NetworkX Graph.
    """
    if seed is not None:
        local_rng = np.random.default_rng(seed)
        # NetworkX's nx.erdos_renyi_graph uses numpy's global state or a passed seed
        # We pass the seed directly to ensure isolation if called in parallel
        return nx.erdos_renyi_graph(n, p, seed=seed)
    return nx.erdos_renyi_graph(n, p)

def generate_barabasi_albert(n: int, m: int, seed: Optional[int] = None) -> nx.Graph:
    """
    Generate a Barabási-Albert scale-free network.

    Args:
        n: Number of nodes.
        m: Number of edges to attach from a new node to existing nodes.
        seed: Random seed.

    Returns:
        A NetworkX Graph.
    """
    if seed is not None:
        return nx.barabasi_albert_graph(n, m, seed=seed)
    return nx.barabasi_albert_graph(n, m)

def generate_watts_strogatz(n: int, k: int, p: float, seed: Optional[int] = None) -> nx.Graph:
    """
    Generate a Watts-Strogatz small-world network.

    Args:
        n: Number of nodes.
        k: Each node is joined with its k nearest neighbors in a ring lattice.
        p: Probability of rewiring each edge.
        seed: Random seed.

    Returns:
        A NetworkX Graph.
    """
    if seed is not None:
        return nx.watts_strogatz_graph(n, k, p, seed=seed)
    return nx.watts_strogatz_graph(n, k, p)

def ensure_connected(graph: nx.Graph, max_attempts: int = 100) -> Optional[nx.Graph]:
    """
    Ensure the graph is connected by reconnecting isolated components if necessary.

    If the graph is not connected, we attempt to connect the largest connected
    component to other components by adding edges until the graph is connected.
    If max_attempts is reached without success, we return None to signal failure.

    Args:
        graph: The input NetworkX graph.
        max_attempts: Maximum number of edge addition attempts.

    Returns:
        A connected NetworkX graph, or None if it could not be connected.
    """
    if nx.is_connected(graph):
        return graph

    # Identify connected components
    components = list(nx.connected_components(graph))
    if len(components) <= 1:
        return graph

    # Sort components by size (largest first)
    components.sort(key=len, reverse=True)
    main_component = components[0]
    other_components = components[1:]

    attempts = 0
    for other in other_components:
        if attempts >= max_attempts:
            return None
        # Pick a random node from the main component and the other component
        node_main = random.choice(list(main_component))
        node_other = random.choice(list(other))
        
        # Add edge
        graph.add_edge(node_main, node_other)
        attempts += 1

        # Re-check connectivity
        if nx.is_connected(graph):
            return graph

    # Final check
    if nx.is_connected(graph):
        return graph
    
    return None

def save_network(graph: nx.Graph, metrics: Dict[str, Any], output_dir: Path, seed: int) -> Dict[str, str]:
    """
    Save a network instance and its metrics to disk.

    Args:
        graph: The NetworkX graph.
        metrics: Dictionary of structural metrics.
        output_dir: Directory to save files.
        seed: The seed used to generate this network.

    Returns:
        Dictionary with file paths and checksums.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save graph as GraphML
    graph_path = output_dir / f"network_{seed}.graphml"
    nx.write_graphml(graph, str(graph_path))
    
    # Save metrics as JSON
    metrics_path = output_dir / f"metrics_{seed}.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    return {
        "graph_path": str(graph_path),
        "metrics_path": str(metrics_path)
    }

def save_manifest(manifest: List[Dict[str, Any]], output_dir: Path) -> str:
    """
    Save the manifest of all generated networks.

    Args:
        manifest: List of network metadata dictionaries.
        output_dir: Directory to save the manifest.

    Returns:
        Path to the manifest file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    return str(manifest_path)

def main():
    """
    Main entry point to generate network ensembles.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate network ensembles")
    parser.add_argument("--topology", type=str, required=True, 
                      choices=["er", "ba", "ws"],
                      help="Topology type: er (Erdos-Renyi), ba (Barabasi-Albert), ws (Watts-Strogatz)")
    parser.add_argument("--n", type=int, default=500, help="Number of nodes")
    parser.add_argument("--count", type=int, default=50, help="Number of instances to generate")
    parser.add_argument("--output-dir", type=str, default="data/raw/networks", help="Output directory")
    parser.add_argument("--seed-start", type=int, default=42, help="Starting seed")
    parser.add_argument("--p-er", type=float, default=0.01, help="Edge probability for ER")
    parser.add_argument("--m-ba", type=int, default=3, help="Edges to attach for BA")
    parser.add_argument("--k-ws", type=int, default=5, help="Neighbors for WS")
    parser.add_argument("--p-ws", type=float, default=0.1, help="Rewiring probability for WS")
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    manifest = []
    
    print(f"Generating {args.count} {args.topology} networks with N={args.n}...")
    
    for i in range(args.count):
        seed = args.seed_start + i
        np.random.seed(seed)
        random.seed(seed)
        
        try:
            if args.topology == "er":
                graph = generate_erdos_renyi(args.n, args.p_er, seed=seed)
            elif args.topology == "ba":
                graph = generate_barabasi_albert(args.n, args.m_ba, seed=seed)
            elif args.topology == "ws":
                graph = generate_watts_strogatz(args.n, args.k_ws, args.p_ws, seed=seed)
            else:
                raise ValueError(f"Unknown topology: {args.topology}")
            
            # Ensure connectivity
            connected_graph = ensure_connected(graph)
            if connected_graph is None:
                print(f"Warning: Could not connect network for seed {seed}. Skipping.")
                continue
            
            # Calculate metrics
            metrics = calculate_structural_metrics(connected_graph)
            metrics['seed'] = seed
            metrics['topology'] = args.topology
            metrics['is_connected'] = True
            
            # Save
            file_paths = save_network(connected_graph, metrics, output_dir, seed)
            
            manifest.append({
                "seed": seed,
                "topology": args.topology,
                "n": args.n,
                "file_paths": file_paths,
                "metrics": metrics
            })
            
            print(f"Generated network {i+1}/{args.count} (seed={seed})")
            
        except Exception as e:
            print(f"Error generating network for seed {seed}: {e}")
            continue
    
    # Save manifest
    if manifest:
        manifest_path = save_manifest(manifest, output_dir)
        print(f"Manifest saved to {manifest_path}")
    else:
        print("No networks were generated.")

if __name__ == "__main__":
    main()