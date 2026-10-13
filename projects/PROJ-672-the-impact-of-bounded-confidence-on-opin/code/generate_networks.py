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

# Import the metric calculator
from utils.metrics import calculate_structural_metrics

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions – public API (must keep signatures unchanged)
# ----------------------------------------------------------------------
def set_global_seed(seed: int) -> None:
    """Set global seeds for reproducibility."""
    random.seed(seed)
    # NumPy uses its own RNG; set it as well for any downstream use.
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
    """
    Ensure the returned graph is connected.

    Parameters
    ----------
    G : nx.Graph
        Input graph (may be disconnected).
    strategy : str, optional
        'largest' – keep only the largest connected component.
        'bridge' – not implemented (raises NotImplementedError).

    Returns
    -------
    nx.Graph
        A connected graph.
    """
    if nx.is_connected(G):
        return G

    if strategy == "largest":
        # Keep the largest connected component and relabel nodes 0..N-1
        largest_cc = max(nx.connected_components(G), key=len)
        subgraph = G.subgraph(largest_cc).copy()
        mapping = {
            old_label: new_label for new_label, old_label in enumerate(subgraph.nodes())
        }
        return nx.relabel_nodes(subgraph, mapping)
    elif strategy == "bridge":
        raise NotImplementedError("Bridge strategy not implemented")
    else:
        raise ValueError(f"Unknown strategy: {strategy}")


# ----------------------------------------------------------------------
# Internal file writers
# ----------------------------------------------------------------------
def _write_edgelist(G: nx.Graph, out_path: Path) -> None:
    """Write the graph's edge list (one edge per line: u v)."""
    with out_path.open("w") as f:
        for u, v in G.edges():
            f.write(f"{u} {v}\n")


def _write_metadata(metadata: dict, out_path: Path) -> None:
    """Write a JSON file containing the network metadata."""
    with out_path.open("w") as f:
        json.dump(metadata, f, indent=2)


# ----------------------------------------------------------------------
# Main CLI
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate synthetic networks (ER, BA, WS) and store them as "
            "edgelist files, per‑instance JSON metadata, and a batch CSV. "
            "If --topology is omitted, all three topologies are generated."
        )
    )
    parser.add_argument(
        "--topology",
        choices=["ER", "BA", "WS"],
        required=False,
        help=(
            "Network topology to generate (Erdős‑Renyi, Barabási‑Albert, Watts‑Strogatz). "
            "If omitted, all topologies are generated."
        ),
    )
    parser.add_argument(
        "--instances",
        type=int,
        default=None,
        help=(
            "Number of independent network instances to generate per topology. "
            "Deprecated in favour of --seeds; if both are provided, --seeds wins."
        ),
    )
    parser.add_argument(
        "--seeds",
        type=int,
        default=None,
        help="Alias for --instances; the number of networks to generate per topology.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Base random seed. Each instance will use seed + index.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help=(
            "Base output directory for generated networks. "
            "Defaults to the project's data/raw/networks/ folder."
        ),
    )

    args = parser.parse_args()

    # Resolve number of instances to generate.
    # If neither --instances nor --seeds is supplied, default to 50
    # as required by the research specification.
    if args.seeds is not None:
        instances = args.seeds
    elif args.instances is not None:
        instances = args.instances
    else:
        instances = 50  # Default for the main study

    # Resolve output base directory
    if args.output:
        base_dir = Path(args.output)
    else:
        base_dir = paths.data("raw", "networks")
    base_dir.mkdir(parents=True, exist_ok=True)

    # Determine which topologies to process
    topologies = [args.topology] if args.topology else ["ER", "BA", "WS"]

    # Fixed problem size per the specification
    N_NODES = 500

    log.info(f"Generating {instances} instance(s) for topology set: {topologies}")

    for topology in topologies:
        # Prepare output sub‑directory for this topology (kept for backward compatibility)
        topology_dir = base_dir / topology
        topology_dir.mkdir(parents=True, exist_ok=True)

        # CSV summary file (one per topology)
        csv_path = base_dir / f"{topology}_metadata.csv"
        csv_rows = []

        for idx in range(instances):
            instance_seed = args.seed + idx
            set_global_seed(instance_seed)

            # ------------------------------------------------------------------
            # Generate the raw graph according to topology
            # ------------------------------------------------------------------
            if topology == "ER":
                # Use a higher edge probability to ensure connectivity.
                p = 0.05
                G = generate_erdos_renyi(n=N_NODES, p=p, seed=instance_seed)
            elif topology == "BA":
                m = 3  # each new node attaches to 3 existing nodes
                G = generate_barabasi_albert(n=N_NODES, m=m, seed=instance_seed)
            else:  # WS
                k = 6  # each node initially connected to 6 nearest neighbours
                # Slightly higher rewiring probability improves connectivity.
                p = 0.2
                G = generate_watts_strogatz(n=N_NODES, k=k, p=p, seed=instance_seed)

            # Ensure a single connected component
            G = ensure_connected(G, strategy="largest")

            # Verify node count (required by verification)
            if G.number_of_nodes() != N_NODES:
                raise RuntimeError(
                    f"Generated graph has {G.number_of_nodes()} nodes; expected {N_NODES}."
                )

            # ------------------------------------------------------------------
            # Write artefacts
            # ------------------------------------------------------------------
            base_name = f"{topology}_{idx:04d}"
            edgelist_path = topology_dir / f"{base_name}.edgelist"
            metadata_path = topology_dir / f"metadata_{base_name}.json"

            _write_edgelist(G, edgelist_path)

            # Compute structural metrics using the shared utility
            metrics = calculate_structural_metrics(G)

            metadata = {
                "topology": topology,
                "seed": instance_seed,
                "node_count": G.number_of_nodes(),
                "edge_count": G.number_of_edges(),
                "metrics": metrics,
            }
            _write_metadata(metadata, metadata_path)

            # ALSO write a copy of the metadata at the root of the networks folder
            # to satisfy tasks that expect files like data/raw/networks/metadata_BA_0001.json
            root_metadata_path = base_dir / f"metadata_{base_name}.json"
            _write_metadata(metadata, root_metadata_path)

            # Collect row for CSV summary
            csv_rows.append({
                "topology": topology,
                "seed": instance_seed,
                "node_count": G.number_of_nodes(),
                "edge_count": G.number_of_edges(),
            })

            log.info(f"Wrote {edgelist_path} and {metadata_path}")

        # Write (or overwrite) the CSV summary for this topology
        df = pd.DataFrame(csv_rows)
        # Ensure deterministic column order matching the schema
        df = df[["topology", "seed", "node_count", "edge_count"]]
        df.to_csv(csv_path, index=False)
        log.info(f"Summary CSV written to {csv_path}")

    log.info("Network generation completed.")


if __name__ == "__main__":
    main()