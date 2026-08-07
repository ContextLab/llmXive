"""
data/models.py

Defines base data models/entities for the Orca follow-up project.
Includes Pydantic and dataclass versions for flexibility.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
import numpy as np
from pydantic import BaseModel, Field, field_validator
from typing import Union

# Dataclass versions for internal use
@dataclass
class PhysicalScenario:
    """
    Represents a physical scenario from the dataset.
    """
    video_id: str
    original_outcome: str
    counterfactual_prompt: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    optical_flow_magnitude: float = 0.0

@dataclass
class LatentVector:
    """
    Represents a latent vector extracted from the model.
    """
    scenario_id: str
    vector: np.ndarray
    prompt: str
    dim: int

    def __post_init__(self):
        if not isinstance(self.vector, np.ndarray):
            self.vector = np.array(self.vector)
        if self.dim != len(self.vector):
            raise ValueError(f"Dimension mismatch: expected {len(self.vector)}, got {self.dim}")

@dataclass
class CounterfactualEdit:
    """
    Represents a counterfactual edit applied to a latent vector.
    """
    original_latent: LatentVector
    modified_latent: LatentVector
    edit_vector: np.ndarray
    edit_type: str  # e.g., "vector_arithmetic", "zero_mask"
    ambiguous_flag: int = 0  # 0 = valid, 1 = ambiguous

    def __post_init__(self):
        if not isinstance(self.edit_vector, np.ndarray):
            self.edit_vector = np.array(self.edit_vector)

# Pydantic versions for serialization/API
class PhysicalScenarioPydantic(BaseModel):
    video_id: str
    original_outcome: str
    counterfactual_prompt: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    optical_flow_magnitude: float = 0.0

class LatentVectorPydantic(BaseModel):
    scenario_id: str
    vector: List[float]  # JSON serializable
    prompt: str
    dim: int

    @field_validator('vector')
    def validate_vector(cls, v):
        if not isinstance(v, list):
            v = v.tolist()
        return v

class CounterfactualEditPydantic(BaseModel):
    original_latent_id: str
    modified_latent_id: str
    edit_vector: List[float]
    edit_type: str
    ambiguous_flag: int = 0

    @field_validator('edit_vector')
    def validate_edit_vector(cls, v):
        if not isinstance(v, list):
            v = v.tolist()
        return v
