import json
import random
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from models.cap_classifier import CAPClassifier, classify_confidence
from utils.seeds import get_rng
from utils.noise import inject_noise
from utils.logging import get_logger, info, warning, error
from config import get_config

class DynamicNCQGenerator:
    """
    Generates Negative Candidate-included Questions (NCQ) dynamically.
    Filters candidates based on CAPClassifier output.
    Enforces FR-007: Minimum threshold fallback if pruning results in zero candidates.
    """
    def __init__(self, pool_size: int, classifier: CAPClassifier):
        self.pool_size = pool_size
        self.classifier = classifier
        self.config = get_config()
        # Minimum candidates to retain to avoid empty prompts (FR-007)
        self.min_threshold = getattr(self.config, 'min_candidates_threshold', 1)

    def generate_prompt(self, task_id: str, cycle: int, all_candidates: List[Dict]) -> List[Dict]:
        """
        Generates a dynamic prompt based on CAP classification.
        
        Args:
            task_id: The ID of the current task.
            cycle: The current training cycle number.
            all_candidates: List of all available negative candidates.
            
        Returns:
            A filtered list of candidates to include in the prompt.
        """
        # Get classification from the CAP classifier
        classification = self.classifier.classify()
        
        # Determine which candidates to keep based on classification
        # The classifier logic (T021/T021a) identifies 'fluctuating' candidates
        # as the ones to retain. 'consistently rejected' and 'consistently accepted'
        # are pruned.
        candidates_to_keep = self.classifier.get_candidates_to_keep(
            all_candidates, classification
        )
        
        # FR-007: Fallback mechanism
        # If the resulting set is empty or below the minimum threshold,
        # fallback to the full set (or a minimal safe set) to prevent empty prompts.
        if len(candidates_to_keep) < self.min_threshold:
            warning(
                f"Cycle {cycle}: Filtered set size ({len(candidates_to_keep)}) "
                f"below threshold ({self.min_threshold}). Fallback to full set."
            )
            # Fallback to full set as per FR-007
            return all_candidates
        
        info(
            f"Cycle {cycle}: Retained {len(candidates_to_keep)} candidates "
            f"after CAP pruning."
        )
        return candidates_to_keep

class CAPZPPOLoop:
    """
    Implements the Confidence-Adaptive Pruning (CAP) ZPPO training loop.
    Updates student confidence using attention-weighted rule, records prompt length per cycle.
    """
    def __init__(self, seed: int, num_cycles: int, pool_size: int):
        self.rng = get_rng(seed)
        self.num_cycles = num_cycles
        self.pool_size = pool_size
        self.classifier = CAPClassifier()
        self.generator = DynamicNCQGenerator(pool_size, self.classifier)
        self.history: List[Dict[str, Any]] = []
        self.config = get_config()
        
        # Hyperparameters from config
        self.alpha = getattr(self.config, 'alpha', 0.1)
        self.initial_candidate_pool_size = getattr(self.config, 'initial_candidate_pool_size', pool_size)

    def run(self) -> List[Dict[str, Any]]:
        """
        Runs the CAP-ZPPO simulation.
        
        Returns:
            List of records containing cycle, confidence, correctness, and prompt length.
        """
        info(f"Running CAP-ZPPO for {self.num_cycles} cycles.")
        
        # Initial state
        current_conf = 0.5
        expert_conf = 0.95
        
        # Generate all candidates for the task
        # In a real scenario, these would come from a loader, but for the simulation
        # we generate them as per T012/T015 context
        all_candidates = [
            {"task_id": "task_001", "candidate_id": i, "text": f"neg_candidate_{i}"} 
            for i in range(self.pool_size)
        ]

        for cycle in range(self.num_cycles):
            # 1. Generate dynamic prompt using CAP logic
            prompt = self.generator.generate_prompt("task_001", cycle, all_candidates)
            prompt_length = len(prompt)
            
            # 2. Calculate prompt_length_factor for learning dynamics
            # Formula: prompt_length_factor = 1 / current_prompt_length
            # Using max(1, ...) to avoid division by zero
            current_factor = 1 / max(1, prompt_length)

            # 3. Inject noise into confidence (FR-008, T026)
            # MUST call inject_noise at every step
            noisy_conf = inject_noise(
                confidence=current_conf, 
                sigma=0.05, 
                rng=self.rng
            )
            
            # 4. Simulate student prediction based on noisy confidence
            # Use the noisy confidence for the decision
            correct = bool(self.rng.random() < noisy_conf)
            
            # 5. Update confidence using attention-weighted rule
            # Formula: new_conf = current_conf + alpha * (expert_conf - current_conf) * (1 - prompt_length_factor)
            # This represents learning: moving towards expert confidence, modulated by prompt complexity
            delta = self.alpha * (expert_conf - current_conf) * (1 - current_factor)
            current_conf += delta
            current_conf = float(np.clip(current_conf, 0.0, 1.0))

            # 6. Update the CAP classifier with the current cycle's confidence
            # This allows the classifier to track history (mean/variance) for future pruning
            self.classifier.add_confidence(cycle, noisy_conf)

            record = {
                "cycle": cycle,
                "confidence": float(noisy_conf),
                "correct": correct,
                "prompt_length": prompt_length,
                "candidates_remaining": prompt_length,
                "total_candidates": self.pool_size
            }
            self.history.append(record)
            
            debug(f"Cycle {cycle}: conf={noisy_conf:.3f}, len={prompt_length}, correct={correct}")
        
        return self.history

def run_cap_zppo_simulation(seed: int, num_cycles: int = 50, pool_size: int = 10) -> List[Dict[str, Any]]:
    """
    Entry point for running a single CAP-ZPPO simulation.
    
    Args:
        seed: Random seed for reproducibility.
        num_cycles: Number of training cycles to run.
        pool_size: Initial size of the negative candidate pool.
        
    Returns:
        List of simulation records.
    """
    loop = CAPZPPOLoop(seed, num_cycles, pool_size)
    return loop.run()