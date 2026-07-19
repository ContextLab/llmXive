"""
Data models for the project.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import hashlib
import json

@dataclass
class MaterialEntry:
    """
    Represents a single material entry from the Materials Project.
    """
    id: str
    composition: str
    formation_energy: float
    descriptors: Dict[str, float]
    dft_computed: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SparsitySubset:
    """
    Represents a subset of the dataset created for sparsity analysis.
    """
    level: str
    seed: int
    percentage: float
    checksum: Optional[str] = None
    criteria: str = ""
    filename: Optional[str] = None
    row_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "level": self.level,
            "seed": self.seed,
            "percentage": self.percentage,
            "checksum": self.checksum,
            "criteria": self.criteria,
            "filename": self.filename,
            "row_count": self.row_count,
            "metadata": self.metadata
        }
