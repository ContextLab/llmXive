import os
import sys
import json
import logging
import random
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from utils.config import set_seeds, get_seed

logger = logging.getLogger(__name__)

class BKTState:
    """Represents the state of a student in the BKT model."""
    
    def __init__(self, knowledge_probability: float = 0.0, has_answered: bool = False):
        self.knowledge_probability = knowledge_probability
        self.has_answered = has_answered
        self.attempts = 0
        self.correct_count = 0

    def __repr__(self):
        return f"BKTState(k={self.knowledge_probability:.3f}, attempts={self.attempts})"

class BKTModel:
    """
    Bayesian Knowledge Tracing (BKT) Model.
    
    Implements the standard BKT model with:
    - p_l0: Initial probability of knowing the skill
    - p_t: Probability of learning the skill (transition from L0 to L1)
    - p_g: Probability of guessing (correct answer when not knowing)
    - p_s: Probability of slipping (incorrect answer when knowing)
    """
    
    def __init__(self, p_l0: float, p_t: float, p_g: float, p_s: float):
        self.p_l0 = p_l0
        self.p_t = p_t
        self.p_g = p_g
        self.p_s = p_s
        self.state = BKTState(knowledge_probability=p_l0)

    def reset_state(self):
        """Reset the student state to initial conditions."""
        self.state = BKTState(knowledge_probability=self.p_l0)
        self.state.attempts = 0
        self.state.correct_count = 0

    def step(self) -> Dict[str, Any]:
        """
        Perform one step of the BKT simulation.
        
        Returns a dictionary with:
        - knowledge_state: Current probability of knowing
        - correct: Whether the answer was correct (bool)
        """
        # Determine if student knows the skill (binary state for decision)
        # We use the probability to sample the true state
        knows_skill = random.random() < self.state.knowledge_probability
        
        # Determine correctness based on true state
        if knows_skill:
            # If knows, correct with prob (1 - p_s)
            is_correct = random.random() > self.p_s
        else:
            # If doesn't know, correct with prob p_g
            is_correct = random.random() < self.p_g
        
        # Update knowledge state based on outcome
        self._update_knowledge_state(is_correct)
        
        self.state.attempts += 1
        if is_correct:
            self.state.correct_count += 1
        
        return {
            "knowledge_state": self.state.knowledge_probability,
            "correct": is_correct,
            "state_binary": knows_skill,
            "attempts": self.state.attempts
        }

    def _update_knowledge_state(self, is_correct: bool):
        """
        Update the probability of knowing based on the observation.
        
        Uses Bayes' rule to update P(L1 | Observation).
        """
        p = self.state.knowledge_probability
        
        if is_correct:
            # P(L1 | Correct) = P(Correct | L1) * P(L1) / P(Correct)
            # P(Correct | L1) = 1 - p_s
            # P(Correct) = (1 - p_s) * p + p_g * (1 - p)
            
            numerator = (1 - self.p_s) * p
            denominator = (1 - self.p_s) * p + self.p_g * (1 - p)
            
            if denominator == 0:
                new_p = 0.0
            else:
                new_p = numerator / denominator
        else:
            # P(L1 | Incorrect) = P(Incorrect | L1) * P(L1) / P(Incorrect)
            # P(Incorrect | L1) = p_s
            # P(Incorrect) = p_s * p + (1 - p_g) * (1 - p)
            
            numerator = self.p_s * p
            denominator = self.s * p + (1 - self.p_g) * (1 - p)
            
            if denominator == 0:
                new_p = 0.0
            else:
                new_p = numerator / denominator
        
        # Apply learning transition if correct and not already known?
        # Actually, the standard BKT update is the Bayesian update above.
        # The learning transition (p_t) is implicitly handled in the prior for the NEXT step
        # if we were modeling discrete states. In the continuous probability version,
        # the update rule above is sufficient.
        # However, some implementations add p_t explicitly if correct.
        # Let's stick to the standard Bayesian update.
        
        # Clamp to [0, 1]
        self.state.knowledge_probability = max(0.0, min(1.0, new_p))

def bkt_transition(current_p: float, is_correct: bool, p_t: float, p_g: float, p_s: float) -> float:
    """
    Compute the next knowledge probability given current state and observation.
    
    This is a helper function for direct calculation.
    """
    if is_correct:
        numerator = (1 - p_s) * current_p
        denominator = (1 - p_s) * current_p + p_g * (1 - current_p)
    else:
        numerator = p_s * current_p
        denominator = p_s * current_p + (1 - p_g) * (1 - current_p)
    
    if denominator == 0:
        return 0.0
    
    return numerator / denominator

class BKTSimulator:
    """
    High-level simulator for running BKT simulations on a population.
    """
    
    def __init__(self, p_l0: float, p_t: float, p_g: float, p_s: float):
        self.model_params = {
            'p_l0': p_l0,
            'p_t': p_t,
            'p_g': p_g,
            'p_s': p_s
        }
        self.current_model = BKTModel(**self.model_params)

    def reset_state(self):
        """Reset the internal model state."""
        self.current_model.reset_state()

    def step(self) -> Dict[str, Any]:
        """Perform one simulation step."""
        return self.current_model.step()

def main():
    """Example usage of BKT Simulator."""
    # Set seeds for reproducibility
    set_seeds(42)
    
    simulator = BKTSimulator(p_l0=0.2, p_t=0.3, p_g=0.1, p_s=0.1)
    
    print("Running BKT simulation for 5 attempts...")
    for i in range(5):
        result = simulator.step()
        print(f"Attempt {i+1}: Knowledge={result['knowledge_state']:.3f}, Correct={result['correct']}")

if __name__ == "__main__":
    main()