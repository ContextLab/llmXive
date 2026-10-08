"""
Data models for the Network Synchronization Impact project.

Defines core entities: SynchronizationStatus, NetworkGraph, SimulationResult, and RegressionModel.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json
from pathlib import Path
import networkx as nx


class SynchronizationStatus(Enum):
    """Enumeration of possible synchronization outcomes."""
    NOT_SYNCHRONIZED = "not_synchronized"
    PARTIALLY_SYNCHRONIZED = "partially_synchronized"
    FULLY_SYNCHRONIZED = "fully_synchronized"
    INDETERMINATE = "indeterminate"


@dataclass
class NetworkGraph:
    """
    Represents a network graph with its topological properties.

    Attributes:
        id: Unique identifier for the network.
        graph: The NetworkX graph object.
        source: Source of the data (e.g., 'SNAP', 'NetworkRepository').
        metrics: Dictionary of computed topological metrics.
    """
    id: str
    graph: nx.Graph
    source: str = "unknown"
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert NetworkGraph to a dictionary for serialization."""
        return {
            "id": self.id,
            "source": self.source,
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "is_connected": nx.is_connected(self.graph) if self.graph.number_of_nodes() > 0 else False,
            "metrics": self.metrics
        }


@dataclass
class SimulationResult:
    """
    Represents the result of a Kuramoto synchronization simulation.

    Attributes:
        network_id: ID of the network simulated.
        critical_coupling: The estimated critical coupling strength (K_c).
        status: Final synchronization status.
        order_parameter_trace: List of order parameter values over time (optional).
        runtime_seconds: Time taken to run the simulation.
        parameters: Dictionary of simulation parameters used.
    """
    network_id: str
    critical_coupling: Optional[float]
    status: SynchronizationStatus
    order_parameter_trace: Optional[List[float]] = None
    runtime_seconds: float = 0.0
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert SimulationResult to a dictionary for serialization."""
        return {
            "network_id": self.network_id,
            "critical_coupling": self.critical_coupling,
            "status": self.status.value,
            "runtime_seconds": self.runtime_seconds,
            "parameters": self.parameters
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


@dataclass
class RegressionModel:
    """
    Represents a fitted regression model analyzing topology vs. synchronization.

    Attributes:
        model_type: Type of model (e.g., 'Linear', 'Polynomial', 'Ridge').
        coefficients: Dictionary mapping feature names to coefficients.
        r_squared: Coefficient of determination.
        p_values: Dictionary mapping feature names to p-values.
        remediation_action: Description of any VIF remediation taken.
        cross_validation_stats: Dictionary with CV results (mean_r2, std_dev).
    """
    model_type: str
    coefficients: Dict[str, float]
    r_squared: float
    p_values: Dict[str, float]
    remediation_action: Optional[str] = None
    cross_validation_stats: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert RegressionModel to a dictionary for serialization."""
        result = {
            "model_type": self.model_type,
            "coefficients": self.coefficients,
            "r_squared": self.r_squared,
            "p_values": self.p_values
        }
        if self.remediation_action:
            result["remediation_action"] = self.remediation_action
        if self.cross_validation_stats:
            result["cross_validation_stats"] = self.cross_validation_stats
        return result

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)