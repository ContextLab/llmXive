"""
Orchestration script for the network‑synchronization pipeline.

This script iterates over every raw network file under ``data/raw/``,
computes the required topological metrics, runs the Kuramoto simulation
to obtain the synchronization threshold, and aggregates all per‑network
results into a single JSON file ``results/sim_results.json``.

Expected usage (as described in the quick‑start guide)::

    python -m src.main --config config.yaml

The script relies on the following public API:

* ``src.topology.compute_metrics(G: nx.Graph, network_id: str) -> dict``
  – computes the three required metrics and writes a JSON file under
    ``data/processed/metrics_{network_id}.json``. The returned dictionary
    contains the metric values.

* ``src.simulation.process_single_network(G: nx.Graph, network_id: str) -> SimulationResult``
  – runs the Kuramoto model (with the bisection search for the critical
    coupling) and returns a ``SimulationResult`` dataclass instance.

* ``src.utils.save_json`` – helper to write JSON files with indentation
  and optional schema validation.

The script is deliberately defensive: a failure on a single network is
logged but does not abort the whole pipeline, ensuring that the final
``sim_results.json`` contains an entry for every successfully processed
network.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict

import networkx as nx
from scipy.io import mmread

# Project‑specific imports
from config import load_config, get_paths
from src.topology import compute_metrics  # type: ignore
from src.simulation import process_single_network  # type: ignore
from src.utils import save_json  # type: ignore
from llmxive_toolkit import paths as llm_paths, get_logger

# Initialise a logger (writes to stdout by default)
log = get_logger(__name__)

def _load_graph(file_path: Path) -> nx.Graph:
    """
    Load a network graph from ``file_path``.

    Supported formats:
    * ``.mtx`` – Matrix‑Market; loaded via ``scipy.io.mmread`` and converted
      to a NetworkX graph.
    * ``.txt`` / ``.csv`` – edge‑list; loaded via ``nx.read_edgelist``.
    """
    suffix = file_path.suffix.lower()
    if suffix == ".mtx":
        log.debug(f"Loading Matrix‑Market file {file_path}")
        matrix = mmread(str(file_path))
        # Ensure the matrix is binary (0/1) adjacency
        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError(f"Adjacency matrix {file_path} is not square.")
        G = nx.from_scipy_sparse_matrix(matrix)
    elif suffix in {".txt", ".csv"}:
        log.debug(f"Loading edge‑list file {file_path}")
        # ``create_using=nx.Graph`` forces an undirected graph
        G = nx.read_edgelist(str(file_path), create_using=nx.Graph, nodetype=int)
    else:
        raise ValueError(f"Unsupported file extension '{suffix}' for {file_path}")
    return G

def process_all_networks(config: dict) -> List[Dict]:
    """
    Process every raw network file.

    For each file the function:
    1. Loads the graph.
    2. Calls ``compute_metrics`` – which also writes the per‑network metric
       JSON under ``data/processed``.
    3. Calls ``process_single_network`` – which runs the Kuramoto sweep and
       returns a ``SimulationResult``.
    4. Converts the ``SimulationResult`` into a plain ``dict`` and adds the
       ``network_id`` field.

    Returns a list of dictionaries, one per successfully processed network.
    """
    raw_dir: Path = llm_paths.data("raw")
    if not raw_dir.is_dir():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    results: List[Dict] = []
    for file_path in sorted(raw_dir.iterdir()):
        if not file_path.is_file():
            continue  # skip sub‑directories

        network_id = file_path.stem  # filename without suffix
        log.info(f"Processing network '{network_id}' from {file_path.name}")

        try:
            G = _load_graph(file_path)
        except Exception as exc:
            log.error(f"Failed to load graph '{network_id}': {exc}")
            continue

        # ------------------------------------------------------------------
        # 1) Topological metrics
        # ------------------------------------------------------------------
        try:
            metrics = compute_metrics(G, network_id)  # returns a dict
            log.debug(f"Metrics for '{network_id}': {metrics}")
        except Exception as exc:
            log.error(f"Metric computation failed for '{network_id}': {exc}")
            continue

        # ------------------------------------------------------------------
        # 2) Kuramoto simulation
        # ------------------------------------------------------------------
        try:
            sim_result = process_single_network(G, network_id)
            # Convert dataclass to dict (excluding any private attributes)
            sim_dict = {
                "network_id": network_id,
                "coupling_strength_threshold": sim_result.coupling_strength_threshold,
                "status": sim_result.status.value
                if hasattr(sim_result.status, "value")
                else str(sim_result.status),
                "order_parameter_time_series": sim_result.order_parameter_time_series,
            }
            results.append(sim_dict)
            log.info(f"Simulation finished for '{network_id}'. Threshold: {sim_dict['coupling_strength_threshold']}")
        except Exception as exc:
            log.error(f"Simulation failed for '{network_id}': {exc}")
            continue

    return results

def aggregate_simulation_results(results: List[Dict], config: dict) -> None:
    """
    Write the aggregated list of per‑network simulation results to
    ``results/sim_results.json``.
    """
    out_path: Path = llm_paths.results("sim_results.json")
    # Ensure the parent directory exists (llmxive_toolkit creates it on demand)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON with pretty‑printing (indent=2) for human readability.
    with out_path.open("w", encoding="utf-8") as fp:
        json.dump(results, fp, indent=2, sort_keys=True)

    log.info(f"Aggregated simulation results written to {out_path}")

def _parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the full network‑topology + Kuramoto pipeline."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to the YAML configuration file (default: config.yaml)",
    )
    return parser.parse_args()

def main() -> None:
    """
    Entry point used by ``python -m src.main``.
    """
    args = _parse_cli()
    cfg = load_config(args.config)
    # ``get_paths`` is kept for backward compatibility; it may return a dict
    # of pathlib.Path objects that downstream code expects.
    paths_dict = get_paths(cfg)

    log.info("Starting full pipeline")
    results = process_all_networks(cfg)
    if not results:
        log.warning("No network results were produced – check raw data and logs.")
    aggregate_simulation_results(results, cfg)
    log.info("Pipeline completed successfully")

if __name__ == "__main__":
    main()