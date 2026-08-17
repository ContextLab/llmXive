"""
Pilot dataset generation script.

This script creates a small pilot dataset consisting of multiple network
realizations for three topologies (Small‑World, Scale‑Free, Random).  For each
realization it computes topological metrics (currently only the clustering
coefficient is required) and writes a CSV file with the following columns:

    network_id, topology_type, cutoff, clustering_coeff

The output CSV is written to:
    data/processed/pilot_data/pilot_metrics.csv

The script is intended to be run directly:
    python code/generate_pilot_dataset.py

It relies on the existing network generation utilities in the project:
    - generate_small_world_graph (code/generate_networks_small_world.py)
    - generate_scale_free_graph (code/generate_networks.py)
    - generate_random_graph (code/generate_networks_extra.py)
    - compute_topological_metrics (code/generate_networks.py)

The list of cutoff factors is read from the simulation configuration file
(code/simulation_config.yaml) via the ``load_simulation_config`` helper.
If the configuration does not specify ``cutoff_factors`` a default list of
three factors is used.
"""

import csv
import os
import uuid
from pathlib import Path

# Project‑specific imports
from utils.io import load_simulation_config
from generate_networks_small_world import generate_small_world_graph
from generate_networks import generate_scale_free_graph, compute_topological_metrics
from generate_networks_extra import generate_random_graph

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DEFAULT_CUTOFF_FACTORS = [1.0, 1.5, 2.0]  # fallback if config missing
NUM_REALIZATIONS_PER_TOPOLOGY = 5        # modest number for a pilot set

OUTPUT_CSV = Path("data/processed/pilot_data/pilot_metrics.csv")


def _ensure_output_dir(path: Path) -> None:
    """Create the parent directory for *path* if it does not exist."""
    path.parent.mkdir(parents=True, exist_ok=True)


def _load_cutoff_factors() -> list[float]:
    """Load cutoff factors from the simulation config, falling back to defaults."""
    try:
        config = load_simulation_config()
        factors = config.get("cutoff_factors", DEFAULT_CUTOFF_FACTORS)
        # Ensure we have a list of numbers
        return [float(f) for f in factors]
    except Exception:
        # Any problem reading the config results in using the hard‑coded defaults.
        return DEFAULT_CUTOFF_FACTORS


def _generate_one_graph(topology: str, cutoff: float):
    """
    Generate a single network graph for the requested *topology*.

    Parameters
    ----------
    topology: str
        One of ``"small_world"``, ``"scale_free"``, ``"random"``.
    cutoff: float
        The distance‑based cutoff factor to be passed to the generator.

    Returns
    -------
    networkx.Graph
        The generated graph.
    """
    if topology == "small_world":
        # generate_small_world_graph signature (as used elsewhere) expects a
        # ``cutoff_factor`` keyword; we forward the value directly.
        return generate_small_world_graph(cutoff_factor=cutoff)
    elif topology == "scale_free":
        return generate_scale_free_graph(cutoff_factor=cutoff)
    elif topology == "random":
        return generate_random_graph(cutoff_factor=cutoff)
    else:
        raise ValueError(f"Unsupported topology type: {topology}")


def _collect_metrics(graph) -> dict:
    """
    Compute the required metrics for *graph*.

    Currently only the clustering coefficient is needed for the pilot CSV.
    ``compute_topological_metrics`` returns a dictionary that contains at
    least the key ``clustering_coeff``.
    """
    metrics = compute_topological_metrics(graph)
    # Guard against missing key – raise a clear error so the failure is loud.
    if "clustering_coeff" not in metrics:
        raise KeyError("Metric 'clustering_coeff' not found in the result of compute_topological_metrics")
    return metrics


def main() -> None:
    """Entry point for the pilot dataset generation."""
    _ensure_output_dir(OUTPUT_CSV)
    cutoff_factors = _load_cutoff_factors()

    fieldnames = ["network_id", "topology_type", "cutoff", "clustering_coeff"]
    rows = []

    for topology in ("small_world", "scale_free", "random"):
        for i in range(NUM_REALIZATIONS_PER_TOPOLOGY):
            for cutoff in cutoff_factors:
                # Generate graph
                graph = _generate_one_graph(topology, cutoff)

                # Compute metrics
                metrics = _collect_metrics(graph)

                # Assemble CSV row
                row = {
                    "network_id": str(uuid.uuid4()),
                    "topology_type": topology,
                    "cutoff": cutoff,
                    "clustering_coeff": metrics["clustering_coeff"],
                }
                rows.append(row)

    # Write CSV
    with OUTPUT_CSV.open(mode="w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Pilot dataset written to {OUTPUT_CSV} ({len(rows)} rows).")


if __name__ == "__main__":
    main()