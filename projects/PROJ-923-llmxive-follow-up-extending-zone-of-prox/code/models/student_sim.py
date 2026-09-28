import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from utils.logging import get_logger, info, debug, warning
from utils.seeds import get_rng
from config import get_config

@dataclass
class StudentState:
    """
    Represents the internal state of the simulated student model.
    Tracks confidence scores per task and learning parameters.
    """
    task_id: str
    current_confidence: float
    expert_confidence: float  # Ground truth expert confidence for the task
    prompt_length_factor: float  # Normalized prompt length (0.0 to 1.0)
    cycle: int = 0
    history: List[float] = None

    def __post_init__(self):
        if self.history is None:
            self.history = []

class SimulatedStudent:
    """
    Simulated student model that updates confidence scores based on
    the learning dynamics defined in T012.

    Formula: new_conf = current_conf + alpha * (expert_conf - current_conf) * (1 - prompt_length_factor)

    This class handles the simulation of a student interacting with the ZPPO loop,
    updating its confidence after each cycle based on the prompt length and the
    expert gap.
    """

    def __init__(self, seed: int):
        """
        Initialize the simulated student with a specific random seed for reproducibility.

        Args:
            seed (int): The random seed for the student's internal RNG.
        """
        self.seed = seed
        self.rng = get_rng(seed)
        self.logger = get_logger("SimulatedStudent")
        self.state_map: Dict[str, StudentState] = {}
        self.config = get_config()
        self.alpha = self.config.get("learning_alpha", 0.1)
        self.noise_sigma = self.config.get("noise_sigma", 0.05)

        info(f"Initialized SimulatedStudent with seed {seed}, alpha={self.alpha}, noise_sigma={self.noise_sigma}")

    def initialize_task(self, task_id: str, expert_confidence: float, initial_confidence: float = 0.5) -> None:
        """
        Initialize a new task state for the student.

        Args:
            task_id (str): Unique identifier for the task.
            expert_confidence (float): The expert's confidence in the correct answer (ground truth).
            initial_confidence (float): The student's starting confidence for this task.
        """
        if task_id in self.state_map:
            debug(f"Task {task_id} already initialized, resetting state.")

        self.state_map[task_id] = StudentState(
            task_id=task_id,
            current_confidence=initial_confidence,
            expert_confidence=expert_confidence,
            prompt_length_factor=0.0, # Will be updated per cycle
            cycle=0,
            history=[initial_confidence]
        )
        debug(f"Initialized task {task_id} with initial confidence {initial_confidence}")

    def update_confidence(self, task_id: str, prompt_length_factor: float, cycle: int) -> float:
        """
        Update the student's confidence for a specific task using the learning dynamics formula.

        Formula: new_conf = current_conf + alpha * (expert_conf - current_conf) * (1 - prompt_length_factor)

        Args:
            task_id (str): The task identifier.
            prompt_length_factor (float): Normalized prompt length (0.0 to 1.0).
            cycle (int): The current cycle number.

        Returns:
            float: The updated confidence score.
        """
        if task_id not in self.state_map:
            raise ValueError(f"Task {task_id} not initialized. Call initialize_task first.")

        state = self.state_map[task_id]

        # Calculate the expert gap
        expert_gap = state.expert_confidence - state.current_confidence

        # Calculate the prompt length factor influence
        # (1 - prompt_length_factor) implies that longer prompts (higher factor)
        # reduce the learning rate, while shorter prompts increase it.
        learning_rate_modifier = (1.0 - prompt_length_factor)

        # Calculate the update delta
        delta = self.alpha * expert_gap * learning_rate_modifier

        # Apply noise to the update as per FR-008
        noise = self.rng.normal(0.0, self.noise_sigma)
        delta += noise

        # Update confidence
        new_confidence = state.current_confidence + delta

        # Clamp confidence to [0.0, 1.0]
        new_confidence = float(np.clip(new_confidence, 0.0, 1.0))

        # Update state
        state.current_confidence = new_confidence
        state.prompt_length_factor = prompt_length_factor
        state.cycle = cycle
        state.history.append(new_confidence)

        debug(f"Task {task_id} Cycle {cycle}: Conf {state.history[-2]:.4f} -> {new_confidence:.4f} (Gap: {expert_gap:.4f}, PromptFactor: {prompt_length_factor:.4f})")

        return new_confidence

    def get_confidence(self, task_id: str) -> float:
        """
        Get the current confidence score for a task.

        Args:
            task_id (str): The task identifier.

        Returns:
            float: Current confidence score.
        """
        if task_id not in self.state_map:
            raise ValueError(f"Task {task_id} not initialized.")
        return self.state_map[task_id].current_confidence

    def get_history(self, task_id: str) -> List[float]:
        """
        Get the history of confidence scores for a task.

        Args:
            task_id (str): The task identifier.

        Returns:
            List[float]: List of confidence scores over time.
        """
        if task_id not in self.state_map:
            raise ValueError(f"Task {task_id} not initialized.")
        return self.state_map[task_id].history.copy()

    def reset(self) -> None:
        """
        Reset the student state for all tasks.
        """
        self.state_map.clear()
        info("Reset all student states.")