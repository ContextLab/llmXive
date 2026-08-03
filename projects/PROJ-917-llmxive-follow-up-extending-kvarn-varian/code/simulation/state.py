from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import numpy as np

@dataclass
class SimulationState:
    """
    State representation for autoregressive simulation.
    
    This dataclass maintains the cumulative error state across simulation steps,
    including accumulated KL-divergence and the full trajectory of per-step errors.
    
    Fields:
        accumulated_kl: Total accumulated KL-divergence across all steps.
        current_error_state: Dictionary containing error metrics for the current step.
        step_index: Current step index in the simulation.
        full_trajectory: List of per-step KL-divergence values.
    """
    accumulated_kl: float = 0.0
    current_error_state: Dict[str, Any] = field(default_factory=dict)
    step_index: int = 0
    full_trajectory: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "accumulated_kl": self.accumulated_kl,
            "current_error_state": self.current_error_state,
            "step_index": self.step_index,
            "full_trajectory": self.full_trajectory
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationState':
        """Create state from dictionary."""
        return cls(
            accumulated_kl=data.get("accumulated_kl", 0.0),
            current_error_state=data.get("current_error_state", {}),
            step_index=data.get("step_index", 0),
            full_trajectory=data.get("full_trajectory", [])
        )
