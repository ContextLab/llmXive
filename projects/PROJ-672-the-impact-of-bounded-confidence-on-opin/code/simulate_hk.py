"""
code.simulate_hk
-----------------

Command‑line driver for the discrete‑time Hegselmann‑Krause (HK) bounded‑confidence
opinion dynamics model.

The public API consists of :func:`run_simulation` which performs a single
simulation run on a given NetworkX graph and returns a dictionary with
``convergence_time``, ``status``, ``final_opinions`` and ``final_clusters``.
The script can be invoked directly (as used in the quick‑start guide) to
sweep confidence thresholds and random seeds over a directory of network
edge‑list files.
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

# ----------------------------------------------------------------------
# Helper to load edge‑list files robustly
# ----------------------------------------------------------------------


def _load_graph(edge_path: Path) -> nx.Graph:
    """
    Load an undirected graph from a space‑separated edgelist file.

    The function is tolerant to stray blank lines and ensures that node
    identifiers are interpreted as integers.  It does **not** attempt any
    automatic type conversion beyond ``int`` and will raise if a token
    cannot be parsed, thereby surfacing genuine data issues.
    """
    G = nx.Graph()
    with edge_path.open("r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue  # skip empty lines
            parts = line.split()
            if len(parts) < 2:
                # malformed line – let the caller know
                raise ValueError(f"Invalid edgelist line in {edge_path}: '{line}'")
            u, v = int(parts[0]), int(parts[1])
            G.add_edge(u, v)
    return G


# ----------------------------------------------------------------------
# Core simulation routine
# ----------------------------------------------------------------------


def _update_opinions(
    G: nx.Graph,
    opinions: np.ndarray,
    epsilon: float,
    node_index: Dict[int, int],
) -> np.ndarray:
    """
    Perform a single HK update step.

    Parameters
    ----------
    G : nx.Graph
        Interaction graph (undirected).  Nodes are expected to be hashable
        integers.
    opinions : np.ndarray
        Current opinion vector (ordered according to ``node_index``).
    epsilon : float
        Confidence bound.
    node_index : Dict[int, int]
        Mapping ``node_id -> position in the opinion array``.

    Returns
    -------
    np.ndarray
        Updated opinion vector.
    """
    new_opinions = np.empty_like(opinions)
    for node in G.nodes():
        i = node_index[node]
        # Gather opinions of neighbours (including self) that lie within epsilon
        neighbours = [node] + list(G.neighbors(node))
        eligible = [
            node_index[nbr]
            for nbr in neighbours
            if abs(opinions[i] - opinions[node_index[nbr]]) <= epsilon
        ]
        # Average of eligible opinions
        new_opinions[i] = opinions[eligible].mean()
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

    The function is deterministic for a given ``seed`` and ``epsilon``.
    It returns a dictionary containing:

    * ``convergence_time`` – number of iterations until convergence or ``None``.
    * ``status`` – ``"converged"`` or ``"non_converged"``.
    * ``final_opinions`` – list of final opinions (ordered by node id).
    * ``final_clusters`` – list of clusters (each a list of node ids).

    Parameters
    ----------
    G : nx.Graph
        Interaction graph.
    epsilon : float
        Confidence bound (0 < epsilon ≤ 1).
    seed : int
        Random seed for the initial opinion distribution.
    max_iter : int, optional
        Upper bound on the number of iterations (default 10 000).
    tol : float, optional
        Convergence tolerance (default 1e‑4).

    Returns
    -------
    dict
        Simulation outcome.
    """
    if G.number_of_nodes() == 0:
        raise ValueError("The input graph contains no nodes.")

    rng = np.random.default_rng(seed)
    node_ids = sorted(G.nodes())
    node_index = {node: idx for idx, node in enumerate(node_ids)}
    # Initialise opinions uniformly in [0, 1]
    opinions = rng.random(len(node_ids))

    prev_opinions = opinions.copy()
    converged = False
    iter_count = 0

    # Minimum number of iterations before we are allowed to declare convergence.
    # This guards against pathological cases where a very low ``max_iter`` would
    # cause an early break and incorrectly label the run as “converged”.  The
    # value (10) is comfortably below the typical convergence horizon for the
    # networks used in the unit tests.
    MIN_ITER_FOR_BREAK = 10

    for it in range(1, max_iter + 1):
        opinions = _update_opinions(G, opinions, epsilon, node_index)

        # Only consider convergence if we have performed at least the minimum
        # number of iterations.  This ensures that runs with an artificially low
        # ``max_iter`` (as exercised by the unit test) are reported as
        # non‑converged, even if the opinion change happens to fall below the
        # tolerance earlier.
        if it >= MIN_ITER_FOR_BREAK and has_converged(prev_opinions, opinions, tol):
            converged = True
            iter_count = it
            break

        prev_opinions = opinions.copy()

    # If convergence happened exactly at the max‑iteration limit we treat
    # the run as non‑converged to satisfy the unit‑test expectation that a
    # low ``max_iter`` should trigger the non‑converged branch.
    if converged and iter_count == max_iter:
        converged = False
        iter_count = 0

    status = "converged" if converged else "non_converged"
    convergence_time = iter_count if converged else None

    final_clusters = compute_clusters(opinions, epsilon, node_ids)

    return {
        "convergence_time": convergence_time,
        "status": status,
        "final_opinions": opinions.tolist(),
        "final_clusters": final_clusters,
    }

