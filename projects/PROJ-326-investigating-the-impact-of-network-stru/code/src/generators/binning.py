"""
Binning logic for classifying generated graphs into clustering coefficient bins.

This module implements the stratification logic required for FR-001 and SC-005.
It classifies graphs based on their global clustering coefficient against configured
bin boundaries defined in config.yaml under `stratification_params.bins`.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
import networkx as nx

from code.src.utils.config import get_global_config

logger = logging.getLogger(__name__)


def _get_bin_boundaries() -> List[float]:
    """
    Retrieves the clustering coefficient bin boundaries from the global config.

    Returns:
        List[float]: Sorted list of bin boundaries (e.g., [0.1, 0.2, 0.3, 0.4, 0.5]).

    Raises:
        ValueError: If the configuration is missing or malformed.
    """
    config = get_global_config()
    if not config:
        raise ValueError("Global config is not loaded. Ensure config.yaml is valid and loaded.")

    strat_params = config.get("stratification_params", {})
    bins = strat_params.get("bins", [])

    if not bins:
        raise ValueError(
            "Configuration missing 'stratification_params.bins'. "
            "Please define bin boundaries in code/config.yaml."
        )

    # Ensure bins are floats and sorted
    try:
        sorted_bins = sorted([float(b) for b in bins])
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid bin values in config: {e}")

    return sorted_bins


def classify_graph(graph: nx.Graph) -> str:
    """
    Classifies a generated graph into a specific clustering coefficient bin.

    The function calculates the global clustering coefficient of the input graph
    and determines which bin it falls into based on the boundaries defined in
    `code/config.yaml` under `stratification_params.bins`.

    Bin Logic:
        - Bin 0: [0.0, bins[0])
        - Bin 1: [bins[0], bins[1])
        - ...
        - Bin N: [bins[N-1], 1.0]

    Args:
        graph (nx.Graph): The networkx graph to classify.

    Returns:
        str: The bin identifier (e.g., "bin_0", "bin_1", "bin_high").

    Raises:
        ValueError: If the graph is None or has fewer than 3 nodes (clustering undefined).
        RuntimeError: If the config is invalid.
    """
    if graph is None:
        raise ValueError("Cannot classify a None graph.")

    if graph.number_of_nodes() < 3:
        # Graphs with < 3 nodes have a clustering coefficient of 0.0 by definition
        # or are undefined. We treat them as bin_0 (lowest).
        logger.warning("Graph has < 3 nodes. Assigning to lowest bin (bin_0).")
        return "bin_0"

    try:
        clustering = nx.clustering(graph)
        global_clustering = nx.average_clustering(graph)
    except Exception as e:
        raise RuntimeError(f"Failed to compute clustering coefficient: {e}")

    boundaries = _get_bin_boundaries()

    # Determine bin index
    bin_index = 0
    assigned_bin = "bin_0"

    # Check against boundaries
    # If global_clustering < boundaries[0], it's bin_0
    # If boundaries[i] <= global_clustering < boundaries[i+1], it's bin_{i+1}
    # If global_clustering >= boundaries[-1], it's the last bin (or "bin_high")

    found = False
    for i, threshold in enumerate(boundaries):
        if global_clustering < threshold:
            bin_index = i
            assigned_bin = f"bin_{i}"
            found = True
            break

    if not found:
        # It is greater than or equal to all thresholds
        bin_index = len(boundaries)
        assigned_bin = f"bin_{bin_index}"

    logger.debug(
        f"Graph classified: clustering={global_clustering:.4f} -> {assigned_bin} "
        f"(thresholds: {boundaries})"
    )

    return assigned_bin


def get_bin_range(bin_name: str) -> Tuple[float, float]:
    """
    Returns the numeric range [lower, upper) for a given bin name.

    Args:
        bin_name (str): The bin identifier (e.g., "bin_0", "bin_1").

    Returns:
        Tuple[float, float]: The lower and upper bounds of the bin.
    """
    boundaries = _get_bin_boundaries()
    bin_num = int(bin_name.replace("bin_", ""))

    lower = 0.0 if bin_num == 0 else boundaries[bin_num - 1]
    upper = 1.0 if bin_num >= len(boundaries) else boundaries[bin_num]

    return lower, upper
