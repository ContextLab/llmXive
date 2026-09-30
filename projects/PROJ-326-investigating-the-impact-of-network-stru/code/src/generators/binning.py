import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

def classify_graph(graph: Any, bins: List[float]) -> Optional[str]:
    """
    Classify a graph into a bin based on its clustering coefficient.
    bins: List of thresholds, e.g., [0.1, 0.2, 0.3, 0.4, 0.5]
    Returns a string label like "bin_0.1" or None if outside range.
    """
    try:
        import networkx as nx
        cc = nx.average_clustering(graph)
    except Exception as e:
        logger.error(f"Failed to compute clustering coefficient: {e}")
        return None

    # Determine bin
    # Bins are defined as intervals: [0, b1), [b1, b2), ..., [bn, 1.0]
    # Or strictly: < b1, < b2, ..., >= bn
    # Let's assume bins represent upper bounds of intervals starting from 0
    # e.g., bins=[0.1, 0.2] means:
    # bin_0.1: 0 <= cc < 0.1
    # bin_0.2: 0.1 <= cc < 0.2
    # bin_max: cc >= 0.2

    bin_label = None
    for i, threshold in enumerate(bins):
        if cc < threshold:
            bin_label = f"bin_{threshold}"
            break
    else:
        # If cc is greater than or equal to all thresholds
        bin_label = f"bin_{bins[-1]}_plus" if bins else "bin_unknown"

    logger.debug(f"Graph classified into {bin_label} (cc={cc:.3f})")
    return bin_label
