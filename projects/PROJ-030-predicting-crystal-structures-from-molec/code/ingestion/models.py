"""
Data models for the ingestion pipeline.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

@dataclass
class MoleculeRecord:
    """Represents a single molecule record with its properties."""
    id: str
    smiles: str
    space_group: str
    lattice_a: float
    lattice_b: float
    lattice_c: float
    alpha: float
    beta: float
    gamma: float
    volume: float
    fingerprint: Optional[List[int]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ModelMetrics:
    """Container for model evaluation metrics."""
    model_name: str
    accuracy: Optional[float] = None
    macro_f1: Optional[float] = None
    r_squared: Optional[float] = None
    mae: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class FeatureImportance:
    """Container for feature importance data."""
    feature_id: int
    importance_score: float
    substructure: Optional[str] = None
    collision_flag: bool = False
