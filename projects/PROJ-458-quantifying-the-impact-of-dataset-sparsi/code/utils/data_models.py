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
    
    Attributes:
        id: Unique material identifier (e.g., 'mp-1234')
        composition: Chemical composition string (e.g., 'Fe2O3')
        formation_energy: Formation energy per atom in eV
        descriptors: Dictionary of calculated feature vectors
        dft_computed: Flag indicating if data is DFT computed
        metadata: Additional optional metadata
    """
    id: str
    composition: str
    formation_energy: float
    descriptors: Dict[str, float]
    dft_computed: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "composition": self.composition,
            "formation_energy": self.formation_energy,
            "descriptors": self.descriptors,
            "dft_computed": self.dft_computed,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MaterialEntry':
        """Create instance from dictionary."""
        return cls(
            id=data["id"],
            composition=data["composition"],
            formation_energy=data["formation_energy"],
            descriptors=data["descriptors"],
            dft_computed=data.get("dft_computed", True),
            metadata=data.get("metadata", {})
        )

@dataclass
class SparsitySubset:
    """
    Represents a subset of the dataset created for sparsity analysis.
    
    Attributes:
        level: Identifier for the sparsity level (e.g., '100', '50', '1')
        seed: Random seed used for reproducibility
        percentage: Percentage of full dataset retained (0.0 to 100.0)
        checksum: SHA-256 checksum of the subset data for integrity verification
        criteria: Description of the sampling criteria used
        filename: Path to the saved subset file
        row_count: Number of rows in this subset
        metadata: Additional metadata about the subset generation
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

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SparsitySubset':
        """Create instance from dictionary."""
        return cls(
            level=data["level"],
            seed=data["seed"],
            percentage=data["percentage"],
            checksum=data.get("checksum"),
            criteria=data.get("criteria", ""),
            filename=data.get("filename"),
            row_count=data.get("row_count", 0),
            metadata=data.get("metadata", {})
        )

    def update_checksum(self, data_bytes: bytes) -> None:
        """Update the checksum based on raw data bytes."""
        self.checksum = hashlib.sha256(data_bytes).hexdigest()