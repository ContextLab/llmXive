import os
import json
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from utils.logging import get_logger, log_metric
from utils.seeds import get_seed
from models.state_store import StateStore, CycleRecord
from models.student_sim import SimulatedStudent
from models.cap_classifier import CAPClassifier
from data.loaders import load_mmlu_held_out_set
from config import get_config

logger = get_logger(__name__)

class CAPNCQGenerator:
    """
    Generates Confidence-Adaptive Pruning (CAP) Negative Candidate-included Question prompts.
    Filters candidates based on historical confidence scores.
    """

    def __init__(self, held_out_data: List[Dict], config: Dict, state_store: StateStore):
        self.held_out_data = held_out_data
        self.config = config
        self.state_store = state_store
        self.cap_classifier = CAPClassifier(state_store, config)
        self.negative_candidates = config.get('negative_candidates', [])
        self.min_candidates = config.get('simulation', {}).get('min_candidates', 1)
        
        logger.info(f"Initialized CAPNCQGenerator with {len(held_out_data)} questions.")

    def generate_prompt(self, question_idx: int, cycle_id: int) -> Dict[str, Any]:
        """
        Generates a prompt with pruned negative candidates based on CAP logic.
        """
        if question_idx >= len(self.held_out_data):
            raise IndexError(f"Question index {question_idx} out of range.")

        item = self.held_out_data[question_idx]
        question_text = item.get('question', '')
        correct_answer = item.get('answer', '')
        
        # Get pruned candidates from CAP classifier
        pruned_candidates = self.cap_classifier.get_active_candidates(cycle_id)
        
        # Fallback: If all candidates are pruned, use full set (or min set) to avoid empty prompt
        if len(pruned_candidates) < self.min_candidates:
            logger.warning(f"Cycle {cycle_id}: Pruned candidates too few ({len(pruned_candidates)}). Falling back to full set.")
            pruned_candidates = self.negative_candidates.copy()
            # Ensure we don't exceed a reasonable max if needed, but spec says fallback to full
        
        prompt_content = {
            "question": question_text,
            "correct_answer": correct_answer,
            "negative_candidates": pruned_candidates,
            "cycle_id": cycle_id,
            "prompt_type": "cap_ncq",
            "pruned_count": len(self.negative_candidates) - len(pruned_candidates)
        }
        
        return prompt_content

class CAPZPPOLoop:
    """
    Implements the CAP-ZPPO training loop.
    Dynamically adjusts the prompt based on student confidence history.
    """

    def __init__(self, config: Dict, state_store: StateStore):
        self.config = config
        self.state_store = state_store
        self.student = SimulatedStudent(config)
        self.ncq_generator = None
        self.held_out_data = None
        self.num_cycles = config.get('simulation', {}).get('num_cycles', 10)
        self.noise_sigma = config.get('simulation', {}).get('noise_sigma', 0.05)
        
        logger.info(f"Initialized CAPZPPOLoop for {self.num_cycles} cycles.")

    def initialize(self, held_out_data: List[Dict]):
        """Initialize the loop with held-out data."""
        self.held_out_data = held_out_data
        self.ncq_generator = CAPNCQGenerator(held_out_data, self.config, self.state_store)
        self.student.reset()
        logger.info("CAPZPPOLoop initialized with held-out data.")

    def run_one_cycle(self, cycle_id: int) -> Dict[str, Any]:
        """
        Executes a single training cycle with CAP logic.
        1. Generate prompt (Dynamic NCQ via CAP)
        2. Simulate student response and confidence
        3. Inject Gaussian noise into confidence (FR-008)
        4. Update student state
        5. Record metrics
        """
        if self.ncq_generator is None or self.held_out_data is None:
            raise RuntimeError("Loop not initialized. Call initialize() first.")

        # Select question
        question_idx = np.random.randint(0, len(self.held_out_data))
        
        # 1. Generate Prompt (CAP logic applied here)
        prompt_data = self.ncq_generator.generate_prompt(question_idx, cycle_id)
        
        # 2. Simulate Student Response
        base_confidence = self.student.predict_confidence(prompt_data)
        
        # 3. Inject Gaussian Noise (FR-008)
        # Add noise to the confidence score to ensure statistical variance
        noise = np.random.normal(0, self.noise_sigma)
        noisy_confidence = base_confidence + noise
        # Clip to valid probability range [0, 1]
        noisy_confidence = np.clip(noisy_confidence, 0.0, 1.0)
        
        logger.debug(f"Cycle {cycle_id} (CAP): Base Confidence={base_confidence:.4f}, Noise={noise:.4f}, Noisy={noisy_confidence:.4f}")

        # 4. Update Student State
        self.student.update_state(noisy_confidence, prompt_data)
        
        # 5. Record Metrics
        is_correct = (noisy_confidence > 0.5)
        
        record = CycleRecord(
            cycle_id=cycle_id,
            prompt_length=len(str(prompt_data)),
            confidence_score=noisy_confidence,
            is_correct=is_correct,
            prompt_type="cap_ncq",
            candidates_count=len(prompt_data.get('negative_candidates', [])),
            timestamp=None
        )
        
        self.state_store.add_record(record)
        
        return {
            "cycle_id": cycle_id,
            "confidence": noisy_confidence,
            "correct": is_correct,
            "prompt_length": record.prompt_length,
            "active_candidates": record.candidates_count
        }

    def run(self) -> List[Dict[str, Any]]:
        """
        Runs the full CAP-ZPPO training loop.
        """
        logger.info(f"Starting CAP-ZPPO simulation for {self.num_cycles} cycles.")
        results = []
        
        for cycle_id in range(self.num_cycles):
            try:
                result = self.run_one_cycle(cycle_id)
                results.append(result)
                log_metric("cap_confidence", result["confidence"], cycle_id)
                log_metric("cap_correct", 1 if result["correct"] else 0, cycle_id)
                log_metric("cap_prompt_len", result["prompt_length"], cycle_id)
            except Exception as e:
                logger.error(f"Error in cycle {cycle_id}: {e}", exc_info=True)
                break
                
        logger.info(f"CAP-ZPPO simulation completed. Total cycles: {len(results)}")
        return results

def set_seed(seed: int):
    """Helper to set seed for this module."""
    np.random.seed(seed)

def run_cap_simulation(config_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Entry point to run the CAP-ZPPO simulation.
    """
    config = get_config(config_path)
    seed_config = config.get('seed', {})
    np.random.seed(seed_config.get('seed', 42))
    
    logger.info("Starting CAP Simulation")
    
    # Initialize State Store
    state_store = StateStore()
    
    # Load Held-out Data
    from data.loaders import load_mmlu_held_out_set
    try:
        held_out_data = load_mmlu_held_out_set(config)
    except Exception as e:
        logger.error(f"Failed to load held-out data: {e}")
        raise e

    # Initialize Loop
    loop = CAPZPPOLoop(config, state_store)
    loop.initialize(held_out_data)
    
    # Run
    results = loop.run()
    
    return results
