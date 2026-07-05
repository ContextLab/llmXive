"""
Metadata logging module for network generation tasks.

Records algorithm details, parameters (edge_probability, preferential_attachment_params),
and random seeds for every generated graph, saving to data/metadata/graph_<id>.json.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from code.src.utils.reproducibility import ensure_data_directory, generate_run_id
from code.src.utils.io import compute_file_checksum


def _ensure_metadata_dir() -> Path:
    """Ensure the metadata directory exists within the data folder."""
    data_root = Path("data")
    metadata_dir = data_root / "metadata"
    ensure_data_directory(metadata_dir)
    return metadata_dir


def save_graph_metadata(
    graph_id: str,
    algorithm: str,
    seed: int,
    parameters: Optional[Dict[str, Any]] = None,
    output_dir: Optional[Union[str, Path]] = None,
) -> Path:
    """
    Save metadata for a generated graph to a JSON file.

    Args:
        graph_id: Unique identifier for the graph (e.g., 'er_001', 'sf_002').
        algorithm: Name of the generation algorithm (e.g., 'erdos_renyi', 'barabasi_albert').
        seed: The random seed used for generation.
        parameters: Dictionary of generation parameters (e.g., edge_probability, m).
        output_dir: Optional directory to save the file. Defaults to data/metadata/.

    Returns:
        Path to the created metadata file.
    """
    if output_dir is None:
        output_dir = _ensure_metadata_dir()
    else:
        output_dir = Path(output_dir)
        ensure_data_directory(output_dir)

    # Normalize parameters to ensure JSON serializability
    clean_params = {}
    if parameters:
        for k, v in parameters.items():
            if isinstance(v, (int, float, str, bool, type(None))):
                clean_params[k] = v
            elif isinstance(v, (list, tuple)):
                clean_params[k] = list(v)
            elif isinstance(v, dict):
                clean_params[k] = {str(ik): iv for ik, iv in v.items()}
            else:
                clean_params[k] = str(v)

    metadata = {
        "graph_id": graph_id,
        "algorithm": algorithm,
        "seed": seed,
        "parameters": clean_params,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }

    filename = f"graph_{graph_id}.json"
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, sort_keys=True)

    # Compute and store checksum for integrity verification
    checksum = compute_file_checksum(filepath)
    metadata["checksum"] = checksum

    # Rewrite with checksum included
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, sort_keys=True)

    return filepath


def load_graph_metadata(graph_id: str, input_dir: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load metadata for a specific graph.

    Args:
        graph_id: Unique identifier for the graph.
        input_dir: Optional directory to load from. Defaults to data/metadata/.

    Returns:
        Dictionary containing graph metadata.

    Raises:
        FileNotFoundError: If the metadata file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if input_dir is None:
        input_dir = _ensure_metadata_dir()
    else:
        input_dir = Path(input_dir)

    filename = f"graph_{graph_id}.json"
    filepath = input_dir / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Metadata file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def log_generation_batch(
    batch_id: str,
    graphs: list,
    algorithm: str,
    seed: int,
    parameters: Optional[Dict[str, Any]] = None,
) -> list:
    """
    Log metadata for a batch of generated graphs.

    Args:
        batch_id: Identifier for the batch run.
        graphs: List of tuples (graph_id, graph_object) or just graph_ids.
        algorithm: Name of the generation algorithm.
        seed: Random seed used for the batch.
        parameters: Generation parameters.

    Returns:
        List of paths to created metadata files.
    """
    paths = []
    for item in graphs:
        if isinstance(item, tuple):
            graph_id, _ = item
        else:
            graph_id = item

        path = save_graph_metadata(
            graph_id=graph_id,
            algorithm=algorithm,
            seed=seed,
            parameters=parameters,
        )
        paths.append(path)
    return paths