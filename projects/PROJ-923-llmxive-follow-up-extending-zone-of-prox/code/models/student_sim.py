import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from utils.logging import get_logger, info, debug, warning
from utils.seeds import get_rng
from utils.noise import inject_noise
from config import get_config

@dataclass
class StudentState:
    confidence: float
    correct_count: int
    total_count: int

class SimulatedStudent:
    def __init__(self, seed: int):
        self.rng = get_rng(seed)
        self.config = get_config()
        self.state = StudentState(
            confidence=0.5,
            correct_count=0,
            total_count=0
        )

    def update_confidence(self, expert_conf: float, prompt_length_factor: float) -> float:
        """
        Updates confidence using the formula:
        new_conf = current_conf + alpha * (expert_conf - current_conf) * (1 - prompt_length_factor)
        
        Applies Gaussian noise (sigma=0.05) to the confidence score at every step as per T026.
        
        Args:
            expert_conf: The expert's confidence score for the current step.
            prompt_length_factor: A factor derived from prompt length (1 / initial_candidate_pool_size).
            
        Returns:
            The updated confidence score after applying the learning dynamics and noise.
        """
        # 1. Calculate the base update without noise
        alpha = self.config.alpha
        delta = alpha * (expert_conf - self.state.confidence) * (1 - prompt_length_factor)
        new_conf = self.state.confidence + delta
        
        # 2. Clip to valid range [0.0, 1.0]
        new_conf = float(np.clip(new_conf, 0.0, 1.0))
        
        # 3. Inject Gaussian noise as per T026 requirement
        # T026 specifies sigma=0.05
        noisy_conf = inject_noise(new_conf, sigma=0.05, rng=self.rng)
        
        # 4. Final clip to ensure noise didn't push it out of bounds
        self.state.confidence = float(np.clip(noisy_conf, 0.0, 1.0))
        
        debug(f"Student confidence updated: {self.state.confidence:.4f} (expert: {expert_conf:.4f}, factor: {prompt_length_factor:.4f})")
        
        return self.state.confidence

    def predict(self, confidence: float) -> bool:
        """Simulates a prediction based on confidence."""
        # Use the noisy confidence for prediction if it was updated in the current step,
        # otherwise use the current state confidence.
        return bool(self.rng.random() < confidence)

    def record_result(self, correct: bool):
        self.state.total_count += 1
        if correct:
            self.state.correct_count += 1

    def get_accuracy(self) -> float:
        if self.state.total_count == 0:
            return 0.0
        return self.state.correct_count / self.state.total_count