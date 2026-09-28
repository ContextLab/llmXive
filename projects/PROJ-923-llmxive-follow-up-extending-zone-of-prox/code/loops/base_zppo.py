"""
Base ZPPO Implementation: Static Negative Candidate-included Question (NCQ) Loop.

This module implements the static baseline simulation for the ZPPO training loop.
It generates a fixed set of negative candidates for every step and runs the student
through a series of buffer cycles, recording accuracy and confidence metrics.

Dependencies:
- T008 (Seeds): For deterministic RNG
- T026 (Noise): For per-step Gaussian noise injection
- T012 (Generators): For synthetic rollout log generation
- T015 (Student Sim): For student state updates
"""

import json
import random
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from data.generators import generate_synthetic_rollout_log
from models.student_sim import SimulatedStudent, StudentState
from utils.noise import inject_noise
from utils.seeds import get_rng
from utils.logging import get_logger, info, debug, warning
from config import get_config

# Constants
DEFAULT_NOISE_SIGMA = 0.05
DEFAULT_CYCLES = 10

logger = get_logger(__name__)


class StaticNCQGenerator:
    """
    Generates a static set of negative candidates for the NCQ prompt.
    In the baseline scenario, this set remains constant across all cycles.
    """

    def __init__(self, candidate_pool: List[str], seed: int):
        """
        Initialize the generator with a pool of potential negative candidates.

        Args:
            candidate_pool: List of negative candidate strings (e.g., incorrect answers).
            seed: Random seed for reproducibility if sampling is needed.
        """
        self.candidate_pool = candidate_pool
        self.seed = seed
        self.rng = get_rng(seed)

        # For static baseline, we select a fixed subset once and reuse it
        # unless the pool is smaller than the desired prompt size.
        self.static_candidates = self._select_static_candidates()
        info(f"StaticNCQGenerator initialized with {len(self.static_candidates)} candidates.")

    def _select_static_candidates(self) -> List[str]:
        """
        Select a fixed subset of candidates to be used for all cycles.
        """
        if len(self.candidate_pool) == 0:
            warning("Empty candidate pool provided to StaticNCQGenerator.")
            return []

        # Determine the number of candidates to include (e.g., top 5 or all if < 5)
        num_candidates = min(5, len(self.candidate_pool))
        indices = self.rng.choice(len(self.candidate_pool), size=num_candidates, replace=False)
        return [self.candidate_pool[i] for i in indices]

    def generate_prompt(self, current_step: int, task_id: str) -> str:
        """
        Generate the NCQ prompt string for a given step.
        Since it is static, the content does not change based on history.

        Args:
            current_step: The current training step/cycle index.
            task_id: The identifier of the current task.

        Returns:
            A formatted string representing the NCQ prompt.
        """
        if not self.static_candidates:
            return f"Task: {task_id}\nInstruction: Solve the problem.\nNegative Candidates: None available."

        candidates_str = "\n".join([f"- {c}" for c in self.static_candidates])
        return (
            f"Task: {task_id}\n"
            f"Instruction: Solve the problem.\n"
            f"Negative Candidates to Consider:\n{candidates_str}\n"
            f"Step: {current_step}"
        )

    def get_candidates(self) -> List[str]:
        """Return the current static candidate list."""
        return self.static_candidates


