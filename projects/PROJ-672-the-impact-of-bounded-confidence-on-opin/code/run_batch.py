"""
code.run_batch
----------------

Batch runner for the Hegselmann‑Krause (HK) bounded‑confidence opinion dynamics
model. It sweeps the confidence threshold ε over a configurable range and
runs a number of independent seeds for each network instance. Results are
stored as HDF5 files together with a summary CSV.

The script can be invoked directly from the command line, e.g.:

    python -m code.run_batch \\
        --networks data/raw/networks/ \\
        --output data/raw/simulations/ \\
        --epsilon-start 0.05 \\
        --epsilon-end 0.50 \\
        --epsilon-step 0.05 \\
        --seeds 50

The generated files are:

* ``data/raw/simulations/run_{TOPOLOGY}_{epsilon:.2f}_{seed}.h5`` – one
  HDF5 file per simulation containing the opinion vector and a JSON
  metadata record.
* ``data/raw/simulations/summary.csv`` – a CSV that aggregates the metadata
  of all runs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

import h5py
import numpy as np
import pandas as pd

from llmxive_toolkit import paths, get_logger
from simulate_hk import run_simulation

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper to load edge‑list files robustly
# ----------------------------------------------------------------------


def _load_graph_custom(edge_path: Path) -> "nx.Graph":
    """
    Load a NetworkX graph from a space‑separated edgelist file.

    The original ``generate_networks`` script writes the edgelist as a
    single line with escaped ``\\n`` characters (e.g.
    ``"0 36\\n0 41\\n..."``).  This loader first replaces the literal
    ``\\n`` with an actual newline, then parses each line in the usual
    way.  It also tolerates proper multi‑line files.

    Parameters
    ----------
    edge_path : Path
        Path to the ``*.edgelist`` file.

    Returns
    -------
    nx.Graph
        The loaded undirected graph.
    """
    import networkx as nx

    raw_text = edge_path.read_text(encoding="utf-8")
    # Replace escaped newline literals with real newlines
    normalized = raw_text.replace("\\n", "\n")
    G = nx.Graph()
    for line in normalized.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            raise ValueError(f"Invalid edgelist line in {edge_path}: '{line}'")
        u, v = int(parts[0]), int(parts[1])
        G.add_edge(u, v)
    return G


# ----------------------------------------------------------------------
# Core batch logic
# ----------------------------------------------------------------------


def _generate_epsilons(start: float, end: float, step: float) -> List[float]:
    eps = np.arange(start, end + step / 2, step)
    return [float(f"{e:.6f}") for e in np.round(eps, decimals=6)]


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Batch runner for HK simulations over a sweep of ε values."
    )
    parser.add_argument(
        "--networks",
        type=Path,
        required=True,
        help="Root directory containing ``*.edgelist`` files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Directory where HDF5 result files and the summary CSV will be written.",
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
    args = parser.parse_args(argv)

    # Prepare output directories
    out_dir: Path = args.output
    out_dir.mkdir(parents=True, exist_ok=True)

    # Discover all edgelist files
    edgelist_files = list(args.networks.rglob("*.edgelist"))
    if not edgelist_files:
        log.error("No ``*.edgelist`` files found under %s", args.networks)
        raise FileNotFoundError("No network edgelist files discovered.")

    epsilons = _generate_epsilons(args.epsilon_start, args.epsilon_end, args.epsilon_step)

    summary_records = []
    run_counter = 0

    for net_path in edgelist_files:
        topology = net_path.parent.name.upper()
        network_id = net_path.stem  # e.g. "ER_0000"
        try:
            G = _load_graph_custom(net_path)
        except Exception as exc:
            log.error("Failed to load graph %s: %s", net_path, exc)
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
                h5_name = f"run_{topology}_{epsilon:.2f}_{seed}.h5"
                h5_path = out_dir / h5_name

                with h5py.File(h5_path, "w") as h5f:
                    h5f.create_dataset(
                        "opinions",
                        data=np.array(result["final_opinions"], dtype=float),
                    )
                    meta_json = json.dumps(
                        {
                            "topology": topology,
                            "network_id": network_id,
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

                summary_records.append(
                    {
                        "run_id": run_counter,
                        "network_id": network_id,
                        "topology": topology,
                        "epsilon": epsilon,
                        "seed": seed,
                        "convergence_time": result["convergence_time"],
                        "status": result["status"],
                        "final_clusters": json.dumps(result["final_clusters"]),
                    }
                )
                run_counter += 1
                log.debug(
                    "Wrote %s (status=%s, conv_time=%s)",
                    h5_path,
                    result["status"],
                    result["convergence_time"],
                )

    # Write summary CSV
    summary_df = pd.DataFrame(summary_records)
    summary_path = out_dir / "summary.csv"
    summary_df.to_csv(summary_path, index=False)
    log.info("Batch completed: %d runs written to %s", run_counter, out_dir)


if __name__ == "__main__":
    main()