from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class PolymerRecord:
    """
    Data model for a single polymer record from literature.
    Implements T007.
    """
    polymer_name: str
    smiles: str
    permeability: Optional[float] = None
    selectivity: Optional[float] = None
    unit_permeability: str = "Barrer"
    unit_selectivity: str = "Dimensionless"
    synthesis_method: Optional[str] = None
    source: str = "unknown"
    reference: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "polymer_name": self.polymer_name,
            "smiles": self.smiles,
            "permeability": self.permeability,
            "selectivity": self.selectivity,
            "unit_permeability": self.unit_permeability,
            "unit_selectivity": self.unit_selectivity,
            "synthesis_method": self.synthesis_method,
            "source": self.source,
            "reference": self.reference,
            "notes": self.notes,
            "created_at": self.created_at.isoformat()
        }
