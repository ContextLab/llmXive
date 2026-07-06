from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import numpy as np

@dataclass
class IonPair:
    pair_id: int
    cation: str
    anion: str
    xyz_path: str
    reference_energy: float

@dataclass
class CalculationResult:
    pair_id: int
    dft_total_energy: float
    d3_dispersion_energy: float
    reference_energy: float
    error: float
    scaled_error: Optional[float] = None
