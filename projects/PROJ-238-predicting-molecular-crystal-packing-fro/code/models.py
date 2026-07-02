from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import json

@dataclass
class Molecule:
    id: str
    mw: float
    descriptors: Dict[str, float] = field(default_factory=dict)

@dataclass
class CrystalStructure:
    id: str
    unit_cell: Dict[str, float] = field(default_factory=dict)
    interaction_type: Optional[str] = None

@dataclass
class ModelResult:
    model_type: str
    metrics: Dict[str, float] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)

def to_json(obj: Any) -> str:
    """Convert a dataclass object to JSON string."""
    return json.dumps(obj.__dict__)