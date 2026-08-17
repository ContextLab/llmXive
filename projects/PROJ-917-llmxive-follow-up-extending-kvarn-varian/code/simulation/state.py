from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import numpy as np

@dataclass
class SimulationState:
    """
    Represents the state of a sequential simulation step.
    
    Attributes:
        accumulated_kl: Total accumulated KL-divergence up to the current step.
        current_error_state: Dictionary containing the error state of the current step.
        step_index: The current step index in the simulation.
        full_trajectory: List of per-step KL-divergence values recorded so far.
    """
    accumulated_kl: float = 0.0
    current_error_state: Dict[str, Any] = field(default_factory=dict)
    step_index: int = 0
    full_trajectory: List[float] = field(default_factory=list)