class StaticZPPOLoop:
    """
    Implements the Static ZPPO Training Loop.

    This loop simulates the training process where the student interacts with
    a fixed NCQ prompt over multiple cycles. It records accuracy and confidence
    metrics per cycle.
    """

    def __init__(self, student: SimulatedStudent, ncq_generator: StaticNCQGenerator, config: Dict[str, Any]):
        """
        Initialize the loop.

        Args:
            student: The simulated student model instance.
            ncq_generator: The static NCQ generator instance.
            config: Configuration dictionary containing hyperparameters.
        """
        self.student = student
        self.ncq_generator = ncq_generator
        self.config = config
        self.rng = get_rng(config.get('seed', 42))

        # Hyperparameters
        self.num_cycles = config.get('num_cycles', DEFAULT_CYCLES)
        self.noise_sigma = config.get('noise_sigma', DEFAULT_NOISE_SIGMA)
        self.tasks = config.get('tasks', [])

        info(f"StaticZPPOLoop initialized for {self.num_cycles} cycles with sigma={self.noise_sigma}")

    def run_cycle(self, cycle_idx: int, task_id: str) -> Dict[str, Any]:
        """
        Execute a single training cycle.

        1. Generate the static NCQ prompt.
        2. Simulate student response and confidence.
        3. Inject Gaussian noise into confidence (FR-008).
        4. Update student state.
        5. Record metrics.

        Args:
            cycle_idx: Current cycle index (0-based).
            task_id: The task being solved.

        Returns:
            A dictionary containing cycle results (accuracy, confidence, prompt length).
        """
        # 1. Generate Prompt
        prompt = self.ncq_generator.generate_prompt(cycle_idx, task_id)
        prompt_length = len(prompt.split())

        # 2. Simulate Student Response
        # The student updates confidence based on the "expert gap" and "prompt length"
        # as per T012/T015 logic.
        # We simulate the interaction by calling the student's update method.
        student_state_before = self.student.get_state()

        # Simulate the student's "learning" from the prompt
        # In a real scenario, this would involve an LLM call. Here we use the simulation logic.
        # The student attempts to solve the task given the negative candidates.
        success = self.student.step(prompt, task_id)

        # Get updated state
        student_state_after = self.student.get_state()

        # 3. Inject Noise into Confidence
        # T026 requirement: Per-step Gaussian noise injection (σ=0.05)
        raw_confidence = student_state_after.confidence
        noisy_confidence = inject_noise(raw_confidence, sigma=self.noise_sigma)

        # Clamp confidence to [0, 1]
        noisy_confidence = np.clip(noisy_confidence, 0.0, 1.0)

        # Update student state with noisy confidence for next cycle
        self.student.update_confidence(noisy_confidence)

        # 4. Determine Accuracy (Binary: Correct/Incorrect based on threshold or ground truth)
        # For simulation, we assume accuracy correlates with confidence + noise effect
        # In a real loop, this would be compared against ground truth.
        # Here, we treat a confidence > 0.9 (after noise) as "Accepted/Correct" for the metric
        # or use the student's internal 'is_correct' flag if available.
        # Simplified for simulation:
        is_correct = 1.0 if noisy_confidence > 0.8 else 0.0

        result = {
            "cycle": cycle_idx,
            "task_id": task_id,
            "prompt_length": prompt_length,
            "raw_confidence": float(raw_confidence),
            "noisy_confidence": float(noisy_confidence),
            "accuracy": float(is_correct),
            "prompt_content": prompt
        }

        debug(f"Cycle {cycle_idx}: Acc={is_correct:.2f}, Conf={noisy_confidence:.4f}, Len={prompt_length}")
        return result

    def run(self, output_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Run the full training loop over all cycles and tasks.

        Args:
            output_path: Optional path to save the rollout log JSON.

        Returns:
            List of result dictionaries per cycle.
        """
        all_results = []
        info(f"Starting Static ZPPO Simulation for {len(self.tasks)} tasks and {self.num_cycles} cycles.")

        for task_id in self.tasks:
            info(f"Processing Task: {task_id}")
            for cycle in range(self.num_cycles):
                result = self.run_cycle(cycle, task_id)
                all_results.append(result)

            # Reset student state between tasks if necessary (e.g., new task context)
            # For this baseline, we assume the student carries over state or resets per task.
            # Per T012 logic, we might reset or continue. Let's reset per task for independent task evaluation.
            self.student.reset()

        info(f"Simulation complete. Total records: {len(all_results)}")

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(all_results, f, indent=2)
            info(f"Rollout log saved to {output_path}")

        return all_results


def run_static_zppo_simulation(
    seed: int,
    num_tasks: int = 10,
    num_cycles: int = DEFAULT_CYCLES,
    noise_sigma: float = DEFAULT_NOISE_SIGMA,
    output_dir: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function to orchestrate the static ZPPO simulation.

    Args:
        seed: Random seed for reproducibility.
        num_tasks: Number of tasks to simulate.
        num_cycles: Number of buffer cycles per task.
        noise_sigma: Standard deviation for Gaussian noise injection.
        output_dir: Directory to save the rollout log.

    Returns:
        List of cycle results.
    """
    logger.info(f"Running static ZPPO simulation: seed={seed}, tasks={num_tasks}, cycles={num_cycles}")

    # Load config
    config = get_config()
    config['seed'] = seed
    config['num_cycles'] = num_cycles
    config['noise_sigma'] = noise_sigma

    # Generate synthetic data / tasks
    # T012: Generate synthetic rollout log data (tasks, candidates)
    # We need a pool of negative candidates and a set of tasks.
    # Using the generator to create the initial state and candidates.
    synthetic_data = generate_synthetic_rollout_log(seed=seed, num_tasks=num_tasks)

    tasks = synthetic_data['tasks']
    candidate_pool = synthetic_data['negative_candidates']

    if not tasks:
        warning("No tasks generated. Simulation cannot proceed.")
        return []

    # Initialize Student (T015)
    student = SimulatedStudent(seed=seed, config=config)

    # Initialize Static NCQ Generator
    ncq_gen = StaticNCQGenerator(candidate_pool=candidate_pool, seed=seed)

    # Initialize Loop
    loop = StaticZPPOLoop(
        student=student,
        ncq_generator=ncq_gen,
        config=config
    )

    # Run
    output_path = output_dir / "rollout_log_static.json" if output_dir else None
    results = loop.run(output_path=output_path)

    return results