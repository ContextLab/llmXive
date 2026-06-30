"""
Contracts package for executable schemas.

Exports Pydantic models for:
- GTFSGraph
- RouteSequence
- ValidationResult
"""
from .models import (
    GTFSGraph,
    StationNode,
    TransferEdge,
    TransitLine,
    RouteSequence,
    ValidationResult,
    ValidationStatus,
    model_to_json,
    load_graph_from_json,
    load_route_from_json,
    load_validation_from_json
)

__all__ = [
    "GTFSGraph",
    "StationNode",
    "TransferEdge",
    "TransitLine",
    "RouteSequence",
    "ValidationResult",
    "ValidationStatus",
    "model_to_json",
    "load_graph_from_json",
    "load_route_from_json",
    "load_validation_from_json"
]
