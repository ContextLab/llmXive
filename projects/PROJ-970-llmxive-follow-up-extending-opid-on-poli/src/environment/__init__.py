"""Environment package.

Provides the ``StateGraph`` data structure together with utilities for
generating and validating synthetic graphs.
"""

# Re‑export core symbols from the implementation located under ``code/environment``.
from importlib import import_module

# Import the concrete implementations.
_state_graph = import_module('code.environment.state_graph')
Node = _state_graph.Node
Edge = _state_graph.Edge
StateGraph = _state_graph.StateGraph

_graph_generator = import_module('code.environment.graph_generator')
generate_tier_1 = _graph_generator.generate_tier_1
generate_tier_2 = _graph_generator.generate_tier_2
generate_tier_3 = _graph_generator.generate_tier_3
generate_tier_3_nodes = _graph_generator.generate_tier_3_nodes
generate_tier_3_edges = _graph_generator.generate_tier_3_edges

_validator = import_module('code.environment.validator')
validate_graph = _validator.validate_graph

__all__ = [
    "Node",
    "Edge",
    "StateGraph",
    "generate_tier_1",
    "generate_tier_2",
    "generate_tier_3",
    "generate_tier_3_nodes",
    "generate_tier_3_edges",
    "validate_graph",
]
