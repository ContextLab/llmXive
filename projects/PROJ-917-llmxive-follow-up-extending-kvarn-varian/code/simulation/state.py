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

    def update(self, step_kl: float, error_details: Optional[Dict[str, Any]] = None) -> 'SimulationState':
        """
        Updates the simulation state with the results of a new step.
        
        Args:
            step_kl: The KL-divergence calculated for the current step.
            error_details: Optional dictionary of specific error metrics for this step.
        
        Returns:
            A new SimulationState instance with updated values.
        """
        new_accumulated = self.accumulated_kl + step_kl
        new_trajectory = self.full_trajectory + [step_kl]
        new_error_state = error_details if error_details is not None else {}
        
        return SimulationState(
            accumulated_kl=new_accumulated,
            current_error_state=new_error_state,
            step_index=self.step_index + 1,
            full_trajectory=new_trajectory
        )
