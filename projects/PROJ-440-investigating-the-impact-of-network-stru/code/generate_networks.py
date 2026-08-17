import os
import sys
import json
import hashlib
import argparse
import logging

import networkx as nx
import numpy as np
from typing import Dict, Any, Tuple, Optional
from scipy.stats import ks_2samp

def set_seed(seed: int) -> None:
    """Sets the random seed for reproducibility."""
    np.random.seed(seed)
    nx.set_random_state(seed)


def power_law_function(x: np.ndarray, a: float, k: float) -> np.ndarray:
    """Calculates the power law function."""
    return a * x**(-k)

def validate_scale_free(degree_sequence: list[int]) -> bool:
      """Validates if the degree sequence follows a power law distribution using KS test."""

      # Fit power law to observed data
      from scipy.optimize import curve_fit
      popt, pcov = curve_fit(power_law_function, np.unique(degree_sequence), np.histogram(degree_sequence, bins=np.unique(degree_sequence))[0])

      # Generate theoretical power law distribution
      x = np.unique(degree_sequence)
      y_theoretical = power_law_function(x, *popt)

      # Perform KS test
      ks_statistic, p_value = ks_2samp(degree_sequence, y_theoretical)

      return p_value > 0.05


def validate_random_graph(graph: nx.Graph) -> bool:
    """Validates if the graph is a random graph."""
    # Check if the degree distribution is approximately Poisson
    degrees = sorted([d for n, d in graph.degree()])
    mean_degree = np.mean(degrees)
    variance_degree = np.var(degrees)
    return abs(variance_degree - mean_degree) < 0.1 * mean_degree  # Allow some tolerance

def generate_random_graph(n: int, seed: int) -> nx.Graph:
    """Generates a random graph with n nodes."""
    set_seed(seed)
    return nx.erdos_renyi_graph(n, 0.1)

def generate_scale_free_graph(n: int, seed: int) -> nx.Graph:
    """Generates a scale-free graph with n nodes."""
    set_seed(seed)
    return nx.barabasi_albert_graph(n, 3)

def generate_small_world_graph(n: int, seed: int) -> nx.Graph:
    """Generates a small-world graph with n nodes."""
    set_seed(seed)
    return nx.watts_strogatz_graph(n, 6, 0.1)

def generate_lattice_graph(n: int, seed: int) -> nx.Graph:
    """Generates a lattice graph with n nodes."""
    set_seed(seed)
    sqrt_n = int(np.sqrt(n))
    return nx.grid_2d_graph(sqrt_n, sqrt_n)

def generate_star_graph(n: int, seed: int) -> nx.Graph:
      """Generates a star graph with n nodes."""
      set_seed(seed)
      if n < 2:
          raise ValueError("Star graph requires at least 2 nodes.")
      center = 0
      leaves = list(range(1, n))
      graph = nx.Graph()
      graph.add_nodes_from(range(n))
      for leaf in leaves:
          graph.add_edge(center, leaf)
      return graph

def compute_metrics_for_graph(graph: nx.Graph) -> Dict[str, float]:
    """Computes metrics for a given graph."""
    clustering_coefficient = nx.average_clustering(graph)
    try:
        average_path_length = nx.average_shortest_path_length(graph)
    except nx.NetworkXError:  # Handle disconnected graphs
        average_path_length = np.nan

    degree_sequence = sorted([d for n, d in graph.degree()])
    return {
        "clustering_coefficient": clustering_coefficient,
        "average_path_length": average_path_length,
        "degree_sequence": degree_sequence,
    }

def generate_networks(num_graphs: int, network_class: str, n: int = 100) -> list[Tuple[str, nx.Graph, Dict[str, float]]]:
    """Generates a list of networks with specified class and metrics."""
    networks = []
    for i in range(num_graphs):
        seed = i  # Use different seed for each graph
        if network_class == "random":
            graph = generate_random_graph(n, seed)
        elif network_class == "scale_free":
            graph = generate_scale_free_graph(n, seed)
        elif network_class == "small_world":
            graph = generate_small_world_graph(n, seed)
        elif network_class == "lattice":
            graph = generate_lattice_graph(n, seed)
        elif network_class == "star":
          graph = generate_star_graph(n,seed)
        else:
            raise ValueError(f"Unknown network class: {network_class}")

        metrics = compute_metrics_for_graph(graph)
        networks.append((network_class, graph, metrics))
    return networks


def save_to_csv(data: list[Tuple[str, nx.Graph, Dict[str, float]]], filename: str) -> None:
    """Saves network data to a CSV file."""
    with open(filename, "w") as f:
        f.write("id,class,N,clustering_coefficient,average_path_length\n")
        for i, (network_class, graph, metrics) in enumerate(data):
            row = [
                str(i),
                network_class,
                str(graph.number_of_nodes()),
                str(metrics["clustering_coefficient"]),
                str(metrics["average_path_length"]),
            ]
            f.write(",".join(row) + "\n")

def main():
    """Main function to generate networks and save them to a CSV file."""

    parser = argparse.ArgumentParser(description="Generate network topologies and compute metrics.")
    parser.add_argument("--num_graphs", type=int, default=10, help="Number of graphs per class.")
    parser.add_argument("--network_classes", nargs='+', default=["random", "scale_free", "small_world", "lattice","star"], help="List of network classes to generate.")
    parser.add_argument("--filename", type=str, default="data/raw/networks.csv", help="Output CSV filename.")

    args = parser.parse_args()

    all_networks = []
    for network_class in args.network_classes:
        networks = generate_networks(args.num_graphs, network_class)
        all_networks.extend(networks)

    save_to_csv(all_networks, args.filename)

    print(f"Generated and saved networks to {args.filename}")


if __name__ == "__main__":
    main()
