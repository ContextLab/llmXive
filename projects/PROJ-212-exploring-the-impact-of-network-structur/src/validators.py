"""
Validators for data integrity checks in network synchronization analysis.

This module provides functions to:
- Validate graph structures and simulation inputs (existing functionality).
- Load JSON files and validate them against JSON/YAML schemas stored in the
  ``contracts/`` directory.
- Run a lightweight self‑test (`python -m src.validators --self-test`) that
  ensures the schema loading and validation machinery works without error.
"""

import json
import logging
import pathlib
from typing import Any, Dict, List, Tuple, Union, Optional

import jsonschema
import yaml
import networkx as nx
import numpy as np

from data_models import NetworkGraph

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Existing graph‑related validation utilities (preserved from the original file)
# ----------------------------------------------------------------------
def check_disconnected_graph(graph: nx.Graph) -> Tuple[bool, int]:
    """
    Check if a graph is disconnected and count its connected components.

    Args:
        graph: A NetworkX graph to check.

    Returns:
        Tuple of (is_disconnected, num_components).
        is_disconnected is True if the graph has more than one connected component.
        num_components is the total number of connected components.

    Raises:
        ValueError: If the graph is None or empty.
    """
    if graph is None:
        raise ValueError("Graph cannot be None")

    if graph.number_of_nodes() == 0:
        raise ValueError("Graph cannot be empty")

    num_components = nx.number_connected_components(graph)
    is_disconnected = num_components > 1

    if is_disconnected:
        logger.warning(
            f"Graph has {num_components} connected components. "
            f"Simulation may return infinity threshold."
        )

    return is_disconnected, num_components


def validate_graph(
    graph: Union[nx.Graph, NetworkGraph],
    min_nodes: int = 2,
    max_nodes: int = 10000,
    allow_self_loops: bool = False,
    allow_multiple_edges: bool = False,
) -> Tuple[bool, List[str]]:
    """
    Validate a graph meets structural requirements for simulation.

    Args:
        graph: NetworkX graph or NetworkGraph dataclass to validate.
        min_nodes: Minimum number of nodes required.
        max_nodes: Maximum number of nodes allowed.
        allow_self_loops: Whether self‑loops are permitted.
        allow_multiple_edges: Whether multiple edges between nodes are permitted.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors: List[str] = []

    # Extract NetworkX graph from NetworkGraph if needed
    if isinstance(graph, NetworkGraph):
        nx_graph = getattr(graph, "graph", None)
    elif isinstance(graph, nx.Graph):
        nx_graph = graph
    else:
        errors.append(f"Invalid graph type: {type(graph)}")
        return False, errors

    if nx_graph is None:
        errors.append("Graph is None")
        return False, errors

    # Node count checks
    num_nodes = nx_graph.number_of_nodes()
    if num_nodes < min_nodes:
        errors.append(f"Graph has {num_nodes} nodes, minimum required is {min_nodes}")
    if num_nodes > max_nodes:
        errors.append(f"Graph has {num_nodes} nodes, maximum allowed is {max_nodes}")

    # Self‑loop check
    if not allow_self_loops:
        self_loops = list(nx.selfloop_edges(nx_graph))
        if self_loops:
            errors.append(f"Graph contains {len(self_loops)} self‑loops")

    # Multiple‑edge check
    if not allow_multiple_edges:
        if isinstance(nx_graph, nx.MultiGraph):
            errors.append("Graph is a MultiGraph but multiple edges are not allowed")
        elif isinstance(nx_graph, nx.Graph):
            # Simple Graph – nothing extra needed
            pass

    # Isolated nodes
    isolated_nodes = [n for n, d in nx_graph.degree() if d == 0]
    if isolated_nodes:
        errors.append(f"Graph contains {len(isolated_nodes)} isolated nodes")

    # Negative edge weight check
    for u, v, data in nx_graph.edges(data=True):
        if "weight" in data and data["weight"] < 0:
            errors.append(f"Edge ({u}, {v}) has negative weight: {data['weight']}")
            break

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_network_list(
    networks: List[Union[nx.Graph, NetworkGraph, Dict[str, Any]]]
) -> Tuple[bool, List[str]]:
    """
    Validate a list of networks for batch processing.

    Args:
        networks: List of graphs or network dictionaries to validate.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors: List[str] = []

    if not networks:
        errors.append("Network list is empty")
        return False, errors

    if len(networks) > 1000:
        logger.warning(f"Large network list detected: {len(networks)} networks")

    for idx, network in enumerate(networks):
        # Extract Graph object
        if isinstance(network, dict):
            if "graph" not in network:
                errors.append(f"Network at index {idx} is a dict without 'graph' key")
                continue
            graph = network["graph"]
        else:
            graph = network

        is_valid, graph_errors = validate_graph(graph)
        if not is_valid:
            network_id = (
                network.get("id", f"index_{idx}")
                if isinstance(network, dict)
                else f"index_{idx}"
            )
            for err in graph_errors:
                errors.append(f"Network '{network_id}': {err}")

    is_valid = len(errors) == 0
    if not is_valid:
        logger.warning(f"Validation failed for {len(errors)}/{len(networks)} networks")
    return is_valid, errors


