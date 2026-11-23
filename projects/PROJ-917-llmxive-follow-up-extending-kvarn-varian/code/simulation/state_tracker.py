"""
Simulation State Tracking Framework.

Provides classes and functions to track cumulative error states and
KL-divergence accumulators during autoregressive simulation runs.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
import json
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
EPSILON = 1e-10
DEFAULT_DTYPE = np.float64


@dataclass
class SimulationState:
    """
    Represents the state of a simulation at a specific step.
    Includes cumulative error metrics and distribution parameters.
    """
    step: int
    # Distribution parameters for current step
    current_mean: float = 0.0
    current_var: float = 0.0
    current_skew: float = 0.0
    current_kurt: float = 0.0
    # Cumulative metrics
    cumulative_kl_divergence: float = 0.0
    cumulative_error: float = 0.0
    # Per-step trace for analysis
    kl_trace: List[float] = field(default_factory=list)
    error_trace: List[float] = field(default_factory=list)
    # Metadata
    is_valid: bool = True
    failure_reason: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert state to dictionary for serialization."""
        return {
            "step": self.step,
            "current_mean": self.current_mean,
            "current_var": self.current_var,
            "current_skew": self.current_skew,
            "current_kurt": self.current_kurt,
            "cumulative_kl_divergence": self.cumulative_kl_divergence,
            "cumulative_error": self.cumulative_error,
            "kl_trace": self.kl_trace,
            "error_trace": self.error_trace,
            "is_valid": self.is_valid,
            "failure_reason": self.failure_reason
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'SimulationState':
        """Create SimulationState from dictionary."""
        return cls(
            step=data["step"],
            current_mean=data["current_mean"],
            current_var=data["current_var"],
            current_skew=data["current_skew"],
            current_kurt=data["current_kurt"],
            cumulative_kl_divergence=data["cumulative_kl_divergence"],
            cumulative_error=data["cumulative_error"],
            kl_trace=data["kl_trace"],
            error_trace=data["error_trace"],
            is_valid=data["is_valid"],
            failure_reason=data.get("failure_reason")
        )


class StateTracker:
    """
    Tracks simulation state across multiple steps.
    Manages cumulative error accumulation and KL-divergence tracking.
    """

    def __init__(self, run_id: str, initial_state: Optional[SimulationState] = None):
        """
        Initialize the StateTracker.

        Args:
            run_id: Unique identifier for this simulation run.
            initial_state: Optional starting state. If None, starts at step 0 with zeros.
        """
        self.run_id = run_id
        if initial_state:
            self.current_state = initial_state
        else:
            self.current_state = SimulationState(step=0)
        self.history: List[SimulationState] = [self.current_state]
        self.logger = logging.getLogger(f"StateTracker.{run_id}")

    def update(
        self,
        step: int,
        current_mean: float,
        current_var: float,
        current_skew: float,
        current_kurt: float,
        quantized_mean: Optional[float] = None,
        quantized_var: Optional[float] = None,
        quantized_skew: Optional[float] = None,
        quantized_kurt: Optional[float] = None
    ) -> SimulationState:
        """
        Update the tracker with new step data and compute accumulated metrics.

        Args:
            step: Current simulation step.
            current_mean, current_var, current_skew, current_kurt: 
                Parameters of the full-precision distribution.
            quantized_mean, quantized_var, quantized_skew, quantized_kurt:
                Parameters of the quantized distribution (optional).
                If None, error metrics will not be updated.

        Returns:
            Updated SimulationState.
        """
        try:
            # Compute step-wise KL divergence if quantized params provided
            step_kl = 0.0
            if quantized_mean is not None and quantized_var is not None:
                # Use Gaussian KL divergence approximation
                # KL(P || Q) for Gaussians: 0.5 * (log(var_q/var_p) + var_p/var_q + (mean_p - mean_q)^2/var_q - 1)
                step_kl = compute_kl_divergence_simple(
                    current_mean, current_var,
                    quantized_mean, quantized_var
                )

            # Compute step-wise error (L2 distance on mean as proxy)
            step_error = 0.0
            if quantized_mean is not None:
                step_error = (current_mean - quantized_mean) ** 2

            # Update cumulative metrics
            new_cumulative_kl = self.current_state.cumulative_kl_divergence + step_kl
            new_cumulative_error = self.current_state.cumulative_error + step_error

            # Create new state
            new_state = SimulationState(
                step=step,
                current_mean=current_mean,
                current_var=current_var,
                current_skew=current_skew,
                current_kurt=current_kurt,
                cumulative_kl_divergence=new_cumulative_kl,
                cumulative_error=new_cumulative_error,
                kl_trace=self.current_state.kl_trace + [step_kl],
                error_trace=self.current_state.error_trace + [step_error],
                is_valid=True
            )

            self.current_state = new_state
            self.history.append(new_state)
            self.logger.debug(f"Step {step}: KL={step_kl:.6f}, Cumulative KL={new_cumulative_kl:.6f}")

            return new_state

        except Exception as e:
            self.logger.error(f"Error updating state at step {step}: {e}")
            failed_state = SimulationState(
                step=step,
                current_mean=current_mean,
                current_var=current_var,
                current_skew=current_skew,
                current_kurt=current_kurt,
                cumulative_kl_divergence=self.current_state.cumulative_kl_divergence,
                cumulative_error=self.current_state.cumulative_error,
                kl_trace=self.current_state.kl_trace,
                error_trace=self.current_state.error_trace,
                is_valid=False,
                failure_reason=str(e)
            )
            self.current_state = failed_state
            self.history.append(failed_state)
            return failed_state

    def get_final_state(self) -> SimulationState:
        """Return the most recent state."""
        return self.current_state

    def get_history(self) -> List[SimulationState]:
        """Return the full history of states."""
        return self.history

    def save_to_file(self, filepath: Union[str, Path]) -> None:
        """
        Save the entire history to a JSON file.

        Args:
            filepath: Path to save the JSON file.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "run_id": self.run_id,
            "total_steps": len(self.history) - 1,
            "final_cumulative_kl": self.current_state.cumulative_kl_divergence,
            "final_cumulative_error": self.current_state.cumulative_error,
            "history": [state.to_dict() for state in self.history]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"State history saved to {filepath}")

    @classmethod
    def load_from_file(cls, filepath: Union[str, Path]) -> 'StateTracker':
        """
        Load a StateTracker from a JSON file.

        Args:
            filepath: Path to the JSON file.

        Returns:
            Loaded StateTracker instance.
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"State file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        tracker = cls(run_id=data["run_id"])
        tracker.history = []
        
        for state_dict in data["history"]:
            state = SimulationState.from_dict(state_dict)
            tracker.history.append(state)
        
        if tracker.history:
            tracker.current_state = tracker.history[-1]
        
        return tracker

# --- KL Divergence Utilities ---

def compute_kl_divergence_simple(
    mean_p: float, 
    var_p: float, 
    mean_q: float, 
    var_q: float
) -> float:
    """
    Compute KL divergence between two Gaussian distributions P and Q.
    
    Formula: 0.5 * (log(var_q/var_p) + var_p/var_q + (mean_p - mean_q)^2/var_q - 1)
    
    Args:
        mean_p, var_p: Mean and variance of distribution P (full precision).
        mean_q, var_q: Mean and variance of distribution Q (quantized).
    
    Returns:
        KL(P || Q) divergence value.
    """
    # Ensure numerical stability
    var_p = max(var_p, EPSILON)
    var_q = max(var_q, EPSILON)
    
    log_ratio = np.log(var_q / var_p)
    var_ratio = var_p / var_q
    mean_diff_sq = (mean_p - mean_q) ** 2
    mean_term = mean_diff_sq / var_q
    
    kl = 0.5 * (log_ratio + var_ratio + mean_term - 1.0)
    return float(np.maximum(0.0, kl))  # KL divergence cannot be negative

def compute_kl_divergence_batch(
    means_p: np.ndarray, 
    vars_p: np.ndarray, 
    means_q: np.ndarray, 
    vars_q: np.ndarray
) -> np.ndarray:
    """
    Compute KL divergence for batches of Gaussian distributions.
    
    Args:
        means_p, vars_p: Arrays of means and variances for P.
        means_q, vars_q: Arrays of means and variances for Q.
    
    Returns:
        Array of KL divergence values.
    """
    # Clip to avoid division by zero
    vars_p = np.clip(vars_p, EPSILON, None)
    vars_q = np.clip(vars_q, EPSILON, None)
    
    log_ratio = np.log(vars_q / vars_p)
    var_ratio = vars_p / vars_q
    mean_diff_sq = (means_p - means_q) ** 2
    mean_term = mean_diff_sq / vars_q
    
    kl = 0.5 * (log_ratio + var_ratio + mean_term - 1.0)
    return np.maximum(0.0, kl)

# --- Global State Management ---

_global_trackers: Dict[str, StateTracker] = {}

def reset_tracker(run_id: str) -> None:
    """Reset the global tracker for a specific run ID."""
    if run_id in _global_trackers:
        del _global_trackers[run_id]
        logger.info(f"Reset tracker for run: {run_id}")

def get_tracker(run_id: str) -> StateTracker:
    """Get or create a global tracker for a run ID."""
    if run_id not in _global_trackers:
        _global_trackers[run_id] = StateTracker(run_id=run_id)
    return _global_trackers[run_id]

# --- Analysis Utilities ---

def compute_cumulative_kl_trace(history: List[SimulationState]) -> List[float]:
    """
    Extract cumulative KL divergence trace from history.
    
    Args:
        history: List of SimulationState objects.
    
    Returns:
        List of cumulative KL divergence values.
    """
    return [state.cumulative_kl_divergence for state in history]

def compute_cumulative_error_trace(history: List[SimulationState]) -> List[float]:
    """
    Extract cumulative error trace from history.
    
    Args:
        history: List of SimulationState objects.
    
    Returns:
        List of cumulative error values.
    """
    return [state.cumulative_error for state in history]

def compute_average_kl_per_step(history: List[SimulationState]) -> float:
    """
    Compute average KL divergence per step.
    
    Args:
        history: List of SimulationState objects.
    
    Returns:
        Average KL divergence per step.
    """
    if len(history) <= 1:
        return 0.0
    final_kl = history[-1].cumulative_kl_divergence
    steps = len(history) - 1
    return final_kl / steps

def compute_average_error_per_step(history: List[SimulationState]) -> float:
    """
    Compute average error per step.
    
    Args:
        history: List of SimulationState objects.
    
    Returns:
        Average error per step.
    """
    if len(history) <= 1:
        return 0.0
    final_error = history[-1].cumulative_error
    steps = len(history) - 1
    return final_error / steps

def validate_state_consistency(state: SimulationState) -> bool:
    """
    Validate that a state is internally consistent.
    
    Args:
        state: SimulationState to validate.
    
    Returns:
        True if valid, False otherwise.
    """
    if not state.is_valid:
        return False
    
    # Check non-negative variance
    if state.current_var < 0:
        return False
    
    # Check cumulative metrics are non-decreasing (for KL and error)
    if len(state.kl_trace) > 1:
        for i in range(1, len(state.kl_trace)):
            if state.kl_trace[i] < state.kl_trace[i-1] - EPSILON:
                return False
    
    return True

def main():
    """
    Example usage of the StateTracker framework.
    """
    # Create a tracker
    tracker = StateTracker(run_id="demo_run_001")
    
    # Simulate a few steps
    for step in range(1, 6):
        # Simulate some data
        mean_p = float(step)
        var_p = 1.0 + 0.1 * step
        mean_q = mean_p + 0.1 * (step % 2 - 0.5)  # Small quantization error
        var_q = var_p * 0.95  # Slight variance shift
        
        tracker.update(
            step=step,
            current_mean=mean_p,
            current_var=var_p,
            current_skew=0.0,
            current_kurt=3.0,
            quantized_mean=mean_q,
            quantized_var=var_q
        )
    
    # Print results
    final_state = tracker.get_final_state()
    print(f"Final Step: {final_state.step}")
    print(f"Cumulative KL Divergence: {final_state.cumulative_kl_divergence:.6f}")
    print(f"Cumulative Error: {final_state.cumulative_error:.6f}")
    
    # Save to file
    tracker.save_to_file("data/simulation/demo_state.json")
    print("State saved to data/simulation/demo_state.json")

if __name__ == "__main__":
    main()