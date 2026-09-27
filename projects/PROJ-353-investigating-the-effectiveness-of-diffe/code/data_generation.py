"""
Synthetic Graph Generation for Small-World Network Study.

Generates N=110 Watts-Strogatz graphs with varying rewiring probabilities (beta)
from 0.0 to 1.0, annotates nodes with community labels derived from the initial
ring lattice, and saves the results to data/raw/graphs.jsonl.
"""
import json
import os
import random
from pathlib import Path

import networkx as nx
import numpy as np

from utils import SAMPLE_SIZE, seed_all

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
N_NODES: int = 11
K_NEIGHBORS: int = 2
BETA_LEVELS: list[float] = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
GRAPHS_PER_BETA: int = 10

OUTPUT_PATH: Path = Path("data/raw/graphs.jsonl")

# ----------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------
def generate_watts_strogatz_graph(beta: float, seed: int) -> nx.Graph:
    """
    Generate a Watts-Strogatz graph.

    Args:
        beta: Rewiring probability (0.0 to 1.0).
        seed: Random seed for reproducibility.

    Returns:
        NetworkX Graph object.
    """
    # Ensure seed is applied before generation
    random.seed(seed)
    np.random.seed(seed)

    # Create the initial ring lattice
    # n=11, k=2 (each node connected to 2 nearest neighbors on each side)
    G = nx.WattsStrogatz_graph(n=N_NODES, k=K_NEIGHBORS, p=beta, seed=seed)
    return G

def derive_community_labels(G: nx.Graph) -> dict[int, int]:
    """
    Derive community labels from the initial ring lattice structure.
    
    Since the graph is generated from a ring lattice, nodes are naturally
    ordered 0..N-1. We assign labels based on position in the ring.
    For a simple ring of 11 nodes, we can assign labels 0, 1, 2 to create
    a balanced distribution (3 groups: sizes 4, 4, 3 or similar).
    
    Args:
        G: The generated graph (node indices 0..N-1).
    
    Returns:
        Dictionary mapping node_id -> label_id.
    """
    n_nodes = len(G.nodes())
    labels = {}
    
    # Assign labels cyclically to ensure balance
    # 11 nodes -> 3 classes roughly balanced (4, 4, 3)
    for node_id in G.nodes():
        labels[node_id] = node_id % 3
        
    return labels

def compute_clustering_coefficient(G: nx.Graph) -> float:
    """
    Compute the global clustering coefficient of the graph.
    
    Args:
        G: NetworkX Graph.
    
    Returns:
        Clustering coefficient (float).
    """
    return nx.clustering_coefficient(G)

def validate_graph(G: nx.Graph, beta: float) -> bool:
    """
    Validate the generated graph.
    
    Checks:
    - No disconnected components (unless beta=1.0 where it's possible but rare for n=11)
    - Class balance < 80%
    
    Args:
        G: Graph to validate.
        beta: Rewiring probability used.
    
    Returns:
        True if valid, False otherwise.
    """
    # Check for disconnected components
    components = list(nx.connected_components(G))
    if len(components) > 1:
        # If disconnected, we might want to regenerate or skip
        # For N=11 and K=2, beta=1.0 can sometimes disconnect, but let's flag it
        # The task says "detect disconnected components (regenerate/skip)"
        # We will skip invalid graphs and try to generate more until we hit N=110
        return False

    # Check class balance
    labels = derive_community_labels(G)
    counts = {}
    for l in labels.values():
        counts[l] = counts.get(l, 0) + 1
    
    max_count = max(counts.values())
    total = sum(counts.values())
    if max_count / total >= 0.80:
        return False

    return True

# ----------------------------------------------------------------------
# Main Generation Logic
# ----------------------------------------------------------------------
def main():
    """
    Generate N=110 graphs and save to data/raw/graphs.jsonl.
    """
    # Verify Sample Size constraint
    if SAMPLE_SIZE != 110:
        raise ValueError(f"Spec constraint violated: SAMPLE_SIZE must be 110, got {SAMPLE_SIZE}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    graphs_data = []
    generated_count = 0
    attempts_per_beta = 20  # Allow some retries for invalid graphs

    print(f"Starting generation for N={SAMPLE_SIZE} graphs...")
    
    # We need 10 graphs per beta level for 11 levels = 110 total
    # We will iterate through beta levels and generate 10 valid graphs for each
    for beta in BETA_LEVELS:
        count_for_beta = 0
        attempts = 0
        
        while count_for_beta < GRAPHS_PER_BETA and attempts < attempts_per_beta:
            # Generate a seed based on beta level and attempt number
            # Use a deterministic seed sequence
            seed_val = int(beta * 1000) + attempts
            seed_all(seed_val)
            
            G = generate_watts_strogatz_graph(beta, seed_val)
            
            if validate_graph(G, beta):
                # Compute metrics
                clustering = compute_clustering_coefficient(G)
                labels = derive_community_labels(G)
                
                # Convert graph to edge list
                edge_list = list(G.edges())
                
                # Create data record
                record = {
                    "id": f"graph_{beta}_{count_for_beta}",
                    "beta": beta,
                    "seed": seed_val,
                    "clustering_coeff": clustering,
                    "node_count": len(G.nodes()),
                    "edge_list": edge_list,
                    "labels": labels
                }
                
                graphs_data.append(record)
                count_for_beta += 1
                generated_count += 1
                print(f"Generated valid graph for beta={beta} (#{count_for_beta})")
            else:
                attempts += 1
                print(f"Invalid graph for beta={beta} (attempt {attempts}), retrying...")
        
        if count_for_beta < GRAPHS_PER_BETA:
            raise RuntimeError(f"Failed to generate {GRAPHS_PER_BETA} valid graphs for beta={beta}. Only got {count_for_beta}.")

    # Final check
    if generated_count != SAMPLE_SIZE:
        raise RuntimeError(f"Generation failed: Expected {SAMPLE_SIZE} graphs, got {generated_count}.")

    print(f"Successfully generated {generated_count} graphs.")

    # Save to JSONL
    with open(OUTPUT_PATH, "w") as f:
        for record in graphs_data:
            f.write(json.dumps(record) + "\n")

    print(f"Graphs saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
