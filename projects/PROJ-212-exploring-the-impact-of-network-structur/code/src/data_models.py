from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json
from pathlib import Path
import networkx as nx

class SynchronizationStatus(Enum):
    """Enumeration for synchronization status."""
    SYNCED = "synced"
    UNSYNCED = "unsynced"
    INCONCLUSIVE = "inconclusive"

@dataclass
class NetworkGraph:
    """
    Data class representing a network graph.

    Attributes:
        id: Unique identifier for the graph.
        graph: The NetworkX graph object.
        source: Source of the graph data (e.g., 'SNAP', 'synthetic').
        metadata: Additional metadata about the graph.
    """
    id: str
    graph: nx.Graph
    source: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SimulationResult:
    """
    Data class representing the result of a Kuramoto simulation.

    Attributes:
        graph_id: ID of the graph simulated.
        threshold: Critical coupling strength found (or infinity if disconnected).
        metrics: Topological metrics computed for the graph.
        status: Synchronization status.
        details: Additional details about the simulation.
    """
    graph_id: str
    threshold: float
    metrics: Dict[str, Any]
    status: SynchronizationStatus
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RegressionModel:
    """
    Data class representing a regression model result.

    Attributes:
        model_type: Type of regression model (e.g., 'linear', 'ridge').
        coefficients: Dictionary of feature names to coefficients.
        r_squared: R-squared value.
        p_values: Dictionary of feature names to p-values.
        vif_scores: Dictionary of feature names to VIF scores.
        cv_mean_r2: Mean R-squared from cross-validation.
        cv_std_r2: Standard deviation of R-squared from cross-validation.
        is_stable: Boolean indicating if the model is stable based on CV std dev.
    """
    model_type: str
    coefficients: Dict[str, float]
    r_squared: float
    p_values: Dict[str, float]
    vif_scores: Dict[str, float]
    cv_mean_r2: float
    cv_std_r2: float
    is_stable: bool
    features: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)