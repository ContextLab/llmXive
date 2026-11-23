"""
Data models for the ingestion pipeline.

Defines core data structures for molecules, model metrics, and feature importance
used throughout the crystal structure prediction pipeline.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

@dataclass
class MoleculeRecord:
    """
    Represents a single molecule record with its crystallographic and chemical properties.
    
    Attributes:
        id: Unique identifier for the record (e.g., COD ID or generated hash)
        smiles: Canonical SMILES string of the molecule
        space_group: Space group symbol (e.g., 'P21/c')
        lattice_a: Lattice parameter a (Angstrom)
        lattice_b: Lattice parameter b (Angstrom)
        lattice_c: Lattice parameter c (Angstrom)
        alpha: Lattice angle alpha (degrees)
        beta: Lattice angle beta (degrees)
        gamma: Lattice angle gamma (degrees)
        volume: Unit cell volume (Angstrom^3)
        fingerprint: Optional ECFP4 fingerprint as a list of integers (bits)
        metadata: Additional metadata dictionary (e.g., source, parsing status)
    """
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert the record to a dictionary for serialization."""
        return {
            "id": self.id,
            "smiles": self.smiles,
            "space_group": self.space_group,
            "lattice_a": self.lattice_a,
            "lattice_b": self.lattice_b,
            "lattice_c": self.lattice_c,
            "alpha": self.alpha,
            "beta": self.beta,
            "gamma": self.gamma,
            "volume": self.volume,
            "fingerprint": self.fingerprint,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MoleculeRecord":
        """Create a MoleculeRecord from a dictionary."""
        return cls(
            id=data["id"],
            smiles=data["smiles"],
            space_group=data["space_group"],
            lattice_a=float(data["lattice_a"]),
            lattice_b=float(data["lattice_b"]),
            lattice_c=float(data["lattice_c"]),
            alpha=float(data["alpha"]),
            beta=float(data["beta"]),
            gamma=float(data["gamma"]),
            volume=float(data["volume"]),
            fingerprint=data.get("fingerprint"),
            metadata=data.get("metadata", {})
        )

@dataclass
class ModelMetrics:
    """
    Container for model evaluation metrics.
    
    Attributes:
        model_name: Name/identifier of the model
        accuracy: Classification accuracy (0.0 to 1.0)
        macro_f1: Macro-averaged F1 score
        r_squared: R-squared (coefficient of determination) for regression
        mae: Mean Absolute Error for regression
        timestamp: ISO format timestamp when metrics were calculated
    """
    model_name: str
    accuracy: Optional[float] = None
    macro_f1: Optional[float] = None
    r_squared: Optional[float] = None
    mae: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to a dictionary for serialization."""
        return {
            "model_name": self.model_name,
            "accuracy": self.accuracy,
            "macro_f1": self.macro_f1,
            "r_squared": self.r_squared,
            "mae": self.mae,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelMetrics":
        """Create ModelMetrics from a dictionary."""
        return cls(
            model_name=data["model_name"],
            accuracy=data.get("accuracy"),
            macro_f1=data.get("macro_f1"),
            r_squared=data.get("r_squared"),
            mae=data.get("mae"),
            timestamp=data.get("timestamp", datetime.now().isoformat())
        )

@dataclass
class FeatureImportance:
    """
    Container for feature importance data from model analysis.
    
    Attributes:
        feature_id: Identifier of the fingerprint bit or feature
        importance_score: Numerical score indicating feature importance
        substructure: Optional chemical substructure string (SMILES/InChI) mapped to this bit
        collision_flag: True if this bit maps to multiple substructures (ambiguity)
    """
    feature_id: int
    importance_score: float
    substructure: Optional[str] = None
    collision_flag: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "feature_id": self.feature_id,
            "importance_score": self.importance_score,
            "substructure": self.substructure,
            "collision_flag": self.collision_flag
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureImportance":
        """Create FeatureImportance from a dictionary."""
        return cls(
            feature_id=int(data["feature_id"]),
            importance_score=float(data["importance_score"]),
            substructure=data.get("substructure"),
            collision_flag=bool(data.get("collision_flag", False))
        )