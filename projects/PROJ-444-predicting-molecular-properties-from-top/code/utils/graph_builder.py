"""
graph_builder.py
Utilities for building molecular graphs, validating SMILES, and handling memory checks.
"""

import logging
from pathlib import Path
from typing import Optional, Union

import networkx as nx
import numpy as np
from rdkit import Chem

# Global singleton logger for invalid SMILES
_invalid_smiles_logger: Optional[logging.Logger] = None


def setup_invalid_smiles_logger(log_file: Union[str, Path]) -> logging.Logger:
    """
    Configure a logger that records invalid SMILES strings to the given file.
    The logger is a singleton; repeated calls return the same logger.

    Parameters
    ----------
    log_file : Union[str, Path]
        Path to the log file where invalid SMILES will be recorded.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    global _invalid_smiles_logger
    if _invalid_smiles_logger is not None:
        return _invalid_smiles_logger

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("invalid_smiles_logger")
    logger.setLevel(logging.INFO)
    # Avoid duplicate handlers if this function is called multiple times
    if not logger.handlers:
        handler = logging.FileHandler(log_path, mode='a')
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    _invalid_smiles_logger = logger
    return logger


def log_invalid_smiles(smiles: str, reason: str) -> None:
    """
    Log an invalid SMILES string with a reason. If the logger has not been set up,
    it will be created with the default path ``data/logs/invalid_smiles.log``.

    Parameters
    ----------
    smiles : str
        The SMILES string that could not be processed.
    reason : str
        Human‑readable explanation of why the SMILES is invalid.
    """
    global _invalid_smiles_logger
    if _invalid_smiles_logger is None:
        # Default log location as required by the spec
        default_path = Path("data") / "logs" / "invalid_smiles.log"
        setup_invalid_smiles_logger(default_path)
    _invalid_smiles_logger.info(f"{smiles}\t{reason}")


def is_valid_molecule(smiles: str) -> bool:
    """
    Validate a SMILES string using RDKit. Returns True if the SMILES can be
    parsed into a Mol object; otherwise logs the failure and returns False.

    Parameters
    ----------
    smiles : str
        SMILES representation of a molecule.

    Returns
    -------
    bool
        True if RDKit can create a molecule object, False otherwise.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        log_invalid_smiles(smiles, "RDKit failed to parse SMILES")
        return False
    # Additional sanity checks can be added here (e.g., valence)
    return True


# Memory handling constants
MEMORY_THRESHOLD_BYTES = 100 * 1024 * 1024  # 100 MiB


def check_memory_requirement(num_nodes: int) -> bool:
    """
    Check whether the all‑pairs shortest‑path matrix for a graph with
    ``num_nodes`` nodes fits within the memory threshold.

    Parameters
    ----------
    num_nodes : int
        Number of nodes in the graph.

    Returns
    -------
    bool
        True if the estimated memory (num_nodes² × 8 bytes) is below the threshold.

    Raises
    ------
    MemoryError
        If the estimated memory exceeds ``MEMORY_THRESHOLD_BYTES``.
    """
    # Estimate memory for a dense float64 matrix
    estimated_bytes = num_nodes * num_nodes * 8
    if estimated_bytes > MEMORY_THRESHOLD_BYTES:
        raise MemoryError(
            f"Shortest‑path matrix would require {estimated_bytes / (1024**2):.2f} MiB, "
            f"exceeding the {MEMORY_THRESHOLD_BYTES / (1024**2):.2f} MiB limit."
        )
    return True


def compute_shortest_path_matrix(graph: nx.Graph) -> np.ndarray:
    """
    Compute the all‑pairs shortest‑path distance matrix for ``graph``.
    For disconnected node pairs the distance is set to ``np.inf``.

    Parameters
    ----------
    graph : nx.Graph
        Undirected graph representing a molecule.

    Returns
    -------
    np.ndarray
        A ``(n, n)`` array of shortest‑path distances (float64), where ``n``
        is the number of nodes.

    Raises
    ------
    MemoryError
        If the required matrix would exceed the memory threshold.
    """
    n = graph.number_of_nodes()
    if n == 0:
        return np.zeros((0, 0), dtype=np.float64)

    # Verify memory constraints before allocation
    check_memory_requirement(n)

    # Initialise with infinities
    dist_matrix = np.full((n, n), np.inf, dtype=np.float64)
    np.fill_diagonal(dist_matrix, 0.0)

    # Map nodes to integer indices
    nodes = list(graph.nodes())
    node_to_idx = {node: i for i, node in enumerate(nodes)}

    # Compute shortest paths using Dijkstra (handles weighted edges if any)
    for source, lengths in nx.all_pairs_dijkstra_path_length(graph):
        u = node_to_idx[source]
        for target, d in lengths.items():
            v = node_to_idx[target]
            dist_matrix[u, v] = float(d)

    return dist_matrix
