"""
Data models for the project.

Implements T007: IonPair and CalculationResult data classes.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import numpy as np

@dataclass
class IonPair:
    """
    Represents an ionic liquid ion pair.
    
    Attributes:
        id: Unique identifier for the pair.
        cation: Name or formula of the cation.
        anion: Name or formula of the anion.
        coordinates: XYZ coordinates (string or list of dicts).
        reference_energy: CCSD(T)/CBS reference interaction energy (Hartree).
        cation_coords: Coordinates for the cation fragment (for CP).
        anion_coords: Coordinates for the anion fragment (for CP).
    """
    id: str
    cation: str
    anion: str
    coordinates: str  # Assuming XYZ string for simplicity
    reference_energy: float
    cation_coords: Optional[str] = None
    anion_coords: Optional[str] = None

    def __post_init__(self):
        if self.cation_coords is None:
            # Placeholder: if not provided, we might need to parse from coordinates
            # For now, we leave it as None and handle in run_psi4
            pass

@dataclass
class CalculationResult:
    """
    Stores the result of a single-point calculation.
    
    Attributes:
        pair_id: ID of the ion pair.
        method: DFT method used.
        basis: Basis set used.
        total_energy: Total DFT-D3 energy (Hartree).
        dispersion_energy: D3 dispersion contribution (Hartree).
        reference_energy: Reference energy (Hartree).
        error: Signed error (Total - Reference).
        status: 'success' or 'failed'.
    """
    pair_id: str
    method: str
    basis: str
    total_energy: float
    dispersion_energy: float
    reference_energy: float
    error: float
    status: str = "success"

    def __post_init__(self):
        self.error = self.total_energy - self.reference_energy
