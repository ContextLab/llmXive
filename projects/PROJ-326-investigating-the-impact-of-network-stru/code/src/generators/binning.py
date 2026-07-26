"""
Binning logic for classifying generated graphs into clustering coefficient bins.
Implements FR-001 and SC-005 requirements for stratified sampling.
"""
import logging
from typing import List, Optional, Tuple
import networkx as nx

logger = logging.getLogger(__name__)


def get_clustering_coefficient(graph: nx.Graph) -> float:
    """
    Calculate the global clustering coefficient (transitivity) of a graph.

    Args:
        graph: A NetworkX graph object.

    Returns:
        float: The clustering coefficient value between 0 and 1.
    """
    if graph.number_of_nodes() == 0:
        return 0.0
    return nx.transitivity(graph)


def classify_graph(
    graph: nx.Graph,
    bins: Optional[List[float]] = None
) -> Tuple[str, float]:
    """
    Classify a generated graph into a clustering coefficient bin.

    This function calculates the clustering coefficient of the input graph
    and determines which bin it falls into based on the provided bin edges.
    The bins are defined as intervals [bin[i], bin[i+1]).

    Args:
        graph: A NetworkX graph object to classify.
        bins: A sorted list of float bin edges. If None, defaults to
              [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 1.0] as per T062a config.
              The last bin includes the upper bound.

    Returns:
        Tuple[str, float]: A tuple containing:
            - bin_label (str): The label of the bin (e.g., "bin_0", "bin_1").
            - coefficient (float): The calculated clustering coefficient.

    Raises:
        ValueError: If the graph is None or has no nodes.
        ValueError: If the clustering coefficient falls outside the defined bins.
    """
    if graph is None:
        raise ValueError("Input graph cannot be None.")
    if graph.number_of_nodes() == 0:
        raise ValueError("Input graph must have at least one node.")

    # Default bins from T062a config.yaml definition
    if bins is None:
        bins = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 1.0]

    # Validate bins
    if len(bins) < 2:
        raise ValueError("Bins must contain at least two values (lower and upper bound).")

    coefficient = get_clustering_coefficient(graph)

    # Determine bin index
    # We look for the first bin where coefficient < upper_bound
    # Special handling for the last bin which includes the upper bound
    bin_index = -1
    for i in range(len(bins) - 1):
        lower = bins[i]
        upper = bins[i + 1]

        # Check if coefficient falls in [lower, upper)
        # For the last bin, we include the upper bound
        if i == len(bins) - 2:
            if lower <= coefficient <= upper:
                bin_index = i
                break
        else:
            if lower <= coefficient < upper:
                bin_index = i
                break

    if bin_index == -1:
        # This should theoretically not happen if bins cover [0, 1]
        raise ValueError(
            f"Clustering coefficient {coefficient:.4f} does not fall into any defined bin "
            f"with edges {bins}. This indicates a configuration error in the bin boundaries."
        )

    bin_label = f"bin_{bin_index}"
    logger.debug(
        f"Graph classified into {bin_label} with clustering coefficient {coefficient:.4f}"
    )

    return bin_label, coefficient