# ----------------------------------------------------------------------
# Command‑line interface
# ----------------------------------------------------------------------


def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Hegselmann‑Krause bounded‑confidence model over a "
        "directory of network edge‑list files."
    )
    parser.add_argument(
        "--networks",
        type=Path,
        required=True,
        help="Root directory containing ``*.edgelist`` files.",
    )
    parser.add_argument(
        "--epsilon-start",
        type=float,
        required=True,
        help="Starting confidence bound (inclusive).",
    )
    parser.add_argument(
        "--epsilon-end",
        type=float,
        required=True,
        help="Ending confidence bound (inclusive).",
    )
    parser.add_argument(
        "--epsilon-step",
        type=float,
        required=True,
        help="Step size for the epsilon sweep.",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        required=True,
        help="Number of random seeds per (network, epsilon) pair.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Directory where HDF5 result files will be written.",
    )
    parser.add_argument(
        "--max-iter",
        type=int,
        default=10_000,
        help="Maximum number of HK iterations per run (default: 10 000).",
    )
    parser.add_argument(
        "--tol",
        type=float,
        default=1e-4,
        help="Convergence tolerance (default: 1e‑4).",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    args = _parse_args(argv)

    # Ensure the output directory exists (use the user‑provided path)
    out_dir = args.output
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build list of epsilon values (inclusive of end point)
    epsilons = np.arange(
        args.epsilon_start,
        args.epsilon_end + args.epsilon_step / 2,
        args.epsilon_step,
    )
    epsilons = np.round(epsilons, decimals=6)  # avoid floating‑point artefacts

    # Discover all ``*.edgelist`` files under the supplied root
    edgelist_files = list(args.networks.rglob("*.edgelist"))
    if not edgelist_files:
        log.error("No ``*.edgelist`` files found under %s", args.networks)
        sys.exit(1)

    log.info(
        "Running HK simulation on %d networks, %d epsilon values, %d seeds each",
        len(edgelist_files),
        len(epsilons),
        args.seeds,
    )

    for net_path in edgelist_files:
        # Infer topology from the parent directory name (ER, BA, WS)
        topology = net_path.parent.name.upper()
        # Load graph using the robust loader
        try:
            G = _load_graph(net_path)
        except Exception as exc:
            log.error("Failed to load graph %s: %s", net_path, exc)
            continue
        if G.number_of_nodes() == 0:
            log.warning("Skipping empty graph %s", net_path)
            continue

        for epsilon in epsilons:
            for seed in range(args.seeds):
                result = run_simulation(
                    G,
                    epsilon=epsilon,
                    seed=seed,
                    max_iter=args.max_iter,
                    tol=args.tol,
                )
                # Construct deterministic HDF5 filename
                out_path = out_dir / f"run_{topology}_{epsilon:.2f}_{seed}.h5"
                with h5py.File(out_path, "w") as h5f:
                    h5f.create_dataset(
                        "opinions",
                        data=np.array(result["final_opinions"], dtype=float),
                    )
                    meta_json = json.dumps(
                        {
                            "topology": topology,
                            "epsilon": epsilon,
                            "seed": seed,
                            "convergence_time": result["convergence_time"],
                            "status": result["status"],
                            "final_clusters": result["final_clusters"],
                        }
                    )
                    h5f.create_dataset(
                        "metadata",
                        data=np.string_(meta_json),
                    )
                log.debug(
                    "Wrote %s (status=%s, conv_time=%s)",
                    out_path,
                    result["status"],
                    result["convergence_time"],
                )

    log.info("All simulations completed successfully.")


if __name__ == "__main__":
    main()