def validate_simulation_inputs(
    graph: nx.Graph,
    natural_frequencies: Optional[np.ndarray] = None,
    coupling_strength: Optional[float] = None,
    time_span: Optional[Tuple[float, float]] = None,
    num_oscillators: Optional[int] = None,
) -> Tuple[bool, List[str]]:
    """
    Validate inputs for a Kuramoto simulation.

    Args:
        graph: NetworkX graph representing oscillator connections.
        natural_frequencies: Array of natural frequencies for each oscillator.
        coupling_strength: Global coupling strength K.
        time_span: Tuple of (start_time, end_time) for simulation.
        num_oscillators: Number of oscillators (should match graph nodes).

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors: List[str] = []

    # Graph validation
    if graph is None:
        errors.append("Graph is None")
        return False, errors

    num_nodes = graph.number_of_nodes()
    if num_nodes == 0:
        errors.append("Graph has no nodes")
        return False, errors

    # Oscillator count consistency
    if num_oscillators is not None and num_oscillators != num_nodes:
        errors.append(
            f"num_oscillators ({num_oscillators}) does not match graph nodes ({num_nodes})"
        )
    else:
        num_oscillators = num_nodes

    # Natural frequencies check
    if natural_frequencies is not None:
        if len(natural_frequencies) != num_oscillators:
            errors.append(
                f"Natural frequencies length ({len(natural_frequencies)}) "
                f"does not match num_oscillators ({num_oscillators})"
            )
        elif not isinstance(natural_frequencies, np.ndarray):
            errors.append("Natural frequencies must be a numpy array")
        elif np.any(np.isnan(natural_frequencies)) or np.any(np.isinf(natural_frequencies)):
            errors.append("Natural frequencies contain NaN or Inf values")
    else:
        natural_frequencies = np.zeros(num_oscillators)

    # Coupling strength check
    if coupling_strength is not None:
        if not isinstance(coupling_strength, (int, float)):
            errors.append("Coupling strength must be a number")
        elif coupling_strength < 0:
            errors.append("Coupling strength cannot be negative")

    # Time span validation
    if time_span is not None:
        if not isinstance(time_span, (tuple, list)) or len(time_span) != 2:
            errors.append("Time span must be a tuple of (start, end)")
        elif time_span[0] >= time_span[1]:
            errors.append("Time span start must be less than end")
        elif time_span[0] < 0:
            errors.append("Time span start cannot be negative")
    else:
        time_span = (0.0, 100.0)

    is_valid = len(errors) == 0
    if not is_valid:
        logger.error(f"Simulation input validation failed: {errors}")

    return is_valid, errors

# ----------------------------------------------------------------------
# JSON‑schema validation utilities (new for T009)
# ----------------------------------------------------------------------
def _contracts_dir() -> pathlib.Path:
    """
    Return the absolute path to the ``contracts`` directory located at the
    project root. The ``llmxive_toolkit.paths`` helper is not used here to
    avoid a circular import; instead we locate the directory relative to
    this file's location.
    """
    return pathlib.Path(__file__).resolve().parents[1] / "contracts"

def load_json_file(file_path: Union[str, pathlib.Path]) -> Dict[str, Any]:
    """
    Load a JSON file and return its contents as a Python dictionary.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed JSON data.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = pathlib.Path(file_path)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a schema file (YAML or JSON) from the ``contracts`` directory.

    Args:
        schema_name: Filename of the schema (e.g. ``simulation_result.schema.yaml``).

    Returns:
        The schema as a Python dictionary.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError / json.JSONDecodeError: If the schema cannot be parsed.
    """
    schema_path = _contracts_dir() / schema_name
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    if schema_path.suffix.lower() in {".yaml", ".yml"}:
        with schema_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    elif schema_path.suffix.lower() == ".json":
        with schema_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    else:
        raise ValueError(f"Unsupported schema file type: {schema_path}")

def validate_json_against_schema(
    data: Dict[str, Any],
    schema: Dict[str, Any],
    *,  # keyword‑only arguments for clarity
    resolver: Optional[jsonschema.RefResolver] = None,
) -> None:
    """
    Validate a Python dictionary against a JSON/YAML schema using ``jsonschema``.

    This function raises ``jsonschema.ValidationError`` if validation fails.
    It returns ``None`` on success.

    Args:
        data: The JSON‑compatible Python object to validate.
        schema: The schema dictionary.
        resolver: Optional ``jsonschema.RefResolver`` for handling ``$ref``.
    """
    jsonschema.validate(instance=data, schema=schema, resolver=resolver)

def validate_file(
    json_path: Union[str, pathlib.Path],
    schema_name: str,
) -> bool:
    """
    Load a JSON file and validate it against the named schema.

    Args:
        json_path: Path to the JSON file to validate.
        schema_name: Name of the schema file located in ``contracts/``.

    Returns:
        ``True`` if validation succeeds.

    Raises:
        jsonschema.ValidationError: If the JSON does not conform to the schema.
        FileNotFoundError: If either the JSON or the schema file is missing.
    """
    data = load_json_file(json_path)
    schema = load_schema(schema_name)
    validate_json_against_schema(data, schema)
    return True

def _self_test() -> None:
    """
    Minimal self‑test that ensures schema loading works without error.
    It iterates over all ``*.schema.yaml`` files in the ``contracts`` folder
    and attempts to load each one. Successful loading is considered a pass.
    """
    contracts = _contracts_dir()
    schema_files = sorted(contracts.glob("*.schema.yaml"))
    if not schema_files:
        logger.warning("No schema files found in contracts/ – self‑test is a no‑op.")
        return

    for schema_path in schema_files:
        try:
            _ = load_schema(schema_path.name)
            logger.info(f"Loaded schema: {schema_path.name}")
        except Exception as exc:
            logger.error(f"Failed loading schema {schema_path.name}: {exc}")
            raise

    logger.info("Self‑test passed: all schemas loaded successfully.")

# ----------------------------------------------------------------------
# Command‑line interface
# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry point for ``python -m src.validators``.

    Supported flags:
    - ``--self-test`` : Run the internal self‑test and exit with status 0
      on success.
    - ``--validate <json_file> <schema_name>`` : Validate a specific JSON
      file against a schema from ``contracts/``.
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Validate JSON artefacts against contract schemas."
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run a quick self‑test that loads all schemas.",
    )
    parser.add_argument(
        "--validate",
        nargs=2,
        metavar=("JSON_FILE", "SCHEMA_NAME"),
        help="Validate JSON_FILE against SCHEMA_NAME (file in contracts/).",
    )

    args = parser.parse_args()

    if args.self_test:
        try:
            _self_test()
            sys.exit(0)
        except Exception:
            sys.exit(1)

    if args.validate:
        json_file, schema_name = args.validate
        try:
            validate_file(json_file, schema_name)
            logger.info(f"Validation succeeded: {json_file} ↔ {schema_name}")
            sys.exit(0)
        except Exception as exc:
            logger.error(f"Validation failed: {exc}")
            sys.exit(1)

    # If no arguments were supplied, show help.
    parser.print_help()
    sys.exit(0)

if __name__ == "__main__":
    main()
