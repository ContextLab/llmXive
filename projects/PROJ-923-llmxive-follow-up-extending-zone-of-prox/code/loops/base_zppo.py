"""
Base ZPPO Implementation: Static Negative Candidate-included Question (NCQ) Loop.

This module implements the static ZPPO training loop as described in the original paper.
It uses a fixed set of negative candidates for all cycles and records accuracy metrics.
"""

import json
import random
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from project API surface
from data.generators import generate_synthetic_rollout_log
from data.loaders import load_synthetic_rollout_log
from models.student_sim import SimulatedStudent, StudentState
from utils.seeds import get_rng
from utils.noise import inject_noise
from utils.logging import get_logger, info, debug, error
from config import get_config

logger = get_logger(__name__)


class StaticNCQGenerator:
    """
    Generates a static Negative Candidate-included Question (NCQ) prompt.
    
    The prompt includes the task question and a fixed set of negative candidates
    (distractors) that remain constant throughout the training loop.
    """

    def __init__(self, negative_candidates: List[Dict[str, Any]]):
        """
        Initialize the generator with a fixed set of negative candidates.
        
        Args:
            negative_candidates: List of negative candidate dictionaries.
        """
        self.negative_candidates = negative_candidates
        logger.info(f"Initialized StaticNCQGenerator with {len(negative_candidates)} candidates")

    def generate_prompt(self, task: Dict[str, Any], cycle: int) -> str:
        """
        Generate the NCQ prompt for a specific task and cycle.
        
        Args:
            task: Dictionary containing task details (question, ground truth, etc.).
            cycle: Current training cycle number (unused for static generation).
        
        Returns:
            str: The formatted NCQ prompt string.
        """
        question = task.get("question", "")
        # Format negative candidates
        neg_items = []
        for i, cand in enumerate(self.negative_candidates):
            neg_text = cand.get("text", "Unknown")
            neg_items.append(f"{i+1}. {neg_text}")
        
        neg_section = "\n".join(neg_items)
        
        prompt = (
            f"Task: {task.get('task_id', 'Unknown')}\n"
            f"Question: {question}\n"
            f"Negative Candidates:\n{neg_section}\n"
            f"Instruction: Select the best answer from the options above."
        )
        return prompt

    def get_candidate_count(self) -> int:
        """Return the number of negative candidates in the static set."""
        return len(self.negative_candidates)


