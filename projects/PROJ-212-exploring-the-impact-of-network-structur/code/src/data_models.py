from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json
from pathlib import Path
import networkx as nx


class SynchronizationStatus(Enum):
    """Enum representing the synchronization state of a network."""
    NOT_SYNCHRONIZED = "not_synchronized"
    PARTIALLY_SYNCHRONIZED = "partially_synchronized"
    SYNCHRONIZED = "synchronized"
    DISCONNECTED = "disconnected"


@dataclass
class NetworkGraph:
    """
    Represents a network graph with associated metadata.
    
    Attributes:
        graph: The NetworkX graph object.
        source_id: Identifier for the source dataset (e.g., SNAP ID).
        source_path: Path to the source file if loaded from disk.
        num_nodes: Number of nodes in the graph.
        num_edges: Number of edges in the graph.
        is_connected: Boolean indicating if the graph is connected.
        metadata: Additional key-value metadata.
    """
    graph: nx.Graph
    source_id: str
    source_path: Optional[str] = None
    num_nodes: int = field(init=False)
    num_edges: int = field(init=False)
    is_connected: bool = field(init=False)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.num_nodes = self.graph.number_of_nodes()
        self.num_edges = self.graph.number_of_edges()
        self.is_connected = nx.is_connected(self.graph) if self.num_nodes > 0 else False

    def to_dict(self) -> Dict[str, Any]:
        """Convert basic attributes to a dictionary (excludes graph object)."""
        return {
            "source_id": self.source_id,
            "source_path": self.source_path,
            "num_nodes": self.num_nodes,
            "num_edges": self.num_edges,
            "is_connected": self.is_connected,
            "metadata": self.metadata
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize basic attributes to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


@dataclass
class SimulationResult:
    """
    Represents the result of a Kuramoto synchronization simulation.
    
    Attributes:
        source_id: ID of the network simulated.
        critical_coupling: The estimated critical coupling strength (K_c).
                           If disconnected, this is None or float('inf').
        order_parameter_max: Maximum order parameter achieved during simulation.
        synchronization_time: Time steps taken to reach synchronization.
        status: The final synchronization status.
        metrics: Dictionary of topological metrics used in this run.
        raw_data: Optional path to raw simulation data files.
    """
    source_id: str
    critical_coupling: Optional[float]
    order_parameter_max: float
    synchronization_time: Optional[int]
    status: SynchronizationStatus
    metrics: Dict[str, float] = field(default_factory=dict)
    raw_data: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for JSON serialization."""
        return {
            "source_id": self.source_id,
            "critical_coupling": self.critical_coupling,
            "order_parameter_max": self.order_parameter_max,
            "synchronization_time": self.synchronization_time,
            "status": self.status.value,
            "metrics": self.metrics,
            "raw_data": self.raw_data
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


@dataclass
class RegressionModel:
    """
    Represents a statistical regression model analyzing the relationship
    between topological features and synchronization thresholds.
    
    Attributes:
        model_type: Type of model (e.g., 'Linear', 'Polynomial', 'Ridge').
        coefficients: Dictionary mapping feature names to coefficients.
        intercept: The intercept term.
        r_squared: Coefficient of determination.
        p_values: Dictionary mapping feature names to p-values.
        vif_scores: Dictionary mapping feature names to Variance Inflation Factors.
        cv_mean_r2: Mean R² from cross-validation.
        cv_std_r2: Standard deviation of R² from cross-validation.
        is_stable: Boolean indicating if the model is stable (CV std dev <= 0.1).
        alpha: Alpha parameter used for Ridge regression (if applicable).
    """
    model_type: str
    coefficients: Dict[str, float]
    intercept: float
    r_squared: float
    p_values: Dict[str, float]
    vif_scores: Optional[Dict[str, float]] = None
    cv_mean_r2: Optional[float] = None
    cv_std_r2: Optional[float] = None
    is_stable: Optional[bool] = None
    alpha: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for JSON serialization."""
        return {
            "model_type": self.model_type,
            "coefficients": self.coefficients,
            "intercept": self.intercept,
            "r_squared": self.r_squared,
            "p_values": self.p_values,
            "vif_scores": self.vif_scores,
            "cv_mean_r2": self.cv_mean_r2,
            "cv_std_r2": self.cv_std_r2,
            "is_stable": self.is_stable,
            "alpha": self.alpha
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)