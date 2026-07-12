"""
Base Agent module for llmXive automated science pipeline.

Implements the abstract base class for all agent variants (Baseline, Linear Proxy, Hybrid).
Enforces the 50-step hard limit per FR-006 and provides the interface for inference.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import json
import time
import os

from config import CONFIG

@dataclass
class StepResult:
    """Result of a single step in the agent's trajectory."""
    action: str
    observation: str
    success: bool
    step_number: int
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class StepLimitExceeded(Exception):
    """Raised when the agent exceeds the maximum allowed steps (FR-006)."""
    pass

class TimeLimitExceeded(Exception):
    """Raised when the agent exceeds the maximum allowed wall-clock time."""
    pass

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    
    Enforces:
    - 50-step hard limit (FR-006)
    - 6-hour wall-clock time limit (SC-004)
    - Deterministic inference interface
    """
    
    MAX_STEPS: int = 50
    MAX_TIME_SECONDS: int = 6 * 60 * 60  # 6 hours

    def __init__(self, model_path: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent.
        
        Args:
            model_path: Path to the GGUF model file.
            config: Optional configuration dictionary for inference parameters.
        """
        self.model_path = model_path
        self.config = config or {}
        self.step_count = 0
        self.start_time: Optional[float] = None
        self.trajectory_log: List[Dict[str, Any]] = []
        
        # Load model (implementation deferred to subclasses)
        self.model = self._load_model()

    @abstractmethod
    def _load_model(self) -> Any:
        """
        Load the model from disk.
        
        Must be implemented by subclasses (e.g., using llama-cpp-python).
        Returns the loaded model object.
        """
        pass

    @abstractmethod
    def _infer(self, state: Dict[str, Any], history: List[Dict[str, Any]]) -> str:
        """
        Perform inference to determine the next action.
        
        Args:
            state: Current GUI state (DOM, screenshot, etc.).
            history: List of previous steps (actions, observations).
        
        Returns:
            The action string to perform next.
        """
        pass

    def _enforce_step_limit(self) -> None:
        """Check if the step limit has been exceeded and raise if so."""
        if self.step_count > self.MAX_STEPS:
            raise StepLimitExceeded(
                f"Agent exceeded maximum step limit of {self.MAX_STEPS} steps."
            )

    def _enforce_time_limit(self) -> None:
        """Check if the time limit has been exceeded and raise if so."""
        if self.start_time is None:
            return
        
        elapsed = time.time() - self.start_time
        if elapsed > self.MAX_TIME_SECONDS:
            raise TimeLimitExceeded(
                f"Agent exceeded maximum time limit of {self.MAX_TIME_SECONDS} seconds "
                f"({elapsed:.2f}s elapsed)."
            )

    def step(self, state: Dict[str, Any], history: List[Dict[str, Any]]) -> StepResult:
        """
        Execute a single step of the agent.
        
        Args:
            state: Current GUI state.
            history: List of previous steps.
        
        Returns:
            StepResult containing the action, observation, and metadata.
        
        Raises:
            StepLimitExceeded: If the agent exceeds the step limit.
            TimeLimitExceeded: If the agent exceeds the time limit.
        """
        # Enforce limits before proceeding
        self._enforce_step_limit()
        self._enforce_time_limit()
        
        # Increment step counter
        self.step_count += 1
        current_step = self.step_count
        
        # Perform inference
        action = self._infer(state, history)
        
        # Log the step (observation will be filled by the simulator)
        step_record = {
            "step": current_step,
            "action": action,
            "state_snapshot": state.get("snapshot_id", "unknown"),
            "timestamp": time.time()
        }
        self.trajectory_log.append(step_record)
        
        return StepResult(
            action=action,
            observation="",  # Filled by simulator
            success=False,   # Filled by simulator
            step_number=current_step,
            timestamp=time.time()
        )

    def run(self, initial_state: Dict[str, Any]) -> List[StepResult]:
        """
        Run the agent on a task until completion or limit.
        
        Args:
            initial_state: The starting GUI state.
        
        Returns:
            List of StepResult objects for the entire trajectory.
        
        Raises:
            StepLimitExceeded: If the agent exceeds the step limit.
            TimeLimitExceeded: If the agent exceeds the time limit.
        """
        self.step_count = 0
        self.start_time = time.time()
        self.trajectory_log = []
        
        history: List[Dict[str, Any]] = []
        current_state = initial_state
        results: List[StepResult] = []
        
        # Main loop
        while True:
            # Check if task is complete (simulator sets success flag)
            if current_state.get("task_complete", False):
                break
            
            # Perform a step
            result = self.step(current_state, history)
            results.append(result)
            
            # Update history for next iteration
            history.append({
                "action": result.action,
                "observation": result.observation,
                "success": result.success
            })
            
            # Check limits again after step
            self._enforce_step_limit()
            self._enforce_time_limit()
            
            # In a real implementation, the simulator would update current_state
            # based on the action and return the new state.
            # For the base class, we assume the caller updates the state.
            # This is a placeholder to prevent infinite loops in tests.
            # Subclasses or the runner will provide the actual state update mechanism.
            if current_state.get("simulate_next_state"):
                # This branch is for testing where the state updates automatically
                current_state = current_state["simulate_next_state"](current_state, result.action)
            else:
                # If no state update mechanism is provided, we assume the task is done
                # or the caller will inject the next state externally.
                break
        
        return results

    def get_trajectory(self) -> List[Dict[str, Any]]:
        """Return the full trajectory log."""
        return self.trajectory_log

    def reset(self) -> None:
        """Reset the agent's internal state for a new task."""
        self.step_count = 0
        self.start_time = None
        self.trajectory_log = []