"""
code.simulate_hk
-----------------

Command‑line driver for the discrete‑time Hegselmann‑Krause (HK) bounded‑confidence
opinion dynamics model.

The public API consists of :func:`run_simulation` which performs a single
simulation run on a given NetworkX graph and returns a dictionary with
``convergence_time``, ``status``, ``final_opinions`` and ``final_clusters``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

import h5py
import networkx as nx
import numpy as np

from llmxive_toolkit import paths, get_logger
from utils.convergence import compute_clusters, has_converged

log = get_logger(__name__)

def _load_graph(edge_path: Path) -> nx.Graph:
    """
    Load an undirected graph from a space‑separated edgelist file.
    Tolerates literal '\\n' sequences and stray blank lines.
    """
    G = nx.Graph()
    with edge_path.open("r") as f:
        for line in f:
            # Fix corrupted edgelists containing literal '\\n' strings
            clean_line = line.replace('\\n', ' ').strip()
            if not clean_line:
                continue
            parts = clean_line.split()
            if len(parts) < 2:
                continue
            try:
                u, v = int(parts[0]), int(parts[1])
                G.add_edge(u, v)
            except ValueError as exc:
                raise ValueError(f"Invalid edgelist line in {edge_path}: '{line}'") from exc
    return G

def _precompute_neighbor_indices(
    G: nx.Graph,
    node_index: Dict[int, int],
) -> List[np.ndarray]:
    """
    For each node, pre‑compute a NumPy array of neighbour indices (including the node itself).
    This allows the update step to be performed with pure NumPy operations,
    avoiding Python‑level loops over neighbours for every iteration.
    """
    neighbor_indices: List[np.ndarray] = []
    # Ensure deterministic ordering of nodes
    sorted_nodes = sorted(G.nodes())
    for node in sorted_nodes:
        # neighbours list includes the node itself
        nbrs = [node] + list(G.neighbors(node))
        # Map neighbour node IDs to their index in the opinion array
        idxs = np.array([node_index[nbr] for nbr in nbrs], dtype=int)
        neighbor_indices.append(idxs)
    return neighbor_indices

def _update_opinions_vectorized(
    opinions: np.ndarray,
    epsilon: float,
    neighbor_indices: List[np.ndarray],
) -> np.ndarray:
    """
    Perform a single HK update step using vectorised NumPy operations.

    For each node i we consider the opinions of its neighbours (including itself),
    keep only those whose opinion differs from opinion[i] by at most epsilon,
    and replace opinion[i] by the mean of this eligible set.
    """
    new_opinions = np.empty_like(opinions)
    for i, nbr_idxs in enumerate(neighbor_indices):
        # Opinions of neighbours of node i
        nbr_ops = opinions[nbr_idxs]
        # Mask neighbours whose opinion is within confidence bound
        mask = np.abs(nbr_ops - opinions[i]) <= epsilon
        # Compute mean of eligible neighbours; np.mean on an empty slice would raise,
        # but the node itself is always eligible, so mask is never empty.
        new_opinions[i] = nbr_ops[mask].mean()
    return new_opinions

def run_simulation(
    G: nx.Graph,
    epsilon: float,
    seed: int,
    max_iter: int = 10_000,
    tol: float = 1e-4,
) -> Dict:
    """
    Execute the HK model on ``G`` with confidence bound ``epsilon``.
    Returns a dictionary containing convergence information and final state.
    """
    if G.number_of_nodes() == 0:
        raise ValueError("The input graph contains no nodes.")

    rng = np.random.default_rng(seed)
    node_ids = sorted(G.nodes())
    node_index = {node: idx for idx, node in enumerate(node_ids)}

    # Initialise opinions uniformly in [0, 1]
    opinions = rng.random(len(node_ids))
    prev_opinions = opinions.copy()

    # Pre‑compute neighbour index arrays for fast updates
    neighbor_indices = _precompute_neighbor_indices(G, node_index)

    converged = False
    iter_count = 0

    for it in range(1, max_iter + 1):
        opinions = _update_opinions_vectorized(opinions, epsilon, neighbor_indices)
        if has_converged(prev_opinions, opinions, tol):
            converged = True
            iter_count = it
            break
        prev_opinions = opinions.copy()

    status = "converged" if converged else "non_converged"
    convergence_time = iter_count if converged else None
    final_clusters = compute_clusters(opinions, epsilon, node_ids)

    return {
        "convergence_time": convergence_time,
        "status": status,
        "final_opinions": opinions.tolist(),
        "final_clusters": final_clusters,
    }

def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run HK simulation sweep.")
    parser.add_argument("--networks", type=Path, required=True,
                        help="Root directory containing *.edgelist files.")
    parser.add_argument("--epsilon-start", type=float, required=True,
                        help="Starting confidence bound (inclusive).")
    parser.add_argument("--epsilon-end", type=float, required=True,
                        help="Ending confidence bound (inclusive).")
    parser.add_argument("--epsilon-step", type=float, required=True,
                        help="Step size for the epsilon sweep.")
    parser.add_argument("--seeds", type=int, required=True,
                        help="Number of random seeds per (network, epsilon) pair.")
    parser.add_argument("--output", type=Path, required=True,
                        help="Directory where HDF5 result files and the summary CSV will be written.")
    parser.add_argument("--max-iter", type=int, default=10_000,
                        help="Maximum number of HK iterations per run (default: 10 000).")
    parser.add_argument("--tol", type=float, default=1e-4,
                        help="Convergence tolerance (default: 1e‑4).")
    parser.add_argument("--max-total-runs", type=int, default=None,
                        help="Hard limit on total number of simulation runs (useful for quick demos).")
    return parser.parse_args(argv)

def main(argv: List[str] | None = None) -> None:
    args = _parse_args(argv)

    out_dir = args.output
    out_dir.mkdir(parents=True, exist_ok=True)

    epsilons = np.arange(args.epsilon_start,
                         args.epsilon_end + args.epsilon_step / 2,
                         args.epsilon_step)
    epsilons = np.round(epsilons, decimals=6)

    edgelist_files = list(args.networks.rglob("*.edgelist"))
    if not edgelist_files:
        log.error("No edgelist files found under %s", args.networks)
        sys.exit(1)

    log.info(
        "Running HK simulation on %d networks, %d epsilons, %d seeds",
        len(edgelist_files), len(epsilons), args.seeds,
    )

    summary_rows = []
    run_counter = 0
    max_total = args.max_total_runs

    for net_path in edgelist_files:
        topology = net_path.parent.name.upper()
        try:
            G = _load_graph(net_path)
        except Exception as exc:
            log.error("Failed to load %s: %s", net_path, exc)
            continue

        for epsilon in epsilons:
            for seed in range(args.seeds):
                # Respect hard limit if set
                if max_total is not None and run_counter >= max_total:
                    log.info("Reached max_total_runs limit (%d); stopping early.", max_total)
                    break

                result = run_simulation(
                    G,
                    epsilon=epsilon,
                    seed=seed,
                    max_iter=args.max_iter,
                    tol=args.tol,
                )

                # HDF5 output
                out_path = out_dir / f"run_{topology}_{epsilon:.2f}_{seed}.h5"
                with h5py.File(out_path, "w") as h5f:
                    h5f.create_dataset(
                        "opinions",
                        data=np.array(result["final_opinions"], dtype=float),
                    )
                    meta_json = json.dumps(
                        {
                            "topology": topology,
                            "network_id": net_path.name,
                            "epsilon": epsilon,
                            "seed": seed,
                            "convergence_time": result["convergence_time"],
                            "status": result["status"],
                            "final_clusters": result["final_clusters"],
                        }
                    )
                    h5f.create_dataset("metadata", data=np.string_(meta_json))

                summary_rows.append(
                    {
                        "run_id": out_path.name,
                        "network_id": net_path.name,
                        "epsilon": epsilon,
                        "seed": seed,
                        "convergence_time": result["convergence_time"],
                        "status": result["status"],
                        "final_clusters": len(result["final_clusters"]),
                    }
                )
                run_counter += 1
            # Break outer epsilon loop if limit reached
            if max_total is not None and run_counter >= max_total:
                break
        # Break outer network loop if limit reached
        if max_total is not None and run_counter >= max_total:
            break

    # Write summary CSV
    import pandas as pd

    summary_df = pd.DataFrame(summary_rows)
    summary_path = out_dir / "summary.csv"
    summary_df.to_csv(summary_path, index=False)
    log.info("Summary written to %s", summary_path)

if __name__ == "__main__":
    main()
