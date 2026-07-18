"""
Data models for the ingestion pipeline.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class PolymerRecord:
    """
    Represents a single polymer record from literature.
    """
    polymer_name: str
    smiles: Optional[str]
    permeability: Optional[float]
    permeability_unit: Optional[str]
    selectivity: Optional[float]
    selectivity_gas_pair: Optional[str]
    synthesis_method: Optional[str]
    source: str
    reference: Optional[str]
    class_name: Optional[str] = None
    is_high_variance: bool = False
    imputed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
