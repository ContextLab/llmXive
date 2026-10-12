"""Environment package.

Provides the ``StateGraph`` data structure together with utilities for
generating and validating synthetic graphs.

This wrapper re-exports symbols from the top‑level ``environment`` package
(which resides alongside ``src``) so that imports using the ``src``
namespace (e.g. ``import src.environment``) work correctly without moving
the original implementation files.
"""

# Re‑export core symbols from the top‑level ``environment`` package.
# The actual implementation lives in ``environment/state_graph.py``,
# ``environment/graph_generator.py`` and ``environment/validator.py``.
from importlib import import_module

_state_graph = import_module('environment.state_graph')
Node = _state_graph.Node
Edge = _state_graph.Edge
StateGraph = _state_graph.StateGraph

_graph_generator = import_module('environment.graph_generator')
generate_tier_3 = _graph_generator.generate_tier_3
generate_tier_3_nodes = _graph_generator.generate_tier_3_nodes
generate_tier_3_edges = _graph_generator.generate_tier_3_edges

_validator = import_module('environment.validator')
validate_graph = _validator.validate_graph

__all__ = [
    "Node",
    "Edge",
    "StateGraph",
    "generate_tier_3",
    "generate_tier_3_nodes",
    "generate_tier_3_edges",
    "validate_graph",
]
