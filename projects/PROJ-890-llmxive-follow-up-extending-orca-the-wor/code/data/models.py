"""
Base data models and entities for the llmXive Orca follow-up project.

This module defines the core data structures used throughout the pipeline:
- PhysicalScenario: Represents a physical interaction scenario
- LatentVector: Represents a frozen latent vector extracted from the Orca model
- CounterfactualEdit: Represents a counterfactual modification to a scenario
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
import numpy as np

from pydantic import BaseModel, Field, field_validator
from typing import Union


@dataclass
class PhysicalScenario:
    """
    Represents a physical interaction scenario from the Orca dataset.
    
    Attributes:
        scenario_id: Unique identifier for the scenario
        video_id: ID of the source video
        prompt: Natural language prompt describing the scenario
        original_outcome: The actual physical outcome observed
        optical_flow_magnitude: Magnitude of optical flow in the video clip
        metadata: Additional metadata about the scenario
    """
    scenario_id: str = field(default_factory=lambda: str(uuid4()))
    video_id: str = ""
    prompt: str = ""
    original_outcome: str = ""
    optical_flow_magnitude: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.scenario_id:
            self.scenario_id = str(uuid4())


@dataclass
class LatentVector:
    """
    Represents a frozen latent vector extracted from the Orca model.
    
    Attributes:
        vector_id: Unique identifier for the latent vector
        scenario_id: ID of the source PhysicalScenario
        vector: Numpy array containing the latent vector values
        vector_shape: Shape of the vector (for validation)
        extraction_timestamp: When the vector was extracted
        model_version: Version of the Orca model used
    """
    vector_id: str = field(default_factory=lambda: str(uuid4()))
    scenario_id: str = ""
    vector: Optional[np.ndarray] = None
    vector_shape: Tuple[int, ...] = ()
    extraction_timestamp: str = ""
    model_version: str = "orca-v1"

    def __post_init__(self):
        if self.vector is not None:
            self.vector_shape = self.vector.shape
        if not self.extraction_timestamp:
            from datetime import datetime
            self.extraction_timestamp = datetime.now().isoformat()


@dataclass
class CounterfactualEdit:
    """
    Represents a counterfactual modification to a scenario.
    
    Attributes:
        edit_id: Unique identifier for the edit
        original_scenario_id: ID of the original PhysicalScenario
        modified_latent_id: ID of the modified LatentVector
        counterfactual_prompt: The counterfactual prompt describing the edit
        expected_outcome: The expected physical outcome of the edit
        edit_method: Method used to create the edit (e.g., "vector_arithmetic", "zero_mask")
        ambiguity_flag: Whether the prompt was considered ambiguous (0=valid, 1=ambiguous)
    """
    edit_id: str = field(default_factory=lambda: str(uuid4()))
    original_scenario_id: str = ""
    modified_latent_id: str = ""
    counterfactual_prompt: str = ""
    expected_outcome: str = ""
    edit_method: str = "vector_arithmetic"
    ambiguity_flag: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.edit_id:
            self.edit_id = str(uuid4())


# Pydantic models for API serialization
class PhysicalScenarioPydantic(BaseModel):
    """Pydantic version of PhysicalScenario for API serialization."""
    scenario_id: str
    video_id: str
    prompt: str
    original_outcome: str
    optical_flow_magnitude: float
    metadata: Dict[str, Any] = {}

    @field_validator('optical_flow_magnitude')
    @classmethod
    def validate_flow_magnitude(cls, v: float) -> float:
        if v < 0:
            raise ValueError('optical_flow_magnitude must be non-negative')
        return v


class LatentVectorPydantic(BaseModel):
    """Pydantic version of LatentVector for API serialization."""
    vector_id: str
    scenario_id: str
    vector_shape: Tuple[int, ...]
    extraction_timestamp: str
    model_version: str
    # Vector data as list for JSON serialization
    vector_data: Optional[List[float]] = None

    @field_validator('vector_shape')
    @classmethod
    def validate_shape(cls, v: Tuple[int, ...]) -> Tuple[int, ...]:
        if len(v) == 0:
            raise ValueError('vector_shape cannot be empty')
        return v


class CounterfactualEditPydantic(BaseModel):
    """Pydantic version of CounterfactualEdit for API serialization."""
    edit_id: str
    original_scenario_id: str
    modified_latent_id: str
    counterfactual_prompt: str
    expected_outcome: str
    edit_method: str
    ambiguity_flag: int
    metadata: Dict[str, Any] = {}

    @field_validator('ambiguity_flag')
    @classmethod
    def validate_ambiguity_flag(cls, v: int) -> int:
        if v not in (0, 1):
            raise ValueError('ambiguity_flag must be 0 or 1')
        return v