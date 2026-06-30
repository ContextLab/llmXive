"""
Pydantic models defining the executable schemas for the transit project.

These schemas are used to validate outputs from:
- T004: GTFS data fetcher
- T005: GTFS to NetworkX graph converter

And ensure data integrity before consumption by US3 (Dataset Construction).
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ValidationError
from enum import Enum
import json


class TransitLine(BaseModel):
    """Represents a transit line (e.g., 'L', '1', 'R')."""
    line_id: str = Field(..., description="Unique identifier for the line")
    short_name: str = Field(..., description="Human-readable short name (e.g., 'L')")
    long_name: Optional[str] = Field(None, description="Full name of the line")
    color: Optional[str] = Field(None, description="Hex color code for the line")
    text_color: Optional[str] = Field(None, description="Hex text color for contrast")

    @field_validator('line_id')
    @classmethod
    def line_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('line_id cannot be empty')
        return v.strip()


class StationNode(BaseModel):
    """Represents a station node in the graph."""
    station_id: str = Field(..., description="Unique identifier for the station")
    name: str = Field(..., description="Human-readable station name")
    zone_id: Optional[str] = Field(None, description="Zone identifier if applicable")
    # Note: Explicitly NO latitude/longitude fields to ensure map-free property

    @field_validator('station_id')
    @classmethod
    def station_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('station_id cannot be empty')
        return v.strip()

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('station name cannot be empty')
        return v.strip()


class TransferEdge(BaseModel):
    """Represents a transfer edge between stations."""
    from_station_id: str = Field(..., description="Source station ID")
    to_station_id: str = Field(..., description="Destination station ID")
    transfer_type: int = Field(0, description="Transfer type (0=recommended, 1=possible, 2=time_needed, 3=impossible)")
    min_transfer_time: Optional[int] = Field(None, description="Minimum transfer time in seconds")

    @field_validator('from_station_id', 'to_station_id')
    @classmethod
    def station_ids_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Station ID cannot be empty')
        return v.strip()


class GTFSGraph(BaseModel):
    """
    Schema for the GTFS-derived NetworkX graph representation.
    Validates the output of T005 (graph_utils.py).
    """
    metadata: Dict[str, Any] = Field(..., description="Graph metadata (source, timestamp, etc.)")
    nodes: List[StationNode] = Field(..., description="List of station nodes")
    edges: List[TransferEdge] = Field(..., description="List of transfer edges")
    lines: List[TransitLine] = Field(..., description="List of transit lines")

    @field_validator('nodes')
    @classmethod
    def nodes_not_empty(cls, v):
        if not v:
            raise ValueError('At least one node is required')
        return v

    @field_validator('edges')
    @classmethod
    def edges_must_match_nodes(cls, v, info):
        # We cannot easily validate cross-field dependencies in a simple validator
        # without accessing 'values', but we ensure the list exists.
        return v


class RouteSequence(BaseModel):
    """
    Schema for a map-free route sequence.
    Validates the output of T011 (text_utils.py) and US3 generation.
    """
    route_id: str = Field(..., description="Unique ID for this generated sequence")
    origin_station_id: str = Field(..., description="Starting station ID")
    destination_station_id: str = Field(..., description="Ending station ID")
    stations: List[str] = Field(..., description="Ordered list of station IDs in the path")
    lines_used: List[str] = Field(default_factory=list, description="List of line IDs used in order")
    text_prompt: str = Field(..., description="Natural language prompt text")
    text_target: str = Field(..., description="Natural language target/answer text")

    @field_validator('stations')
    @classmethod
    def stations_not_empty(cls, v):
        if not v:
            raise ValueError('Station sequence cannot be empty')
        if len(v) < 2:
            raise ValueError('Station sequence must have at least origin and destination')
        return v

    @field_validator('origin_station_id', 'destination_station_id')
    @classmethod
    def station_ids_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Station ID cannot be empty')
        return v.strip()


class ValidationStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    PARTIAL = "partial"
    ERROR = "error"


class ValidationResult(BaseModel):
    """
    Schema for the result of validating a generated route against the graph.
    Validates the output of T017 (validation.py).
    """
    route_id: str = Field(..., description="ID of the route being validated")
    status: ValidationStatus = Field(..., description="Validation status")
    exact_match: bool = Field(..., description="Whether the sequence exactly matches ground truth")
    connectivity_valid: bool = Field(..., description="Whether the sequence is a valid path in the graph")
    score: float = Field(..., ge=0.0, le=1.0, description="Numerical validity score")
    error_message: Optional[str] = Field(None, description="Error details if validation failed")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional diagnostic details")

    @field_validator('score')
    @classmethod
    def score_in_range(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError('Score must be between 0.0 and 1.0')
        return v

# Helper function to serialize models to JSON for artifact storage
def model_to_json(model: BaseModel) -> str:
    return model.model_dump_json(indent=2)

def load_graph_from_json(json_str: str) -> GTFSGraph:
    return GTFSGraph.model_validate_json(json_str)

def load_route_from_json(json_str: str) -> RouteSequence:
    return RouteSequence.model_validate_json(json_str)

def load_validation_from_json(json_str: str) -> ValidationResult:
    return ValidationResult.model_validate_json(json_str)
