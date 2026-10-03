"""
Data models for the network synchronization impact study.
Defines core entities: NetworkGraph, SimulationResult, RegressionModel.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json
from pathlib import Path
import networkx as nx


class SynchronizationStatus(Enum):
    """Enumeration of synchronization states."""
    NOT_SYNCHRONIZED = "not_synchronized"
    PARTIALLY_SYNCHRONIZED = "partially_synchronized"
    FULLY_SYNCHRONIZED = "fully_synchronized"
    DISCONNECTED = "disconnected"


@dataclass
class NetworkGraph:
    """
    Represents a network graph with its topological properties.
    
    Attributes:
        id: Unique identifier for the network (e.g., filename or SNAP ID)
        graph: The NetworkX graph object
        degree_distribution: Dict mapping degree to frequency
        clustering_coefficient: Average clustering coefficient
        average_path_length: Average shortest path length (float('inf') if disconnected)
        num_nodes: Number of nodes
        num_edges: Number of edges
        is_connected: Boolean indicating if the graph is connected
    """
    id: str
    graph: nx.Graph
    degree_distribution: Dict[int, int] = field(default_factory=dict)
    clustering_coefficient: float = 0.0
    average_path_length: float = float('inf')
    num_nodes: int = 0
    num_edges: int = 0
    is_connected: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "num_nodes": self.num_nodes,
            "num_edges": self.num_edges,
            "is_connected": self.is_connected,
            "clustering_coefficient": self.clustering_coefficient,
            "average_path_length": self.average_path_length if self.average_path_length != float('inf') else None,
            "degree_distribution": self.degree_distribution
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NetworkGraph':
        """Create NetworkGraph from dictionary (graph object must be reconstructed separately)."""
        # Note: The actual nx.Graph object cannot be directly serialized/deserialized this way
        # This is for metadata only
        return cls(
            id=data["id"],
            graph=None,  # Must be loaded separately
            degree_distribution=data.get("degree_distribution", {}),
            clustering_coefficient=data.get("clustering_coefficient", 0.0),
            average_path_length=data.get("average_path_length", float('inf')) or float('inf'),
            num_nodes=data.get("num_nodes", 0),
            num_edges=data.get("num_edges", 0),
            is_connected=data.get("is_connected", False)
        )


@dataclass
class SimulationResult:
    """
    Represents the result of a Kuramoto synchronization simulation.
    
    Attributes:
        network_id: ID of the network that was simulated
        critical_coupling: The critical coupling strength K where synchronization occurs
        status: SynchronizationStatus enum indicating the outcome
        order_parameter_trace: List of order parameter values over time
        time_trace: List of time points corresponding to order_parameter_trace
        metrics: Dict of topological metrics at time of simulation
        parameters: Dict of simulation parameters used (N, dt, t_max, etc.)
    """
    network_id: str
    critical_coupling: Optional[float]  # float('inf') if disconnected or not found
    status: SynchronizationStatus
    order_parameter_trace: List[float] = field(default_factory=list)
    time_trace: List[float] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "network_id": self.network_id,
            "status": self.status.value,
            "metrics": self.metrics,
            "parameters": self.parameters,
            "order_parameter_trace": self.order_parameter_trace,
            "time_trace": self.time_trace
        }
        
        # Handle special float cases
        if self.critical_coupling is None:
            result["critical_coupling"] = None
        elif self.critical_coupling == float('inf'):
            result["critical_coupling"] = "infinity"
        else:
            result["critical_coupling"] = self.critical_coupling
            
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationResult':
        """Create SimulationResult from dictionary."""
        critical_k = data.get("critical_coupling")
        if critical_k == "infinity":
            critical_k = float('inf')
        elif critical_k is None:
            critical_k = None
        else:
            critical_k = float(critical_k) if critical_k is not None else None

        return cls(
            network_id=data["network_id"],
            critical_coupling=critical_k,
            status=SynchronizationStatus(data["status"]),
            order_parameter_trace=data.get("order_parameter_trace", []),
            time_trace=data.get("time_trace", []),
            metrics=data.get("metrics", {}),
            parameters=data.get("parameters", {})
        )


@dataclass
class RegressionModel:
    """
    Represents a fitted regression model analyzing the relationship between
    topological features and synchronization thresholds.
    
    Attributes:
        model_type: Type of model ('linear', 'polynomial', 'ridge')
        coefficients: Dict mapping feature names to coefficients
        intercept: Model intercept
        r_squared: Coefficient of determination
        p_values: Dict mapping feature names to p-values
        vif_scores: Dict mapping feature names to VIF scores (if computed)
        remediation_action: String describing any remediation taken (e.g., feature removal)
        cross_validation_results: Dict with CV results (mean_r2, std_dev, etc.)
        is_valid: Boolean indicating if the model passed validation checks
    """
    model_type: str
    coefficients: Dict[str, float]
    intercept: float
    r_squared: float
    p_values: Dict[str, float]
    vif_scores: Optional[Dict[str, float]] = None
    remediation_action: Optional[str] = None
    cross_validation_results: Optional[Dict[str, float]] = None
    is_valid: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "model_type": self.model_type,
            "coefficients": self.coefficients,
            "intercept": self.intercept,
            "r_squared": self.r_squared,
            "p_values": self.p_values,
            "vif_scores": self.vif_scores,
            "remediation_action": self.remediation_action,
            "cross_validation_results": self.cross_validation_results,
            "is_valid": self.is_valid
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RegressionModel':
        """Create RegressionModel from dictionary."""
        return cls(
            model_type=data["model_type"],
            coefficients=data["coefficients"],
            intercept=data["intercept"],
            r_squared=data["r_squared"],
            p_values=data["p_values"],
            vif_scores=data.get("vif_scores"),
            remediation_action=data.get("remediation_action"),
            cross_validation_results=data.get("cross_validation_results"),
            is_valid=data.get("is_valid", True)
        )

    def save_to_json(self, path: Path) -> None:
        """Save the model summary to a JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_json(cls, path: Path) -> 'RegressionModel':
        """Load a model from a JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)