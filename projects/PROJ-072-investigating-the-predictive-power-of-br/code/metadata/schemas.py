"""
Pydantic schemas for data validation in the Brain Network Metrics project.

These classes correspond to the definitions in data/metadata/schema.yaml
and are used to validate data ingestion, processing, and output artifacts.
"""
from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing_extensions import Annotated


class Subject(BaseModel):
    """Represents a single participant in the study."""
    model_config = ConfigDict(strict=True)

    subject_id: Annotated[str, Field(pattern=r"^sub-\d+$", description="Unique identifier")]
    diagnosis: Annotated[str, Field(enum=["SZ", "HC"], description="Diagnostic label")]
    age: Annotated[float, Field(ge=18, le=100, description="Age in years")]
    sex: Annotated[str, Field(enum=["M", "F"], description="Biological sex")]
    motion_flag: bool = Field(default=False, description="True if excluded due to motion")
    exclusion_reason: Optional[str] = Field(default=None, description="Reason if excluded")
    medication_status: Optional[str] = Field(default=None, description="Medication status")

    @field_validator('subject_id')
    @classmethod
    def validate_subject_id(cls, v: str) -> str:
        if not v.startswith("sub-"):
            raise ValueError("Subject ID must start with 'sub-'")
        return v


class ConnectivityMatrix(BaseModel):
    """Represents a functional connectivity matrix for a subject."""
    model_config = ConfigDict(strict=True)

    subject_id: str = Field(pattern=r"^sub-\d+$", description="Reference to Subject ID")
    matrix_path: str = Field(
        pattern=r"^data/processed/.*\.(npy|csv)$",
        description="Path to the matrix file"
    )
    atlas: str = Field(default="AAL", description="Atlas used")
    dimension: int = Field(gt=0, description="Matrix dimension")
    is_psd: bool = Field(default=False, description="Positive semi-definite flag")
    regularization_applied: bool = Field(default=False, description="Regularization flag")

    @field_validator('matrix_path')
    @classmethod
    def validate_path(cls, v: str) -> str:
        if not v.startswith("data/processed/"):
            raise ValueError("Matrix path must be under data/processed/")
        return v


class FeatureVector(BaseModel):
    """Represents the extracted graph metrics for a subject."""
    model_config = ConfigDict(strict=True)

    subject_id: str = Field(pattern=r"^sub-\d+$", description="Reference to Subject ID")
    global_efficiency: float = Field(ge=0.0, le=1.0, description="Global efficiency")
    local_efficiency: float = Field(ge=0.0, le=1.0, description="Local efficiency")
    modularity: float = Field(description="Modularity score")
    betweenness_centrality_mean: float = Field(description="Mean betweenness centrality")
    prefrontal_centrality: float = Field(description="Prefrontal ROI centrality")
    hippocampal_centrality: float = Field(description="Hippocampal ROI centrality")
    feature_vector_path: Optional[str] = Field(
        default=None,
        pattern=r"^data/processed/.*\.csv$",
        description="Path to full feature vector"
    )

    @field_validator('feature_vector_path')
    @classmethod
    def validate_feature_path(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith("data/processed/"):
            raise ValueError("Feature vector path must be under data/processed/")
        return v


# Type aliases for convenience
SubjectList = List[Subject]
MatrixList = List[ConnectivityMatrix]
FeatureList = List[FeatureVector]
