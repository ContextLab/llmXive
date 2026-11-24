"""
src/simulation.py
-----------------

This module provides the Kuramoto oscillator simulation utilities required for
User Story 1.  It re‑exports the core implementation from the internal
``code/src/simulation.py`` file (which contains the detailed numerical code)
and adds a small command‑line interface that writes a ``SimulationResult`` JSON
file for a single network.

The public API matches the test suite expectations:
  - ``find_critical_coupling`` – locate the synchronization threshold.
  - ``discrete_sweep_fallback`` – fallback sweep when bisection fails.
  - ``process_single_network`` – end‑to‑end processing of a ``networkx.Graph``.
  - ``run_kuramoto_simulation`` – run the model at a fixed coupling strength.

The CLI can be invoked as:

    python -m src.simulation --network-id <id> --graph-path <path/to/edgelist>

The resulting JSON is written to ``results/sim_<network_id>.json`` using the
``src.utils.save_json`` helper, with the ``SynchronizationStatus`` enum value
stored as its string representation.
"""

import argparse
import json
from pathlib import Path
from dataclasses import asdict

import networkx as nx

# Re‑export the core simulation functions from the implementation module.
# The implementation lives under ``code/src/simulation.py`` and is imported
# here to avoid code duplication while still satisfying the public import
# contract ``src.simulation`` expected by the test suite.
from code.src.simulation import (
    check_disconnected,
    compute_order_parameter,
    kuramoto_derivative,
    run_kuramoto_simulation,
    find_critical_coupling,
    discrete_sweep_fallback,
    process_single_network as _core_process_single_network,
)

# ``src.utils`` provides a ``save_json`` helper that writes JSON with
# ``indent=2`` and validates against the appropriate schema.
try:
    from src.utils import save_json
except ImportError as exc:
    raise ImportError(
        "The project expects a 'src.utils.save_json' helper. "
        "Make sure 'src/utils.py' exists and defines 'save_json'."
    ) from exc

# Import the dataclass and enum used for constructing a result when the
# graph is disconnected.
try:
    from data_models import SimulationResult, SynchronizationStatus
except ImportError as exc:
    raise ImportError(
        "Unable to import SimulationResult or SynchronizationStatus from "
        "'data_models'. Ensure the dataclasses are defined as expected."
    ) from exc

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_graph(graph_path: Path) -> nx.Graph:
    """
    Load a graph from an edge‑list file.

    Supported formats:
      * ``.edgelist`` or ``.txt`` – interpreted as a whitespace‑separated
        edge list with integer node identifiers.
      * ``.mtx`` – Matrix‑Market format; ``networkx.readwrite`` can parse it.

    Parameters
    ----------
    graph_path: Path
        Path to the graph file.

    Returns
    -------
    nx.Graph
        The loaded (undirected) graph.
    """
    if not graph_path.is_file():
        raise FileNotFoundError(f"Graph file not found: {graph_path}")

    suffix = graph_path.suffix.lower()
    if suffix in {".edgelist", ".txt", ".csv"}:
        # ``nodetype=int`` ensures node IDs are integers.
        return nx.read_edgelist(str(graph_path), nodetype=int, create_using=nx.Graph())
    elif suffix == ".mtx":
        # ``readwrite`` can read Matrix‑Market files directly.
        return nx.readwrite.readwrite.read_weighted_edgelist(str(graph_path))
    else:
        raise ValueError(f"Unsupported graph file extension: {suffix}")

def _simulation_result_to_dict(sim_res):
    """
    Convert a ``SimulationResult`` dataclass instance to a plain dictionary
    suitable for JSON serialisation.  Enum values are converted to their
    ``value`` string.
    """
    result_dict = asdict(sim_res)
    # ``status`` is an Enum – replace with its string value.
    if "status" in result_dict and hasattr(result_dict["status"], "value"):
        result_dict["status"] = result_dict["status"].value
    return result_dict

# ----------------------------------------------------------------------
# Guarded wrapper for ``process_single_network``
# ----------------------------------------------------------------------
def process_single_network(
    G: nx.Graph,
    network_id: str,
    K_min: float = 0.0,
    K_max: float = 5.0,
    tol: float = 0.001,
    max_iter: int = 50,
    seed: int | None = None,
) -> SimulationResult:
    """
    Wrapper around the core ``process_single_network`` that adds the
    required guard for disconnected graphs.

    If the input graph is disconnected, the function returns a
    ``SimulationResult`` with ``coupling_strength_threshold`` set to ``None``
    and ``status`` set to ``SynchronizationStatus.DISCONNECTED`` without
    performing any K‑sweep or integration.

    Otherwise, the call is delegated to the original implementation.
    """
    if check_disconnected(G):
        # The graph is disconnected – return the sentinel result.
        return SimulationResult(
            network_id=network_id,
            coupling_strength_threshold=None,
            status=SynchronizationStatus.DISCONNECTED,
        )
    # Connected graph – delegate to the full implementation.
    return _core_process_single_network(
        G,
        network_id,
        K_min=K_min,
        K_max=K_max,
        tol=tol,
        max_iter=max_iter,
        seed=seed,
    )

# ----------------------------------------------------------------------
# Command‑line interface
# ----------------------------------------------------------------------
def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Kuramoto synchronization simulation for a single network "
                    "and write the result as JSON."
    )
    parser.add_argument(
        "--network-id",
        required=True,
        help="Identifier for the network (used in the output filename).",
    )
    parser.add_argument(
        "--graph-path",
        type=Path,
        required=True,
        help="Path to the network edge‑list (or Matrix‑Market) file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="Directory where the JSON result will be written (default: ./results).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility of natural frequencies and initial phases.",
    )
    return parser

def main() -> None:
    """
    Entry point for ``python -m src.simulation``.

    The function parses command‑line arguments, loads the graph, runs the
    Kuramoto simulation (including the K‑sweep / bisection search), and
    writes a ``SimulationResult`` JSON file named ``sim_<network_id>.json``
    under the specified output directory.
    """
    args = _build_arg_parser().parse_args()

    # Ensure the output directory exists.
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Load the network.
    G = _load_graph(args.graph_path)

    # Process the network – this handles disconnected graphs internally.
    sim_res = process_single_network(
        G,
        network_id=args.network_id,
        K_min=0.0,
        K_max=5.0,
        tol=0.001,
        max_iter=50,
        seed=args.seed,
    )

    # Serialise the result.
    result_dict = _simulation_result_to_dict(sim_res)

    # Write JSON using the project's helper (ensures schema validation).
    output_path = args.output_dir / f"sim_{args.network_id}.json"
    save_json(result_dict, output_path)

    print(f"Simulation result written to {output_path}")

if __name__ == "__main__":
    main()