class StaticZPPOLoop:
    """
    Implements the static ZPPO training loop.
    
    This loop runs for a fixed number of buffer cycles, simulating student
    responses with noise injection and recording accuracy metrics per cycle.
    """

    def __init__(
        self,
        student: SimulatedStudent,
        ncq_generator: StaticNCQGenerator,
        rollout_log: List[Dict[str, Any]],
        rng: np.random.Generator,
        num_cycles: int = 10
    ):
        """
        Initialize the static ZPPO loop.
        
        Args:
            student: The simulated student model.
            ncq_generator: The static NCQ prompt generator.
            rollout_log: The synthetic rollout log data.
            rng: Numpy random generator for noise injection.
            num_cycles: Number of training cycles to run.
        """
        self.student = student
        self.ncq_generator = ncq_generator
        self.rollout_log = rollout_log
        self.rng = rng
        self.num_cycles = num_cycles
        self.history: List[Dict[str, Any]] = []
        
        logger.info(f"Initialized StaticZPPOLoop with {num_cycles} cycles and {len(rollout_log)} tasks")

    def run(self) -> List[Dict[str, Any]]:
        """
        Execute the static ZPPO training loop.
        
        Returns:
            List[Dict[str, Any]]: History of results per cycle containing:
                - cycle: Cycle number
                - accuracy: Accuracy for this cycle
                - avg_confidence: Average confidence score
                - prompt_length: Average prompt length
                - noise_injected: Whether noise was injected (always True)
        """
        info("Starting Static ZPPO Training Loop")
        debug(f"Number of tasks: {len(self.rollout_log)}")
        debug(f"Number of cycles: {self.num_cycles}")

        for cycle in range(1, self.num_cycles + 1):
            cycle_results = []
            total_confidence = 0.0
            total_prompt_len = 0.0
            
            # Process each task in the rollout log
            for task_data in self.rollout_log:
                task_id = task_data.get("task_id")
                expert_confidence = task_data.get("expert_confidence", 0.0)
                
                # Generate static NCQ prompt
                prompt = self.ncq_generator.generate_prompt(task_data, cycle)
                prompt_len = len(prompt)
                
                # Inject noise into expert confidence as per FR-008
                # Using sigma=0.05 as defined in T026
                noisy_expert_conf = inject_noise(
                    confidence=expert_confidence,
                    sigma=0.05,
                    rng=self.rng
                )
                
                # Update student state and get response
                student_state = self.student.update(
                    task_id=task_id,
                    expert_confidence=noisy_expert_conf,
                    prompt_length=prompt_len,
                    cycle=cycle
                )
                
                current_confidence = student_state.current_confidence
                
                # Determine correctness (simplified: if student confidence > 0.5 and matches expert trend)
                # In a real simulation, this would compare against ground truth
                is_correct = 1 if current_confidence > 0.5 else 0
                
                cycle_results.append({
                    "task_id": task_id,
                    "prompt": prompt,
                    "confidence": current_confidence,
                    "is_correct": is_correct,
                    "cycle": cycle
                })
                
                total_confidence += current_confidence
                total_prompt_len += prompt_len
            
            # Calculate cycle metrics
            num_tasks = len(self.rollout_log)
            accuracy = sum(r["is_correct"] for r in cycle_results) / num_tasks
            avg_confidence = total_confidence / num_tasks
            avg_prompt_len = total_prompt_len / num_tasks
            
            cycle_record = {
                "cycle": cycle,
                "accuracy": accuracy,
                "avg_confidence": avg_confidence,
                "prompt_length": avg_prompt_len,
                "noise_injected": True,
                "details": cycle_results
            }
            
            self.history.append(cycle_record)
            info(f"Cycle {cycle}: Accuracy={accuracy:.4f}, AvgConf={avg_confidence:.4f}, PromptLen={avg_prompt_len:.1f}")
            
            # Log detailed results for first and last cycle
            if cycle == 1 or cycle == self.num_cycles:
                debug(f"Cycle {cycle} details: {json.dumps(cycle_results[:3], indent=2)}")

        return self.history


def run_static_zppo_simulation(
    seed: int,
    num_cycles: Optional[int] = None,
    output_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Run a complete static ZPPO simulation from start to finish.
    
    This function:
    1. Initializes the random seed
    2. Loads or generates the synthetic rollout log
    3. Creates the student model
    4. Generates static negative candidates
    5. Runs the training loop
    6. Returns the convergence history
    
    Args:
        seed: Random seed for reproducibility.
        num_cycles: Number of training cycles (default from config).
        output_path: Optional path to save results.
    
    Returns:
        List[Dict[str, Any]]: Convergence history with accuracy per cycle.
    """
    # Initialize RNG
    rng = get_rng(seed)
    logger.info(f"Running static ZPPO simulation with seed={seed}")
    
    # Load config
    config = get_config()
    if num_cycles is None:
        num_cycles = config.get("num_cycles", 10)
    
    # Load synthetic rollout log (generated by T012)
    try:
        rollout_log = load_synthetic_rollout_log()
    except Exception as e:
        error(f"Failed to load synthetic rollout log: {e}")
        raise
    
    if not rollout_log:
        error("Rollout log is empty. Cannot run simulation.")
        raise ValueError("Empty rollout log")
    
    # Initialize student model
    student = SimulatedStudent(rng=rng)
    
    # Generate static negative candidates (first 5 tasks as distractors)
    # In a real scenario, these would be generated from the task pool
    negative_candidates = []
    for i, task in enumerate(rollout_log[:5]):
        negative_candidates.append({
            "task_id": f"neg_{task.get('task_id', i)}",
            "text": f"Negative candidate for {task.get('task_id', i)}",
            "confidence": 0.0
        })
    
    # Create static NCQ generator
    ncq_generator = StaticNCQGenerator(negative_candidates)
    
    # Create and run the loop
    loop = StaticZPPOLoop(
        student=student,
        ncq_generator=ncq_generator,
        rollout_log=rollout_log,
        rng=rng,
        num_cycles=num_cycles
    )
    
    history = loop.run()
    
    # Save results if output path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(history, f, indent=2)
        info(f"Results saved to {output_path}")
    
    return history