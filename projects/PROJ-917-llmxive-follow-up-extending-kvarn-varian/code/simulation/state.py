"""
Simulation state management for the autoregressive generation loop.

This module defines the `SimulationState` dataclass used to track the
accumulated error state across simulation steps, specifically for
the Sequential Sinkhorn optimizer and KL-divergence accumulation.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import numpy as np


@dataclass
class SimulationState:
    """
    Represents the state of a simulation run at a specific step.

    Attributes:
        accumulated_kl (float): The cumulative KL-divergence accumulated
            from step 0 up to the current step.
        current_error_state (dict): A dictionary containing the current
            error metrics, such as quantization error, drift parameters,
            or specific optimizer states required for the next step.
            Keys are strings, values can be floats, arrays, or nested dicts.
        step_index (int): The index of the current step in the simulation.
    """
    accumulated_kl: float = 0.0
    current_error_state: Dict[str, Any] = field(default_factory=dict)
    step_index: int = 0

    def update(self, step_delta_kl: float, new_error_metrics: Optional[Dict[str, Any]] = None) -> 'SimulationState':
        """
        Updates the simulation state for the next step.

        Args:
            step_delta_kl: The KL-divergence computed for the current transition.
            new_error_metrics: A dictionary of new error metrics to merge into
                `current_error_state`. If None, the existing state is preserved
                (except for the index and accumulated KL).

        Returns:
            A new SimulationState instance with updated values.
        """
        new_accumulated_kl = self.accumulated_kl + step_delta_kl
        new_step_index = self.step_index + 1

        # Merge error states
        new_error_state = dict(self.current_error_state)
        if new_error_metrics:
            new_error_state.update(new_error_metrics)

        return SimulationState(
            accumulated_kl=new_accumulated_kl,
            current_error_state=new_error_state,
            step_index=new_step_index
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the state to a dictionary for logging or storage.

        Returns:
            A dictionary representation of the state.
        """
        return {
            "accumulated_kl": self.accumulated_kl,
            "current_error_state": self.current_error_state,
            "step_index": self.step_index
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationState':
        """
        Deserializes a state from a dictionary.

        Args:
            data: A dictionary containing state keys.

        Returns:
            A new SimulationState instance.
        """
        return cls(
            accumulated_kl=data.get("accumulated_kl", 0.0),
            current_error_state=data.get("current_error_state", {}),
            step_index=data.get("step_index", 0)
        )
