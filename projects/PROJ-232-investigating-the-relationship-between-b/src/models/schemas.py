"""
Pydantic models for the Brain-Music-Emotion project.

Defines data contracts for Subject, ConnectivityMatrix, NetworkMetrics, and BehavioralScore.
These models enforce schema validation for data flowing through the pipeline.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator
import numpy as np

# Type aliases for clarity
MatrixData = List[List[float]]
VectorData = List[float]

class Subject(BaseModel):
    """
    Represents a single study participant.
    
    Attributes:
        subject_id: Unique identifier for the subject (e.g., 'sub-001').
        age: Age in years.
        sex: Biological sex ('M' or 'F').
        handedness: Hand preference ('L', 'R', or 'A').
    """
    subject_id: str = Field(..., description="Unique subject identifier")
    age: int = Field(..., ge=0, le=120, description="Age in years")
    sex: str = Field(..., pattern="^[MF]$", description="Sex (M/F)")
    handedness: Optional[str] = Field(None, pattern="^[LAR]$", description="Handedness (L/R/A)")

    @field_validator('subject_id')
    @classmethod
    def validate_subject_id(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Subject ID cannot be empty")
        return v


class ConnectivityMatrix(BaseModel):
    """
    Represents a functional connectivity matrix derived from fMRI time series.
    
    Attributes:
        subject_id: Link to the subject.
        matrix: 2D list of correlation coefficients.
        atlas_name: Name of the parcellation atlas used (e.g., 'Schaefer200').
        n_nodes: Number of nodes (should match len(matrix)).
        method: Correlation method used (e.g., 'pearson').
    """
    subject_id: str
    matrix: MatrixData
    atlas_name: str = Field(..., description="Atlas name")
    n_nodes: int = Field(..., description="Number of nodes")
    method: str = Field(default="pearson", description="Correlation method")

    @model_validator(mode='after')
    def validate_matrix_properties(self) -> 'ConnectivityMatrix':
        # Convert to numpy for easier validation
        try:
            mat = np.array(self.matrix)
        except Exception as e:
            raise ValueError(f"Invalid matrix format: {e}")

        if mat.ndim != 2:
            raise ValueError("Matrix must be 2-dimensional")

        if mat.shape[0] != mat.shape[1]:
            raise ValueError("Matrix must be square")

        if mat.shape[0] != self.n_nodes:
            raise ValueError(f"Matrix shape {mat.shape[0]} does not match n_nodes {self.n_nodes}")

        # Check symmetry
        if not np.allclose(mat, mat.T, atol=1e-5):
            raise ValueError("Matrix must be symmetric")

        # Check diagonal (should be 1.0 for correlation matrices)
        if not np.allclose(np.diag(mat), 1.0, atol=1e-5):
            raise ValueError("Diagonal elements must be 1.0 for correlation matrices")

        # Check range [-1, 1]
        if np.any(mat < -1.0) or np.any(mat > 1.0):
            raise ValueError("Correlation values must be in range [-1, 1]")

        return self

    @field_validator('matrix')
    @classmethod
    def validate_matrix_type(cls, v: MatrixData) -> MatrixData:
        if not isinstance(v, list) or not all(isinstance(row, list) for row in v):
            raise ValueError("Matrix must be a list of lists of floats")
        return v


class NetworkMetrics(BaseModel):
    """
    Graph theoretical metrics calculated from a connectivity matrix.
    
    Attributes:
        subject_id: Link to the subject.
        global_efficiency: Global efficiency of the network.
        modularity: Modularity score (community structure).
        participation_coefficient: Average participation coefficient of nodes.
        network_efficiency: Dictionary mapping network names to local efficiencies.
        edge_strengths: List of edge weights (flattened upper triangle or similar).
    """
    subject_id: str
    global_efficiency: float = Field(..., ge=0.0, description="Global efficiency")
    modularity: float = Field(..., description="Modularity score")
    participation_coefficient: float = Field(..., ge=0.0, description="Average participation coefficient")
    network_efficiency: Dict[str, float] = Field(default_factory=dict, description="Efficiency per network")
    edge_strengths: Optional[List[float]] = Field(None, description="Edge-level connectivity strengths")

    @field_validator('global_efficiency', 'modularity', 'participation_coefficient')
    @classmethod
    def validate_floats(cls, v: float) -> float:
        if np.isnan(v) or np.isinf(v):
            raise ValueError("Metric value cannot be NaN or Infinity")
        return v


class BehavioralScore(BaseModel):
    """
    Behavioral scores related to musical emotion perception.
    
    Attributes:
        subject_id: Link to the subject.
        bmrq_total: Total score on the Brief Music in Mood Regulation scale.
        bmrq_subscores: Dictionary of specific BMRQ subscale scores.
        music_training_years: Years of formal music training.
    """
    subject_id: str
    bmrq_total: float = Field(..., ge=0.0, description="Total BMRQ score")
    bmrq_subscores: Dict[str, float] = Field(default_factory=dict, description="BMRQ subscales")
    music_training_years: float = Field(default=0.0, ge=0.0, description="Years of music training")

    @field_validator('bmrq_total')
    @classmethod
    def validate_bmrq_total(cls, v: float) -> float:
        if np.isnan(v) or np.isinf(v):
            raise ValueError("BMRQ total cannot be NaN or Infinity")
        return v


# Unified data record for analysis
class AnalysisRecord(BaseModel):
    """
    A joined record containing subject info, connectivity, metrics, and behavior.
    Used for statistical modeling.
    """
    subject: Subject
    connectivity: ConnectivityMatrix
    metrics: NetworkMetrics
    behavior: BehavioralScore

    @model_validator(mode='after')
    def check_subject_id_consistency(self) -> 'AnalysisRecord':
        ids = [
            self.subject.subject_id,
            self.connectivity.subject_id,
            self.metrics.subject_id,
            self.behavior.subject_id
        ]
        if len(set(ids)) != 1:
            raise ValueError("All subject IDs in the analysis record must match")
        return self
