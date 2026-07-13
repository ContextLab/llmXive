"""
Bayesian Knowledge Tracing (BKT) Simulator Module.

Implements a deterministic student simulation engine based on the BKT model.
Addresses Von Neumann's concern for "stability under perturbation" by ensuring
all stochastic processes are seeded deterministically via the `random` module,
controlled by the `set_seed` function imported from `utils.config`.

Dependencies:
  - T007: Schema definitions (contracts/)
  - T005: Config/seed management (utils/config.py)
"""

import os
import sys
import json
import logging
import random
import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

# Import seed management from T005
# Note: The API surface indicates `code/utils/config.py` exists.
# We import the specific function to ensure deterministic behavior.
try:
    from utils.config import set_seeds, get_seed
except ImportError:
    # Fallback for local execution if utils.config is not in path yet
    # In a real run, this import must succeed as per T005 completion.
    def set_seeds(seed: int = 42) -> None:
        """Fallback seed setter."""
        random.seed(seed)
    def get_seed() -> int:
        return 42

from utils.validation import validate_simulation_log

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BKTState:
    """
    Represents the internal state of a student in the BKT model.
    
    Attributes:
        learned: Boolean indicating if the skill is currently learned (L_t = 1).
        p_learn: Probability of learning the skill in one step (P(T)).
        p_guess: Probability of guessing correctly given unlearned state (P(G)).
        p_slip: Probability of slipping (answering incorrectly) given learned state (P(S)).
        p_initial: Prior probability of knowing the skill (L_0).
    """
    learned: bool = False
    p_learn: float = 0.3
    p_guess: float = 0.2
    p_slip: float = 0.1
    p_initial: float = 0.1
    
    # Derived probabilities
    p_correct_unlearned: float = field(init=False)
    p_correct_learned: float = field(init=False)

    def __post_init__(self):
        self.p_correct_unlearned = self.p_guess
        self.p_correct_learned = 1.0 - self.p_slip

    def get_p_correct(self) -> float:
        """Returns the probability of a correct response given current state."""
        if self.learned:
            return self.p_correct_learned
        else:
            return self.p_correct_unlearned

    def update_belief(self, observed_correct: bool) -> None:
        """
        Updates the belief state (learned/unlearned) based on an observation.
        Uses standard BKT update equations.
        
        Note: This method assumes a deterministic 'learned' flag for the student
        in this simulation context, but updates the *probability* of being learned
        for the next step if we were tracking probability. 
        
        For this simulator, we use a thresholded approach:
        If the student is 'unlearned', they transition to 'learned' with probability P(T).
        If the student is 'learned', they stay learned.
        
        However, the standard BKT update updates the *probability* L_t.
        Here we implement the transition logic for the discrete state simulation.
        """
        if self.learned:
            # Once learned, stays learned (standard BKT assumption)
            pass
        else:
            # If unlearned, might learn now with P(T)
            if random.random() < self.p_learn:
                self.learned = True
                logger.debug("Student transitioned to LEARNED state.")


@dataclass
class BKTModel:
    """
    Container for BKT parameters and the current state of a simulated student.
    
    This class encapsulates the parameters (P(G), P(S), P(T), L_0) and the
    current state of the student. It provides methods to step through
    problems and generate responses.
    """
    student_id: str
    problem_id: str
    state: BKTState = field(default_factory=BKTState)
    
    # Simulation metadata
    trial_count: int = 0
    total_correct: int = 0
    history: List[Dict[str, Any]] = field(default_factory=list)

    def step(self, problem_difficulty: float = 0.0) -> Dict[str, Any]:
        """
        Simulates a single student response to a problem.
        
        Args:
            problem_difficulty: Optional factor to adjust P(correct) slightly.
                              Not part of standard BKT but useful for simulation variance.
        
        Returns:
            A dictionary containing the simulation log entry.
        """
        self.trial_count += 1
        
        # Determine correctness based on current state
        p_correct = self.state.get_p_correct()
        
        # Apply difficulty modifier (simple logistic adjustment for simulation)
        # P_adj = p_correct * (1 - 0.1 * difficulty) to make harder problems slightly harder
        # This is a simulation heuristic, not strict BKT.
        adjusted_p_correct = max(0.0, min(1.0, p_correct * (1.0 - 0.1 * problem_difficulty)))
        
        is_correct = random.random() < adjusted_p_correct
        
        if is_correct:
            self.total_correct += 1
        
        # Update state (learning transition)
        # In standard BKT, learning happens *after* the response in the sequence L_t -> L_{t+1}
        # But here we model the transition as: Response -> Update State for next trial.
        # Actually, standard BKT: L_t -> Response -> Update L_{t+1}.
        # We update state AFTER the response to determine L_{t+1} for the next step.
        # Note: The `update_belief` in BKTState above handles the transition from Unlearned to Learned.
        self.state.update_belief(is_correct)
        
        # Construct log entry
        log_entry = {
            "student_id": self.student_id,
            "problem_id": self.problem_id,
            "trial": self.trial_count,
            "is_correct": is_correct,
            "state_before": "learned" if not self.state.learned else "unlearned", # Logic inverted in state logic? 
            # Correction: state.learned is True if learned.
            "state_before": "learned" if self.state.learned else "unlearned",
            "p_correct_estimated": adjusted_p_correct,
            "timestamp": None, # To be filled by runner
            "rt_seconds": None, # To be filled by runner
            "comprehension_rating": None # To be filled by runner
        }
        
        self.history.append(log_entry)
        return log_entry


