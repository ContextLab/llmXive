from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json
from pathlib import Path


class SynchronizationStatus(Enum):
    """Enumeration of possible synchronization states."""
    NOT_SYNCHRONIZED = "not_synchronized"
    SYNCHRONIZED = "synchronized"
    UNKNOWN = "unknown"


@dataclass
class NetworkGraph:
    """
    Represents a network graph with its topological properties.

    Attributes:
        id: Unique identifier for the graph (e.g., filename or dataset ID).
        num_nodes: Total number of nodes in the graph.
        num_edges: Total number of edges in the graph.
        is_connected: Boolean indicating if the graph is connected.
        topological_metrics: Dictionary containing computed metrics
            (degree_distribution, clustering_coefficient, average_path_length, etc.).
        raw_data_path: Optional path to the source data file.
    """
    id: str
    num_nodes: int
    num_edges: int
    is_connected: bool
    topological_metrics: Dict[str, Any] = field(default_factory=dict)
    raw_data_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the NetworkGraph instance to a dictionary."""
        return {
            "id": self.id,
            "num_nodes": self.num_nodes,
            "num_edges": self.num_edges,
            "is_connected": self.is_connected,
            "topological_metrics": self.topological_metrics,
            "raw_data_path": str(self.raw_data_path) if self.raw_data_path else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NetworkGraph":
        """Create a NetworkGraph instance from a dictionary."""
        raw_path = data.get("raw_data_path")
        return cls(
            id=data["id"],
            num_nodes=data["num_nodes"],
            num_edges=data["num_edges"],
            is_connected=data["is_connected"],
            topological_metrics=data.get("topological_metrics", {}),
            raw_data_path=Path(raw_path) if raw_path else None
        )


@dataclass
class SimulationResult:
    """
    Stores the results of a Kuramoto synchronization simulation.

    Attributes:
        graph_id: The ID of the graph this simulation ran on.
        critical_coupling: The estimated critical coupling strength (K_c).
            If the graph is disconnected or synchronization never achieved,
            this may be float('inf').
        status: The final synchronization status (Synchronized, Not Synchronized, etc.).
        simulation_params: Dictionary of parameters used (N, dt, t_max, K_sweep_range, etc.).
        order_parameter_trace: List of order parameter values over time (optional).
        raw_results_path: Optional path to detailed raw simulation data.
    """
    graph_id: str
    critical_coupling: float
    status: SynchronizationStatus
    simulation_params: Dict[str, Any] = field(default_factory=dict)
    order_parameter_trace: Optional[List[float]] = None
    raw_results_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the SimulationResult instance to a dictionary."""
        return {
            "graph_id": self.graph_id,
            "critical_coupling": self.critical_coupling if self.critical_coupling != float('inf') else "infinity",
            "status": self.status.value,
            "simulation_params": self.simulation_params,
            "order_parameter_trace": self.order_parameter_trace,
            "raw_results_path": str(self.raw_results_path) if self.raw_results_path else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationResult":
        """Create a SimulationResult instance from a dictionary."""
        raw_path = data.get("raw_results_path")
        crit_k = data["critical_coupling"]
        if crit_k == "infinity":
            crit_k = float('inf')

        return cls(
            graph_id=data["graph_id"],
            critical_coupling=crit_k,
            status=SynchronizationStatus(data["status"]),
            simulation_params=data.get("simulation_params", {}),
            order_parameter_trace=data.get("order_parameter_trace"),
            raw_results_path=Path(raw_path) if raw_path else None
        )


@dataclass
class RegressionModel:
    """
    Represents a fitted regression model analyzing the relationship between
    topological features and synchronization thresholds.

    Attributes:
        model_type: Type of model used (e.g., 'Linear', 'Polynomial', 'Ridge').
        features: List of feature names used in the model.
        coefficients: List of coefficients corresponding to features.
        intercept: The intercept term of the model.
        r_squared: The R-squared value of the fit.
        p_values: List of p-values for each coefficient.
        vif_scores: Optional list of Variance Inflation Factor scores.
        cross_validation_scores: Optional list of CV R-squared scores.
        is_stable: Boolean indicating if the model is stable (low CV variance).
        raw_results_path: Optional path to detailed regression data.
    """
    model_type: str
    features: List[str]
    coefficients: List[float]
    intercept: float
    r_squared: float
    p_values: List[float]
    vif_scores: Optional[List[float]] = None
    cross_validation_scores: Optional[List[float]] = None
    is_stable: bool = True
    raw_results_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the RegressionModel instance to a dictionary."""
        return {
            "model_type": self.model_type,
            "features": self.features,
            "coefficients": self.coefficients,
            "intercept": self.intercept,
            "r_squared": self.r_squared,
            "p_values": self.p_values,
            "vif_scores": self.vif_scores,
            "cross_validation_scores": self.cross_validation_scores,
            "is_stable": self.is_stable,
            "raw_results_path": str(self.raw_results_path) if self.raw_results_path else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RegressionModel":
        """Create a RegressionModel instance from a dictionary."""
        raw_path = data.get("raw_results_path")
        return cls(
            model_type=data["model_type"],
            features=data["features"],
            coefficients=data["coefficients"],
            intercept=data["intercept"],
            r_squared=data["r_squared"],
            p_values=data["p_values"],
            vif_scores=data.get("vif_scores"),
            cross_validation_scores=data.get("cross_validation_scores"),
            is_stable=data.get("is_stable", True),
            raw_results_path=Path(raw_path) if raw_path else None
        )