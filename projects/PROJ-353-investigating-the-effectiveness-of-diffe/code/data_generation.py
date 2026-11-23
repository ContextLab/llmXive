import json
import os
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple

import networkx as nx
import numpy as np

from utils import seed_all, hash_artifact, SAMPLE_SIZE, MAX_EPOCHS

# Explicit beta levels as required: 0.0, 0.1, ..., 1.0
BETA_LEVELS = [i * 0.1 for i in range(11)]
GRAPHS_PER_BETA = 10
TOTAL_GRAPHS = len(BETA_LEVELS) * GRAPHS_PER_BETA
NODE_COUNT = 20  # Fixed node count for Watts-Strogatz to ensure manageable size
K_NEIGHBORS = 4  # Each node connected to 2k neighbors initially (k=2)

def generate_watts_strogatz_graph(beta: float, seed: int, n_nodes: int = NODE_COUNT, k: int = K_NEIGHBORS) -> nx.Graph:
    """
    Generate a Watts-Strogatz graph with the given beta (rewiring probability).
    Uses the initial ring lattice structure to derive community labels.
    """
    seed_all(seed)
    # Generate the initial ring lattice
    # Note: We use the seed to ensure reproducibility of the random process
    G = nx.watts_strogatz_graph(n=n_nodes, k=k, p=beta, seed=seed)
    return G

def derive_community_labels(G: nx.Graph, n_nodes: int = NODE_COUNT, k: int = K_NEIGHBORS) -> np.ndarray:
    """
    Derive community labels from the initial ring lattice structure.
    Since the initial lattice is a ring where each node is connected to its k nearest neighbors,
    we can assign labels based on the node's position in the ring.
    For simplicity, we divide the ring into communities based on node indices.
    Here, we assume 4 communities for a ring of 20 nodes (5 nodes per community).
    """
    labels = np.zeros(n_nodes, dtype=int)
    community_size = n_nodes // 4
    for i in range(n_nodes):
        labels[i] = i // community_size
    return labels

def compute_clustering_coefficient(G: nx.Graph) -> float:
    """Compute the average clustering coefficient of the graph."""
    return nx.average_clustering(G)

def validate_graph(G: nx.Graph) -> bool:
    """
    Validate that the graph is connected and has the expected number of nodes.
    Returns True if valid, False otherwise.
    """
    if not nx.is_connected(G):
        return False
    if len(G.nodes()) != NODE_COUNT:
        return False
    # Additional check: transitivity > 0.0 (as per task requirement)
    if nx.transitivity(G) <= 0.0:
        return False
    return True

def main():
    """
    Main function to generate the graph dataset.
    - Generates exactly 10 graphs per beta level (0.0 to 1.0).
    - Validates connectivity and regenerates if disconnected.
    - Enforces class balance (<80% max).
    - Saves to data/raw/graphs.jsonl.
    - Records checksum in state/projects/PROJ-353-investigating-the-effectiveness-of-diffe.yaml.
    """
    seed_all(42)  # Global seed for reproducibility

    data_dir = Path("data/raw")
    data_dir.mkdir(parents=True, exist_ok=True)

    output_path = data_dir / "graphs.jsonl"
    graphs_data = []

    max_retries = 1000

    # Track generation stats for verification
    beta_counts = {beta: 0 for beta in BETA_LEVELS}

    for beta in BETA_LEVELS:
        valid_graphs_for_beta = 0
        attempts = 0

        while valid_graphs_for_beta < GRAPHS_PER_BETA:
            if attempts >= max_retries:
                print(f"WARNING: Failed to generate {GRAPHS_PER_BETA} valid connected graphs for beta={beta} after {max_retries} attempts. Proceeding with valid subset ({valid_graphs_for_beta}).")
                break

            seed = random.randint(0, 10**9)
            G = generate_watts_strogatz_graph(beta, seed)

            if not validate_graph(G):
                attempts += 1
                continue

            # Derive labels
            labels = derive_community_labels(G)

            # Check class balance
            unique, counts = np.unique(labels, return_counts=True)
            max_class_ratio = max(counts) / len(labels)
            if max_class_ratio >= 0.8:
                attempts += 1
                continue

            # Graph is valid and balanced
            edge_list = list(G.edges())
            clustering_coeff = compute_clustering_coefficient(G)

            graph_record = {
                "id": f"graph_{beta:.1f}_{seed}",
                "beta": beta,
                "seed": seed,
                "node_count": NODE_COUNT,
                "clustering_coeff": clustering_coeff,
                "edge_list": edge_list,
                "labels": labels.tolist(),
                "community_size": len(unique)
            }

            graphs_data.append(graph_record)
            valid_graphs_for_beta += 1
            beta_counts[beta] = valid_graphs_for_beta
            attempts += 1

    # Write to JSONL
    with open(output_path, 'w') as f:
        for record in graphs_data:
            f.write(json.dumps(record) + '\n')

    print(f"Generated {len(graphs_data)} graphs to {output_path}")

    # Verification Step 9b: Count entries per beta level
    print("\n--- Verification: Distribution per Beta Level ---")
    all_balanced = True
    for beta, count in beta_counts.items():
        status = "OK" if count == GRAPHS_PER_BETA else "UNBALANCED"
        if count != GRAPHS_PER_BETA:
            all_balanced = False
        print(f"Beta {beta:.1f}: {count} graphs ({status})")
    
    if not all_balanced:
        print("WARNING: Distribution is unbalanced. Some beta levels have fewer than 10 valid graphs.")

    # Checksum and state update
    checksum = hash_artifact(str(output_path))
    state_dir = Path("state/projects")
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "PROJ-353-investigating-the-effectiveness-of-diffe.yaml"

    # Write state file (simplified YAML)
    with open(state_file, 'w') as sf:
        sf.write("artifact_hashes:\n")
        sf.write(f"  data/raw/graphs.jsonl: {checksum}\n")

    print(f"\nChecksum recorded in {state_file}")
    print(f"SHA-256: {checksum}")

if __name__ == "__main__":
    main()
