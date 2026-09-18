from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json
from pathlib import Path
import networkx as nx


class SynchronizationStatus(Enum):
    """Enum representing the synchronization state of a network."""
    UNSYNCHRONIZED = "unsynchronized"
    PARTIALLY_SYNCHRONIZED = "partially_synchronized"
    SYNCHRONIZED = "synchronized"
    DISCONNECTED = "disconnected"


@dataclass
class NetworkGraph:
    """
    Represents a network graph with its associated metadata.
    
    Attributes:
        id: Unique identifier for the network (e.g., SNAP dataset ID).
        graph: The NetworkX graph object.
        source: Source of the data (e.g., 'SNAP', 'synthetic').
        path: Optional path to the source file.
        metrics_cache: Cached topological metrics to avoid recomputation.
    """
    id: str
    graph: nx.Graph
    source: str = "unknown"
    path: Optional[Path] = None
    metrics_cache: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the NetworkGraph to a dictionary representation."""
        return {
            "id": self.id,
            "source": self.source,
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "is_connected": nx.is_connected(self.graph) if self.graph.number_of_nodes() > 0 else False,
            "path": str(self.path) if self.path else None
        }


@dataclass
class SimulationResult:
    """
    Represents the result of a Kuramoto synchronization simulation.
    
    Attributes:
        network_id: ID of the network simulated.
        critical_coupling: The estimated critical coupling strength (K) where synchronization occurs.
            If the graph is disconnected, this may be None or infinity.
        status: The final synchronization status.
        order_parameter_trace: List of order parameter values over time (optional).
        config: Dictionary of simulation parameters used (e.g., dt, T_max).
        raw_data_path: Optional path to a file containing detailed time-series data.
    """
    network_id: str
    critical_coupling: Optional[float]
    status: SynchronizationStatus
    order_parameter_trace: Optional[List[float]] = None
    config: Dict[str, Any] = field(default_factory=dict)
    raw_data_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the SimulationResult to a dictionary for JSON serialization."""
        return {
            "network_id": self.network_id,
            "critical_coupling": self.critical_coupling,
            "status": self.status.value,
            "config": self.config,
            "raw_data_path": str(self.raw_data_path) if self.raw_data_path else None
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the result to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


@dataclass
class RegressionModel:
    """
    Represents a statistical regression model analyzing the relationship between
    topological features and synchronization thresholds.
    
    Attributes:
        model_type: Type of model used (e.g., 'linear', 'polynomial', 'ridge').
        coefficients: Dictionary mapping feature names to their coefficients.
        r_squared: Coefficient of determination.
        p_values: Dictionary mapping feature names to their p-values.
        features_used: List of feature names included in the model.
        vif_scores: Optional dictionary of Variance Inflation Factor scores for features.
        cross_validation_scores: List of R² scores from cross-validation.
        stability_flag: Boolean indicating if the model is stable (CV std dev <= 0.1).
        summary_path: Optional path to a detailed summary file.
    """
    model_type: str
    coefficients: Dict[str, float]
    r_squared: float
    p_values: Dict[str, float]
    features_used: List[str]
    vif_scores: Optional[Dict[str, float]] = None
    cross_validation_scores: Optional[List[float]] = None
    stability_flag: bool = True
    summary_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the RegressionModel to a dictionary for JSON serialization."""
        return {
            "model_type": self.model_type,
            "coefficients": self.coefficients,
            "r_squared": self.r_squared,
            "p_values": self.p_values,
            "features_used": self.features_used,
            "vif_scores": self.vif_scores,
            "cross_validation_scores": self.cross_validation_scores,
            "stability_flag": self.stability_flag,
            "summary_path": str(self.summary_path) if self.summary_path else None
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the model to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)