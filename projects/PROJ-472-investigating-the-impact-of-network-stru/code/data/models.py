"""
Data models for the project.
Defines Participant, StructuralConnectome, and AvalancheRecord.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import numpy as np
from pathlib import Path

@dataclass
class Participant:
    """Represents a study participant."""
    subject_id: str
    age: Optional[int] = None
    sex: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StructuralConnectome:
    """Represents a structural connectome (adjacency matrix)."""
    subject_id: str
    matrix: np.ndarray
    labels: List[str]
    region_count: int = 0

    def __post_init__(self):
        if self.region_count == 0:
            self.region_count = self.matrix.shape[0]

@dataclass
class AvalancheRecord:
    """Represents a single neural avalanche event."""
    subject_id: str
    start_time: float
    end_time: float
    size: int
    duration: float
    region_ids: List[int] = field(default_factory=list)
