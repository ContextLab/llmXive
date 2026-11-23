"""
Data models for the Network Synchronization Impact project.

This module defines the core dataclasses used throughout the pipeline,
mirroring the JSON schemas located in the ``contracts/`` directory.
It re‑exports the existing ``SynchronizationStatus``, ``SimulationResult``,
and ``RegressionModel`` definitions from the top‑level ``data_models`` module
to avoid duplication, and adds the ``TopologicalMetrics`` dataclass as well
as a refined ``NetworkGraph`` that references it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import networkx as nx

# Re‑export existing core models to keep a single source of truth.
# The top‑level ``data_models`` module (located at ``code/data_models.py``)
# already defines ``SynchronizationStatus``, ``SimulationResult`` and
# ``RegressionModel``. Import them here and expose them as part of the
# ``src.data_models`` public API.
from data_models import SynchronizationStatus, SimulationResult, RegressionModel

__all__ = [
    "SynchronizationStatus",
    "SimulationResult",
    "RegressionModel",
    "TopologicalMetrics",
    "NetworkGraph",
]

@dataclass
class TopologicalMetrics:
    """
    Topological metrics required by the specification.

    Attributes
    ----------
    mean_degree: float
        Average degree of the graph (⟨k⟩).
    degree_variance: float
        Variance of the degree distribution.
    clustering_coefficient: float
        Global clustering coefficient (transitivity) in the range [0, 1].
    average_path_length: Optional[float]
        Mean shortest‑path length. ``None`` (or ``float('inf')``) indicates
        a disconnected graph where the path length is undefined.
    """
    mean_degree: float
    degree_variance: float
    clustering_coefficient: float
    average_path_length: Optional[float] = None

@dataclass
class NetworkGraph:
    """
    Representation of a network dataset.

    The ``metrics`` field is an instance of :class:`TopologicalMetrics`,
    matching the ``network_metrics.schema.yaml`` contract.

    Attributes
    ----------
    id: str
        Unique identifier for the network (e.g., filename without extension).
    graph: nx.Graph
        The NetworkX graph object containing the adjacency information.
    source: str, default ``"unknown"``
        Origin of the dataset (e.g., ``"SNAP"``, ``"NetworkRepository"``).
    metrics: TopologicalMetrics
        Computed topological metrics for the graph.
    """
    id: str
    graph: nx.Graph
    source: str = "unknown"
    metrics: TopologicalMetrics = field(
        default_factory=lambda: TopologicalMetrics(
            mean_degree=0.0,
            degree_variance=0.0,
            clustering_coefficient=0.0,
            average_path_length=None,
        )
    )

    def to_dict(self) -> dict:
        """
        Serialize the ``NetworkGraph`` to a plain‑Python dictionary that can be
        written to JSON. The ``graph`` object itself is not serialised; only
        its size and connectivity information are included.
        """
        return {
            "id": self.id,
            "source": self.source,
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "is_connected": nx.is_connected(self.graph)
            if self.graph.number_of_nodes() > 0
            else False,
            "metrics": {
                "mean_degree": self.metrics.mean_degree,
                "degree_variance": self.metrics.degree_variance,
                "clustering_coefficient": self.metrics.clustering_coefficient,
                "average_path_length": self.metrics.average_path_length,
            },
        }