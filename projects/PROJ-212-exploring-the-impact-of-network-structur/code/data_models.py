from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json
from pathlib import Path

class SynchronizationStatus(Enum):
    SYNCHRONIZED = "synchronized"
    NOT_SYNCHRONIZED = "not_synchronized"
    DISCONNECTED = "disconnected"
    ERROR = "error"

@dataclass
class NetworkGraph:
    id: str
    nodes: int
    edges: int
    is_connected: bool
    # We store the NetworkX graph object directly or its serialized form
    # For dataclass, we might store metadata and load the graph separately
    # Or we can store the graph if it's picklable, but for JSON serialization:
    adjacency_list: Optional[List[List[int]]] = None
    # Or just keep it simple and assume the graph is managed elsewhere
    # and this dataclass holds metadata.
    # Let's stick to metadata for the dataclass and load graphs on demand.
    # However, the task might expect a graph object.
    # Let's assume we store the graph object in memory and this is a metadata holder.
    # For serialization purposes, we might need to export to edge list.
    pass

@dataclass
class SimulationResult:
    network_id: str
    threshold: float
    status: SynchronizationStatus
    metrics: Dict[str, float]
    r_parameter: float
    t_parameter: int

@dataclass
class RegressionModel:
    model_type: str
    coefficients: Dict[str, float]
    r_squared: float
    p_values: Dict[str, float]
    vif_scores: Optional[Dict[str, float]] = None
    cv_mean_r2: Optional[float] = None
    cv_std_dev: Optional[float] = None
    stability_flag: Optional[bool] = None
