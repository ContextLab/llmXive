"""Environment package.

Provides the ``StateGraph`` data structure together with utilities for
generating and validating synthetic graphs.
"""

# Export core symbols so that ``import src.environment`` gives direct access
from .state_graph import Node, Edge, StateGraph  # noqa: F401
from .graph_generator import (
    generate_tier_3,
    generate_tier_3_nodes,
    generate_tier_3_edges,
)  # noqa: F401
from .validator import validate_graph  # noqa: F401

__all__ = [
    "Node",
    "Edge",
    "StateGraph",
    "generate_tier_3",
    "generate_tier_3_nodes",
    "generate_tier_3_edges",
    "validate_graph",
]
