"""Data models for the research pipeline."""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import hashlib
import json

@dataclass
class MaterialEntry:
    """Represents a single material entry from the database."""
    id: str
    composition: str
    formation_energy: Optional[float]
    descriptors: Dict[str, float] = field(default_factory=dict)
    dft_computed: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "material_id": self.id,
            "composition": self.composition,
            "formation_energy": self.formation_energy,
            "dft_computed": self.dft_computed,
            "descriptors": self.descriptors
        }

@dataclass
class SparsitySubset:
    """Represents a stratified subset of the material pool."""
    level: str
    seed: int
    percentage: float
    checksum: str
    material_ids: List[str] = field(default_factory=list)
    
    def calculate_checksum(self) -> str:
        """Calculate SHA-256 checksum of the sorted material IDs."""
        sorted_ids = sorted(self.material_ids)
        data_str = ",".join(sorted_ids)
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "seed": self.seed,
            "percentage": self.percentage,
            "checksum": self.checksum,
            "material_ids": self.material_ids
        }
