"""
Data models using Pydantic for the asymptotic behavior of random matrix eigenvalues project.

Defines core entities: PerturbationConfig and SimulationRun.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from datetime import datetime
import json

class PerturbationConfig(BaseModel):
    """Configuration for the sparse perturbation matrix."""
    theta: float = Field(..., description="Norm of the perturbation")
    rank: int = Field(..., ge=0, description="Rank of the perturbation")
    support_density: float = Field(..., ge=0.0, le=1.0, description="Fraction of non-zero entries in the support")
    type: Literal["diagonal", "block-sparse", "random sparse"] = Field(..., description="Type of sparsity pattern")

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        allowed = {"diagonal", "block-sparse", "random sparse"}
        if v not in allowed:
            raise ValueError(f"type must be one of {allowed}, got '{v}'")
        return v

    @field_validator('support_density')
    @classmethod
    def validate_density(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("support_density must be between 0.0 and 1.0")
        return v

    def to_dict(self) -> dict:
        """Convert config to a dictionary for JSON serialization."""
        return self.model_dump(mode='json')

class SimulationRun(BaseModel):
    """Record of a single simulation run including metadata and results."""
    run_id: str = Field(..., description="Unique identifier for the run")
    N: int = Field(..., gt=0, description="Matrix dimension")
    seed: int = Field(..., description="Random seed used for reproducibility")
    theta: float = Field(..., description="Perturbation norm")
    eigenvalues: List[float] = Field(..., description="Computed eigenvalues (sorted descending)")
    outlier_flag: bool = Field(..., description="Whether an outlier was detected")
    perturbation_config: Optional[PerturbationConfig] = Field(None, description="Optional perturbation configuration used")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z", description="ISO 8601 timestamp of run completion")

    def to_dict(self) -> dict:
        """Convert simulation run to a dictionary for JSON serialization."""
        return self.model_dump(mode='json')

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Serialize the simulation run to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> 'SimulationRun':
        """Create a SimulationRun instance from a dictionary."""
        if 'perturbation_config' in data and isinstance(data['perturbation_config'], dict):
            data['perturbation_config'] = PerturbationConfig.model_validate(data['perturbation_config'])
        return cls.model_validate(data)

# Re-export for convenience
__all__ = ["PerturbationConfig", "SimulationRun"]
