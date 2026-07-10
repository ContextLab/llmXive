"""
Data Models for the Battery Electrolyte Project.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class MoleculeType(Enum):
    SOLVENT = "solvent"
    SALT = "salt"
    ADDITIVE = "additive"


@dataclass
class ElectrolyteMolecule:
    molecule_id: str
    smiles: str
    type: MoleculeType
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DecompositionEvent:
    molecule_id: str
    potential_v: float
    reactants: List[str]
    products: List[str]
    energy_reactants: float
    energy_products: float
    n_electrons: int
    e_decomp_ev: Optional[float] = None


@dataclass
class FeatureVector:
    molecule_id: str
    features: Dict[str, float]
    target: Optional[float] = None
    bin_label: Optional[str] = None
