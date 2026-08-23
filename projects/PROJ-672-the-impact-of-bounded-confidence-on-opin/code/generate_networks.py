import os
import json
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
import networkx as nx

def set_global_seed(seed: int) -> None:
    """Set global random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    if hasattr(os, 'setenv'):
        os.environ['PYTHONHASHSEED'] = str(seed)

def generate_erdos_renyi(n: int, p: float, seed: int) -> nx.Graph:
    """Generate an Erdős-Rényi random graph."""
    set_global_seed(seed)
    G = nx.erdos_renyi_graph(n, p, seed=seed)
    return G

def generate_barabasi_albert(n: int, m: int, seed: int) -> nx.Graph:
    """Generate a Barabási-Albert scale-free network."""
    set_global_seed(seed)
    # Ensure m < n
    m = min(m, n - 1)
    G = nx.barabasi_albert_graph(n, m, seed=seed)
    return G

def generate_watts_strogatz(n: int, k: int, p: float, seed: int) -> nx.Graph:
    """Generate a Watts-Strogatz small-world network."""
    set_global_seed(seed)
    # Ensure k is even and k < n
    if k % 2 != 0:
        k += 1
    k = min(k, n - 1)
    G = nx.watts_strogatz_graph(n, k, p, seed=seed)
    return G

def ensure_connected(G: nx.Graph, strategy: str = "largest") -> nx.Graph:
    """
    Ensure the graph is connected.
    
    Strategy:
    - 'largest': Keep only the largest connected component and re-index nodes.
    - 'bridge': Add minimal edges to connect components (not implemented yet, raises NotImplementedError).
    
    Returns a new connected graph.
    """
    if nx.is_connected(G):
        return G.copy()
    
    if strategy == "largest":
        components = list(nx.connected_components(G))
        if not components:
            raise ValueError("Graph has no nodes.")
        
        largest_comp = max(components, key=len)
        H = G.subgraph(largest_comp).copy()
        
        # Re-index nodes to 0..N-1 to maintain consistency with simulation expectations
        mapping = {old: new for new, old in enumerate(H.nodes())}
        H = nx.relabel_nodes(H, mapping)
        
        return H
    
    elif strategy == "bridge":
        raise NotImplementedError("Bridge strategy not yet implemented.")
    
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

def save_network(G: nx.Graph, filepath: Path, seed: int, topology: str) -> None:
    """Save a network instance to a GraphML file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    G.graph['seed'] = seed
    G.graph['topology'] = topology
    nx.write_graphml(G, filepath)

def save_manifest(manifest_path: Path, networks: List[Dict[str, Any]]) -> None:
    """Save a manifest of all generated networks."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, 'w') as f:
        json.dump(networks, f, indent=2)

def main():
    """Main entry point for network generation with connectivity validation."""
    # Configuration
    output_dir = Path("data/raw/networks")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parameters
    n_nodes = 500
    seeds = list(range(10))  # Generate 10 instances per topology
    
    topology_configs = [
        {"type": "er", "generator": generate_erdos_renyi, "params": {"p": 0.01}},
        {"type": "ba", "generator": generate_barabasi_albert, "params": {"m": 3}},
        {"type": "ws", "generator": generate_watts_strogatz, "params": {"k": 4, "p": 0.1}},
    ]
    
    manifest_data = []
    
    for config in topology_configs:
        print(f"Generating {config['type']} networks...")
        for seed in seeds:
            try:
                # Generate
                G = config["generator"](n_nodes, **config["params"], seed=seed)
                
                # Validate Connectivity (T015)
                # If disconnected, ensure it becomes connected via largest component
                original_nodes = G.number_of_nodes()
                G_connected = ensure_connected(G, strategy="largest")
                new_nodes = G_connected.number_of_nodes()
                
                if new_nodes < original_nodes:
                    print(f"  Seed {seed}: Disconnected ({original_nodes} nodes). "
                          f"Kept largest component ({new_nodes} nodes).")
                
                # Save
                filename = f"{config['type']}_seed_{seed}.graphml"
                filepath = output_dir / filename
                save_network(G_connected, filepath, seed, config['type'])
                
                # Record in manifest
                manifest_data.append({
                    "filename": filename,
                    "topology": config['type'],
                    "seed": seed,
                    "nodes": new_nodes,
                    "edges": G_connected.number_of_edges(),
                    "connected": True,
                    "reduced": new_nodes < original_nodes
                })
                
            except Exception as e:
                print(f"  Error generating seed {seed}: {e}")
                raise
    
    # Save Manifest
    manifest_path = output_dir / "manifest.json"
    save_manifest(manifest_path, manifest_data)
    print(f"Manifest saved to {manifest_path}")

if __name__ == "__main__":
    main()
