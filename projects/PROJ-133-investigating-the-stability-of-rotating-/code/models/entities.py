"""Data‑model entities used throughout the project.

The module defines simple dataclasses that represent a simulation run and
a stability metric.  Both classes are documented with NumPy‑style
docstrings.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np

@dataclass
class SimulationRun:
    """Metadata describing a single GPE simulation run.

    Attributes
    ----------
    run_id : str
        Unique identifier for the run.
    parameters : dict
        Dictionary of simulation parameters (e.g., ``omega``, ``epsilon_dd``).
    status : str
        ``"completed"``, ``"unstable"``, or ``"failed"``.
    start_time : datetime
        Timestamp when the run started.
    end_time : datetime
        Timestamp when the run finished.
    seed : int
        Random seed used for noise generation.
    """
    run_id: str
    parameters: Dict[str, any]
    status: str
    start_time: datetime
    end_time: datetime
    seed: int

@dataclass
class StabilityMetric:
    """Container for a set of stability metrics associated with a run.

    Attributes
    ----------
    run_id : str
        Identifier of the simulation run.
    vortex_density : float
        Vortices per unit area.
    radial_variance : float
        Variance of the radial density profile.
    structure_factor_sharpness : float
        Sharpness of the first Bragg peak in the structure factor.
    """
    run_id: str
    vortex_density: float
    radial_variance: float
    structure_factor_sharpness: float