def bkt_transition(
    p_guess: float, 
    p_slip: float, 
    p_learn: float, 
    p_initial: float, 
    n_trials: int, 
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Runs a full BKT simulation for a single student over n_trials.
    
    This function serves as a standalone entry point for generating a trace
    given specific parameters, useful for unit testing or batch generation.
    
    Args:
        p_guess: Probability of guessing correctly.
        p_slip: Probability of slipping.
        p_learn: Probability of learning per trial.
        p_initial: Prior probability of knowing.
        n_trials: Number of trials to simulate.
        seed: Optional seed for determinism.
    
    Returns:
        List of log entries.
    """
    if seed is not None:
        random.seed(seed)
    
    state = BKTState(
        learned=(random.random() < p_initial),
        p_learn=p_learn,
        p_guess=p_guess,
        p_slip=p_slip,
        p_initial=p_initial
    )
    
    model = BKTModel(student_id="sim_student", problem_id="sim_problem", state=state)
    
    results = []
    for _ in range(n_trials):
        results.append(model.step())
        
    return results


class BKTSimulator:
    """
    High-level orchestrator for running BKT simulations across multiple students.
    
    Ensures deterministic execution by initializing the random seed at the start
    of the simulation run, addressing the "stability under perturbation" requirement.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the simulator with configuration.
        
        Args:
            config: Dictionary containing simulation parameters:
                    - seed: int (optional)
                    - p_guess: float
                    - p_slip: float
                    - p_learn: float
                    - p_initial: float
                    - num_students: int
                    - num_trials: int
        """
        self.config = config
        self.seed = config.get('seed', 42)
        self.p_guess = config.get('p_guess', 0.2)
        self.p_slip = config.get('p_slip', 0.1)
        self.p_learn = config.get('p_learn', 0.3)
        self.p_initial = config.get('p_initial', 0.1)
        self.num_students = config.get('num_students', 100)
        self.num_trials = config.get('num_trials', 10)
        
        # Initialize seed for determinism
        set_seeds(self.seed)
        logger.info(f"BKTSimulator initialized with seed={self.seed}. "
                    f"Parameters: G={self.p_guess}, S={self.p_slip}, T={self.p_learn}, L0={self.p_initial}")

    def run(self) -> List[Dict[str, Any]]:
        """
        Executes the simulation for all configured students.
        
        Returns:
            A list of dictionaries representing the simulation logs.
        """
        all_logs = []
        
        for i in range(self.num_students):
            student_id = f"student_{i:04d}"
            # Create a fresh state for each student
            state = BKTState(
                learned=(random.random() < self.p_initial),
                p_learn=self.p_learn,
                p_guess=self.p_guess,
                p_slip=self.p_slip,
                p_initial=self.p_initial
            )
            
            model = BKTModel(
                student_id=student_id,
                problem_id="problem_A", # Assuming single problem for this phase or looped externally
                state=state
            )
            
            for t in range(self.num_trials):
                log_entry = model.step()
                log_entry['student_id'] = student_id
                # Fill in simulated RT and comprehension (placeholder logic, 
                # actual values filled by T023 logic or runner)
                # For now, we leave them as None or basic randoms if not handled externally
                # But per T020, we focus on the BKT logic.
                all_logs.append(log_entry)
                
        logger.info(f"Simulation complete. Generated {len(all_logs)} logs for {self.num_students} students.")
        return all_logs

    def save_logs(self, output_path: str) -> None:
        """
        Runs the simulation and saves the results to a JSON file.
        
        Args:
            output_path: Path to the output JSON file.
        """
        logs = self.run()
        
        # Validate a sample of logs against schema (T007/T008)
        if logs:
            # Basic validation check
            sample = logs[0]
            # Ensure required keys exist
            required_keys = ['student_id', 'problem_id', 'trial', 'is_correct', 'state_before']
            missing = [k for k in required_keys if k not in sample]
            if missing:
                raise ValueError(f"Generated log missing required keys: {missing}")

        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2)
        
        logger.info(f"Logs saved to {output_path}")


def main():
    """
    Entry point for running the BKT simulator as a script.
    Usage: python -m code.simulate.bkt_simulator
    """
    # Default configuration
    config = {
        'seed': 42,
        'p_guess': 0.2,
        'p_slip': 0.1,
        'p_learn': 0.3,
        'p_initial': 0.1,
        'num_students': 50,
        'num_trials': 10
    }
    
    # Allow override from environment or args if needed
    output_file = os.getenv('SIMULATION_OUTPUT', 'data/derived/bkt_simulation_logs.json')
    
    simulator = BKTSimulator(config)
    simulator.save_logs(output_file)
    print(f"Simulation complete. Output written to {output_file}")


if __name__ == '__main__':
    main()