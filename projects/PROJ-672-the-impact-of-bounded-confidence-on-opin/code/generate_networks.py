"""
Network generation script.

Provides a CLI that creates synthetic networks of a specified topology,
writes each network to an edgelist file, and stores a per‑instance JSON
metadata file as well as a summary CSV for the whole batch.

The script is deterministic: the global random seed is set from a base
seed plus the instance index. All generated graphs contain exactly
500 nodes, matching the project specification.
"""

import argparse
import json
import random
from pathlib import Path

import networkx as nx
import pandas as pd

from llmxive_toolkit import paths, get_logger
from utils.metrics import calculate_structural_metrics

log = get_logger(__name__)

def set_global_seed(seed: int) -> None:
    """Set global seeds for reproducibility."""
    random.seed(seed)
    import numpy as np
    np.random.seed(seed)

def generate_erdos_renyi(n: int, p: float, seed: int) -> nx.Graph:
    """Generate an Erdős‑Renyi (G(n, p)) graph."""
    return nx.erdos_renyi_graph(n=n, p=p, seed=seed)

def generate_barabasi_albert(n: int, m: int, seed: int) -> nx.Graph:
    """Generate a Barabási‑Albert preferential‑attachment graph."""
    return nx.barabasi_albert_graph(n=n, m=m, seed=seed)

def generate_watts_strogatz(n: int, k: int, p: float, seed: int) -> nx.Graph:
    """Generate a Watts‑Strogatz small‑world graph."""
    return nx.watts_strogatz_graph(n=n, k=k, p=p, seed=seed)

def ensure_connected(G: nx.Graph, strategy: str = "largest") -> nx.Graph:
    """Ensure the returned graph is connected."""
    if nx.is_connected(G):
        return G
    if strategy == "largest":
        largest_cc = max(nx.connected_components(G), key=len)
        subgraph = G.subgraph(largest_cc).copy()
        mapping = {old_label: new_label for new_label, old_label in enumerate(subgraph.nodes())}
        return nx.relabel_nodes(subgraph, mapping)
    raise ValueError(f"Unknown strategy: {strategy}")

def _write_edgelist(G: nx.Graph, out_path: Path) -> None:
    """Write the graph's edge list (one edge per line: u v)."""
    with out_path.open("w") as f:
        for u, v in G.edges():
            f.write(f"{u} {v}\n")

def _write_metadata(metadata: dict, out_path: Path) -> None:
    """Write a JSON file containing the network metadata."""
    with out_path.open("w") as f:
        json.dump(metadata, f, indent=2)

def _flatten_metrics(metrics: dict, prefix: str = "") -> dict:
    """Flatten the nested metrics dict for CSV output."""
    flat = {}
    for key, value in metrics.items():
        flat_key = f"{prefix}{key}" if prefix else key
        # If the value itself is a dict, recurse
        if isinstance(value, dict):
            flat.update(_flatten_metrics(value, prefix=f"{flat_key}_"))
        else:
            flat[flat_key] = value
    return flat

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic networks.")
    parser.add_argument("--topology", choices=["ER", "BA", "WS"], required=False,
                        help="Generate only the specified topology (default: all three).")
    parser.add_argument("--instances", type=int, default=None,
                        help="Number of network instances per topology (default: 50).")
    parser.add_argument("--seeds", type=int, default=None,
                        help="Alias for --instances (kept for backward compatibility).")
    parser.add_argument("--seed", type=int, default=0,
                        help="Base seed for reproducibility (default: 0).")
    parser.add_argument("--output", type=str, default=None,
                        help="Output directory (default: data/raw/networks).")
    args = parser.parse_args()

    # Determine how many instances to create
    instances = args.seeds if args.seeds is not None else (
        args.instances if args.instances is not None else 50
    )

    # Resolve output directory using llmxive_toolkit helper
    base_dir = Path(args.output) if args.output else paths.data("raw", "networks")
    base_dir.mkdir(parents=True, exist_ok=True)

    # Which topologies to generate?
    topologies = [args.topology] if args.topology else ["ER", "BA", "WS"]
    N_NODES = 500

    # Collect rows for the summary CSV (one row per instance)
    for topology in topologies:
        csv_path = base_dir / f"{topology}_metadata.csv"
        csv_rows = []

        for idx in range(instances):
            instance_seed = args.seed + idx
            set_global_seed(instance_seed)

            # Generate the appropriate graph
            if topology == "ER":
                G = generate_erdos_renyi(n=N_NODES, p=0.05, seed=instance_seed)
            elif topology == "BA":
                G = generate_barabasi_albert(n=N_NODES, m=3, seed=instance_seed)
            else:  # WS
                G = generate_watts_strogatz(n=N_NODES, k=6, p=0.2, seed=instance_seed)

            # Ensure we have a connected component of the requested size
            G = ensure_connected(G)

            if G.number_of_nodes() != N_NODES:
                raise RuntimeError(
                    f"Expected {N_NODES} nodes, got {G.number_of_nodes()}"
                )

            # File naming follows the required pattern: <TOPO>_<IDX>.edgelist
            base_name = f"{topology}_{idx:04d}"
            edgelist_path = base_dir / f"{base_name}.edgelist"
            metadata_path = base_dir / f"metadata_{base_name}.json"

            # Persist files
            _write_edgelist(G, edgelist_path)
            metrics = calculate_structural_metrics(G)
            metadata = {
                "topology": topology,
                "seed": instance_seed,
                "node_count": G.number_of_nodes(),
                "edge_count": G.number_of_edges(),
                "metrics": metrics,
            }
            _write_metadata(metadata, metadata_path)

            # Prepare a flat row for the CSV (includes metric columns)
            row = {
                "topology": topology,
                "seed": instance_seed,
                "node_count": G.number_of_nodes(),
                "edge_count": G.number_of_edges(),
            }
            row.update(_flatten_metrics(metrics, prefix="metric_"))
            csv_rows.append(row)

        # Write the per‑topology CSV
        df = pd.DataFrame(csv_rows)
        # Ensure deterministic column order: topology, seed, node_count, edge_count, then metrics
        cols = ["topology", "seed", "node_count", "edge_count"] + [
            c for c in df.columns if c.startswith("metric_")
        ]
        df = df[cols]
        df.to_csv(csv_path, index=False)

    log.info("Network generation completed.")

if __name__ == "__main__":
    main()
