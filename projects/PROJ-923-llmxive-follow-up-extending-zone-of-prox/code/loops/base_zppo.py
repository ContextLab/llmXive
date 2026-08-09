"""
Base ZPPO (Zero-shot Policy Prompt Optimization) Implementation.
Implements the static NCQ generation and training loop with Gaussian noise injection.
"""
import json
import random
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from data.generators import generate_synthetic_rollout_log
from utils.logging import get_logger, info, debug, warning
from utils.seeds import get_rng
from config import get_config

logger = get_logger(__name__)

# Constants for noise injection (FR-008)
NOISE_SIGMA = 0.05

class StaticNCQGenerator:
    """Generates static Negative Candidate-included Questions."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)

    def generate_ncq(self, question_data: Dict[str, Any], buffer_cycle: int) -> str:
        """
        Generates an NCQ prompt for a given question and buffer cycle.
        Includes all known failure modes (negative candidates) for every step.
        """
        prompt_template = self.config.get("ncq_template", "Question: {question}\nOptions: {options}\nNegative Candidates: {negatives}\nAnswer:")
        
        question = question_data.get("question", "")
        options = ", ".join(question_data.get("options", []))
        
        # In static mode, negatives are fixed based on the dataset or generated once
        negatives = question_data.get("negative_candidates", ["Distractor A", "Distractor B", "Distractor C"])
        negatives_str = ", ".join(negatives)

        return prompt_template.format(
            question=question,
            options=options,
            negatives=negatives_str
        )

class StaticZPPOLoop:
    """
    Implements the static ZPPO training loop.
    Runs for a fixed number of buffer cycles, recording accuracy per cycle.
    Injects Gaussian noise into confidence scores at each step (FR-008).
    """

    def __init__(self, config: Dict[str, Any], student_model, ncq_generator: StaticNCQGenerator):
        self.config = config
        self.student_model = student_model
        self.ncq_generator = ncq_generator
        self.logger = get_logger(__name__)
        self.results_log = []

    def _inject_noise(self, confidence: float) -> float:
        """
        Injects Gaussian noise (sigma=0.05) into the confidence score.
        Clamps result to [0.0, 1.0].
        """
        rng = get_rng()
        noise = rng.normal(0, NOISE_SIGMA)
        noisy_confidence = confidence + noise
        return max(0.0, min(1.0, noisy_confidence))

    def run_cycle(self, cycle_idx: int, rollout_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes a single buffer cycle.
        1. Generates NCQ prompt.
        2. Simulates student response (with noise).
        3. Updates student confidence.
        4. Records metrics.
        """
        info(f"Running buffer cycle {cycle_idx}")
        
        cycle_results = []
        
        for item in rollout_data:
            # 1. Generate NCQ
            ncq_prompt = self.ncq_generator.generate_ncq(item, cycle_idx)
            
            # 2. Simulate Student Response (Get raw confidence from model)
            raw_confidence = self.student_model.predict_confidence(ncq_prompt, item)
            
            # 3. Inject Noise (FR-008)
            noisy_confidence = self._inject_noise(raw_confidence)
            
            # 4. Update Student Model (Simplified update logic)
            # In a real loop, this would update internal state based on the noisy confidence
            # For simulation, we just record the noisy confidence as the "observed" confidence
            self.student_model.update_confidence(item["id"], noisy_confidence)
            
            cycle_results.append({
                "step_id": item["id"],
                "cycle": cycle_idx,
                "raw_confidence": raw_confidence,
                "noisy_confidence": noisy_confidence,
                "prompt_length": len(ncq_prompt),
                "is_correct": item.get("is_correct", False)
            })

        # Calculate cycle metrics
        correct_count = sum(1 for r in cycle_results if r["is_correct"])
        total_count = len(cycle_results)
        accuracy = correct_count / total_count if total_count > 0 else 0.0
        avg_confidence = np.mean([r["noisy_confidence"] for r in cycle_results])

        cycle_summary = {
            "cycle": cycle_idx,
            "accuracy": accuracy,
            "avg_confidence": avg_confidence,
            "steps_processed": total_count
        }

        self.results_log.append(cycle_summary)
        info(f"Cycle {cycle_idx} complete. Accuracy: {accuracy:.4f}, Avg Confidence: {avg_confidence:.4f}")

        return cycle_summary

    def run(self, num_cycles: int, rollout_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Runs the full training loop for the specified number of cycles.
        """
        info(f"Starting Static ZPPO simulation for {num_cycles} cycles")
        
        for cycle in range(num_cycles):
            self.run_cycle(cycle, rollout_data)

        return self.results_log

def run_static_zppo_simulation(config_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Entry point for running the static ZPPO simulation.
    Loads config, generates data, runs loop, and returns results.
    """
    config = get_config(config_path)
    
    # Initialize components
    student_model = config.get("student_model_instance") # Assuming this is passed or mocked in real run
    if student_model is None:
        from models.student_sim import SimulatedStudent
        student_model = SimulatedStudent(config)

    ncq_generator = StaticNCQGenerator(config)
    loop = StaticZPPOLoop(config, student_model, ncq_generator)

    # Generate or load rollout data
    # For this simulation, we generate synthetic data as per T012
    rollout_data = generate_synthetic_rollout_log(config)

    # Run simulation
    results = loop.run(num_cycles=config.get("num_buffer_cycles", 10), rollout_data=rollout_data)

    return results
