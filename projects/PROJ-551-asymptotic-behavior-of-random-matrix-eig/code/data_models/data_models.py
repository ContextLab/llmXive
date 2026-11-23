"""
Data models for the project.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
import json

class PerturbationConfig(BaseModel):
    """Configuration for a sparse perturbation."""
    rank: int
    support_density: float
    type: str  # 'diagonal', 'block-sparse', 'random-sparse'
    theta: Optional[float] = None

class SimulationRun(BaseModel):
    """Metadata record for a simulation run."""
    run_id: str
    N: int
    seed: int
    theta: Optional[float] = None
    eigenvalues: Optional[List[float]] = None
    outlier_flag: Optional[bool] = None
    rank: Optional[int] = None
    support_density: Optional[float] = None
    type: Optional[str] = None
    timestamp: Optional[datetime] = None
    checksum: Optional[str] = None
    file_path: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump()
