import json
import os
import random
from pathlib import Path
import networkx as nx
import numpy as np
import hashlib
import yaml

from utils import seed_all, hash_artifact, SAMPLE_SIZE, MAX_EPOCHS
from losses import cross_entropy_loss, info_nce_loss, LinearProbe, compute_accuracy
from models import GCNLayer, GCN2Layer, create_normalized_adjacency, build_gcn_model

# Constants for generation
NUM_NODES = 100  # Fixed N for graph generation as per common small-world studies
K_NEIGHBORS = 4  # Each node connected to 2 on each side in ring lattice
BETA_LEVELS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
GRAPHS_PER_BETA = 10
MAX_RETRIES = 50

def generate_watts_strogatz_graph(beta: float, seed: int, num_nodes: int = NUM_NODES, k: int = K_NEIGHBORS):
    """
    Generate a Watts-Strogatz small-world graph.
    Returns the graph object and the original lattice structure for label derivation.
    """
    seed_all(seed)
    # Create the initial ring lattice
    G_lattice = nx.watts_strogatz_graph(n=num_nodes, k=k, p=0.0, seed=seed)
    
    # Rewire to create the small-world graph
    # We use a fresh seed for the rewiring process to ensure independence if needed,
    # but typically the seed passed controls the randomness of the whole process.
    G = nx.watts_strogatz_graph(n=num_nodes, k=k, p=beta, seed=seed)
    
    return G, G_lattice

def derive_community_labels(G_lattice, num_nodes: int = NUM_NODES):
    """
    Derive community labels from the initial ring lattice structure.
    In a ring lattice with k neighbors, we can define communities based on
    the initial connectivity before rewiring. A simple approach is to divide
    the ring into segments.
    """
    # For a ring lattice, we can define communities by dividing nodes into
    # contiguous segments. With N nodes and assuming k is even, we can
    # create communities of size roughly k+1 or based on the lattice structure.
    # A robust method: use the initial connections to find connected components
    # if the lattice was disconnected, but it's a single ring.
    # Instead, we'll assign labels based on position in the ring to simulate
    # community structure that is then disrupted by rewiring.
    # Let's create 4 communities for simplicity, dividing the ring into quarters.
    num_communities = 4
    labels = {}
    for i in range(num_nodes):
        labels[i] = (i * num_communities) // num_nodes
    return labels

def compute_clustering_coefficient(G):
    """
    Compute the global clustering coefficient of the graph.
    """
    return nx.clustering(G)

def validate_graph(G, labels, max_class_ratio=0.8):
    """
    Validate the generated graph:
    1. Check for disconnected components (should be one giant component).
    2. Check class balance (no class > max_class_ratio).
    """
    # Check connectivity
    if not nx.is_connected(G):
        return False, "Graph is not connected"
    
    # Check class balance
    if not labels:
        return False, "No labels provided"
    
    label_counts = {}
    for label in labels.values():
        label_counts[label] = label_counts.get(label, 0) + 1
    
    total_nodes = sum(label_counts.values())
    max_count = max(label_counts.values())
    
    if max_count / total_nodes > max_class_ratio:
        return False, f"Class imbalance detected: max ratio {max_count/total_nodes:.2f}"
    
    return True, "Valid"

def main():
    """
    Main function to generate the dataset of small-world graphs.
    """
    # Ensure directories exist
    data_dir = Path("data/raw")
    data_dir.mkdir(parents=True, exist_ok=True)
    state_dir = Path("state/projects/PROJ-353-investigating-the-effectiveness-of-diffe")
    state_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = data_dir / "graphs.jsonl"
    state_file = state_dir / "state.yaml"
    
    # Initialize seed
    seed_all(42)
    
    graphs_data = []
    generated_count = 0
    
    print(f"Generating {SAMPLE_SIZE} graphs...")
    
    # We need to generate SAMPLE_SIZE graphs.
    # According to task: 10 graphs per beta level (11 levels) = 110 graphs.
    # This matches SAMPLE_SIZE = 110.
    
    beta_indices = []
    for beta in BETA_LEVELS:
        for _ in range(GRAPHS_PER_BETA):
            beta_indices.append(beta)
    
    if len(beta_indices) != SAMPLE_SIZE:
        raise ValueError(f"Expected {SAMPLE_SIZE} graphs, but beta_levels * graphs_per_beta = {len(beta_indices)}")
    
    for idx, beta in enumerate(beta_indices):
        seed = 42 + idx  # Unique seed for each graph
        success = False
        for retry in range(MAX_RETRIES):
            try:
                G, G_lattice = generate_watts_strogatz_graph(beta, seed)
                labels = derive_community_labels(G_lattice)
                
                is_valid, msg = validate_graph(G, labels)
                if is_valid:
                    success = True
                    break
                else:
                    # Retry with a different seed if validation fails
                    seed += 1
            except Exception as e:
                print(f"Error generating graph {idx}: {e}")
                seed += 1
                continue
        
        if not success:
            raise RuntimeError(f"Failed to generate valid graph for beta={beta} after {MAX_RETRIES} retries")
        
        # Compute clustering coefficient
        clustering_coeff = nx.clustering(G)
        
        # Prepare data for serialization
        graph_entry = {
            "id": f"graph_{idx:03d}",
            "beta": beta,
            "seed": seed,
            "clustering_coeff": clustering_coeff,
            "num_nodes": G.number_of_nodes(),
            "num_edges": G.number_of_edges(),
            "edge_list": list(G.edges()),
            "labels": labels,
            "is_connected": nx.is_connected(G)
        }
        
        graphs_data.append(graph_entry)
        generated_count += 1
        print(f"Generated graph {generated_count}/{SAMPLE_SIZE} (beta={beta})")
    
    # Write to JSONL
    with open(output_file, 'w') as f:
        for entry in graphs_data:
            f.write(json.dumps(entry) + '\n')
    
    print(f"Successfully generated {generated_count} graphs to {output_file}")
    
    # Verify count
    if generated_count != SAMPLE_SIZE:
        raise ValueError(f"Generated {generated_count} graphs, expected {SAMPLE_SIZE}")
    
    # Generate checksum
    checksum = hash_artifact(str(output_file))
    
    # Update state file
    state_data = {}
    if state_file.exists():
        with open(state_file, 'r') as f:
            state_data = yaml.safe_load(f) or {}
    
    if 'artifact_hashes' not in state_data:
        state_data['artifact_hashes'] = {}
    
    state_data['artifact_hashes']['data/raw/graphs.jsonl'] = checksum
    
    with open(state_file, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)
    
    print(f"Checksum recorded: {checksum}")
    print("Graph generation pipeline completed successfully.")

if __name__ == "__main__":
    main()