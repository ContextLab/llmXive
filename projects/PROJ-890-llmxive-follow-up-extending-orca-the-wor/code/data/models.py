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
    Used for internal processing of video metadata and outcomes.
    """
    video_id: str
    original_outcome: str
    counterfactual_prompt: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    optical_flow_magnitude: float = 0.0

    @property
    def scenario_id(self) -> str:
        """Generate a stable ID based on video_id for consistency."""
        return f"scenario_{self.video_id}"

@dataclass
class LatentVector:
    """
    Represents a latent vector extracted from the model.
    Stores the embedding and associated metadata.
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
        if self.vector.dtype not in [np.float32, np.float64]:
            self.vector = self.vector.astype(np.float32)

@dataclass
class CounterfactualEdit:
    """
    Represents a counterfactual edit applied to a latent vector.
    Tracks the transformation from original to modified latent space.
    """
    original_latent: LatentVector
    modified_latent: LatentVector
    edit_vector: np.ndarray
    edit_type: str  # e.g., "vector_arithmetic", "zero_mask"
    ambiguous_flag: int = 0  # 0 = valid, 1 = ambiguous

    def __post_init__(self):
        if not isinstance(self.edit_vector, np.ndarray):
            self.edit_vector = np.array(self.edit_vector)
        if self.edit_vector.dtype not in [np.float32, np.float64]:
            self.edit_vector = self.edit_vector.astype(np.float32)

    def apply_edit(self) -> np.ndarray:
        """
        Apply the edit vector to the original latent to get the modified latent.
        This is a verification helper.
        """
        if self.edit_type == "vector_arithmetic":
            return self.original_latent.vector + self.edit_vector
        elif self.edit_type == "zero_mask":
            return self.modified_latent.vector
        else:
            raise ValueError(f"Unknown edit type: {self.edit_type}")

# Pydantic versions for serialization/API
class PhysicalScenarioPydantic(BaseModel):
    video_id: str
    original_outcome: str
    counterfactual_prompt: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    optical_flow_magnitude: float = 0.0

    class Config:
        arbitrary_types_allowed = False

class LatentVectorPydantic(BaseModel):
    scenario_id: str
    vector: List[float]  # JSON serializable
    prompt: str
    dim: int

    @field_validator('vector')
    def validate_vector(cls, v):
        if not isinstance(v, list):
            if hasattr(v, 'tolist'):
                v = v.tolist()
            else:
                v = list(v)
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
            if hasattr(v, 'tolist'):
                v = v.tolist()
            else:
                v = list(v)
        return v