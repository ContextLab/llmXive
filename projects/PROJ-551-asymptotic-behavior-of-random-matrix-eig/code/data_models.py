"""
Data models using Pydantic for the asymptotic behavior of random matrix eigenvalues project.

Defines core entities: PerturbationConfig and SimulationRun.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
import json

class PerturbationConfig(BaseModel):
    """Configuration for the sparse perturbation matrix."""
    theta: float = Field(..., description="Norm of the perturbation")
    rank: int = Field(..., ge=0, description="Rank of the perturbation")
    sparsity_pattern: str = Field(..., description="Type of sparsity: 'diagonal', 'block_sparse', 'random_sparse'")
    sparsity_density: Optional[float] = Field(None, ge=0.0, le=1.0, description="Density for random/block sparse patterns")

    @field_validator('sparsity_pattern')
    @classmethod
    def validate_pattern(cls, v):
        allowed = {'diagonal', 'block_sparse', 'random_sparse'}
        if v not in allowed:
            raise ValueError(f"sparsity_pattern must be one of {allowed}, got '{v}'")
        return v

    @field_validator('sparsity_density')
    @classmethod
    def validate_density(cls, v, info):
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("sparsity_density must be between 0.0 and 1.0")
        # If density is provided but pattern is diagonal, it's technically ignored but allowed for config flexibility
        return v

    def to_dict(self) -> dict:
        """Convert config to a dictionary for JSON serialization."""
        return self.model_dump(mode='json')

class SimulationRun(BaseModel):
    """Record of a single simulation run including metadata and results."""
    seed: int = Field(..., description="Random seed used for reproducibility")
    N: int = Field(..., gt=0, description="Matrix dimension")
    perturbation: PerturbationConfig = Field(..., description="Perturbation configuration")
    eigenvalues: List[float] = Field(..., description="Computed eigenvalues (sorted descending)")
    w_checksum: str = Field(..., description="SHA-256 checksum of the Wigner matrix")
    p_checksum: str = Field(..., description="SHA-256 checksum of the perturbation matrix")
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
        if 'perturbation' in data and isinstance(data['perturbation'], dict):
            data['perturbation'] = PerturbationConfig.model_validate(data['perturbation'])
        return cls.model_validate(data)