from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json
from pathlib import Path
import networkx as nx

class SynchronizationStatus(Enum):
    SYNCHRONIZED = "synchronized"
    NOT_SYNCHRONIZED = "not_synchronized"
    DISCONNECTED = "disconnected"
    ERROR = "error"

@dataclass
class NetworkGraph:
    id: str
    graph: nx.Graph
    # Metadata
    nodes: int = 0
    edges: int = 0
    is_connected: bool = False
    
    def __post_init__(self):
        self.nodes = self.graph.number_of_nodes()
        self.edges = self.graph.number_of_edges()
        self.is_connected = nx.is_connected(self.graph) if self.nodes > 0 else False

@dataclass
class SimulationResult:
    network_id: str
    threshold: float
    status: SynchronizationStatus
    metrics: Dict[str, float]
    r_parameter: float
    t_parameter: int
    # Additional simulation details
    coupling_range: List[float] = field(default_factory=list)
    convergence_steps: int = 0

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
