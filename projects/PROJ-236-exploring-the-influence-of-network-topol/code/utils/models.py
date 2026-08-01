"""
Pydantic data models for the project.

This module defines the core data entities used throughout the pipeline:
- ``NetworkRealization``: captures the description of a generated network
  topology, including its identifier, type, cutoff distance, and adjacency
  matrix.
- ``TransportResult``: stores the outcome of a thermal transport calculation
  for a given network realization.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, validator


class NetworkRealization(BaseModel):
    """
    Base entity representing a single network realization.

    Attributes
    ----------
    network_id: str
        Unique identifier for the network realization.
    topology_type: str
        Type of topology (e.g., ``small_world``, ``scale_free``, ``random``).
    cutoff: float
        Distance cutoff used to create edges (in Å or appropriate units).
    adjacency: List[List[int]]
        Square adjacency matrix where ``1`` indicates an edge and ``0`` no edge.
    """

    network_id: str = Field(..., description="Unique identifier for the network.")
    topology_type: str = Field(..., description="Topology type of the network.")
    cutoff: float = Field(..., gt=0, description="Cutoff distance used for edge creation.")
    adjacency: List[List[int]] = Field(
        ..., description="Square adjacency matrix representing the graph."
    )

    @validator("adjacency")
    def adjacency_must_be_square(cls, v):
        if not isinstance(v, list) or not all(isinstance(row, list) for row in v):
            raise ValueError("Adjacency must be a list of lists.")
        size = len(v)
        if size == 0:
            raise ValueError("Adjacency matrix cannot be empty.")
        for row in v:
            if len(row) != size:
                raise ValueError("Adjacency matrix must be square.")
            for val in row:
                if val not in (0, 1):
                    raise ValueError("Adjacency entries must be 0 or 1.")
        return v


class TransportResult(BaseModel):
    """
    Base entity representing the result of a transport calculation.

    Attributes
    ----------
    network_id: str
        Identifier linking the result back to a ``NetworkRealization``.
    kappa: float
        Effective thermal conductivity (W/m·K). Must be positive.
    error_estimate: float
        Estimated uncertainty of ``kappa``.
    convergence_status: bool
        Whether the solver converged.
    runtime: float
        Computation time in seconds.
    regime_flag: str
        Label indicating the transport regime (e.g., ``diffusive``, ``ballistic``).
    """

    network_id: str = Field(..., description="Identifier of the associated network.")
    kappa: float = Field(..., gt=0, description="Thermal conductivity (W/m·K).")
    error_estimate: float = Field(..., ge=0, description="Uncertainty of kappa.")
    convergence_status: bool = Field(..., description="Solver convergence flag.")
    runtime: float = Field(..., gt=0, description="Runtime in seconds.")
    regime_flag: str = Field(..., description="Transport regime identifier.")
