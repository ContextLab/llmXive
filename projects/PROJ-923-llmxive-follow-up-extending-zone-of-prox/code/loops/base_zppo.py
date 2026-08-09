import os
import json
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from utils.logging import get_logger, log_metric
from utils.seeds import get_seed
from models.state_store import StateStore, CycleRecord
from models.student_sim import SimulatedStudent
from data.loaders import load_mmlu_held_out_set
from config import get_config

logger = get_logger(__name__)

class StaticNCQGenerator:
    """Generates static Negative Candidate-included Question prompts."""

    def __init__(self, held_out_data: List[Dict], config: Dict):
        self.held_out_data = held_out_data
        self.config = config
        self.negative_candidates = config.get('negative_candidates', [])
        logger.info(f"Initialized StaticNCQGenerator with {len(held_out_data)} questions and {len(self.negative_candidates)} negative candidates.")

    def generate_prompt(self, question_idx: int, cycle_id: int) -> Dict[str, Any]:
        """
        Generates a prompt for a specific question and cycle.
        In the static baseline, the negative candidates are always included.
        """
        if question_idx >= len(self.held_out_data):
            raise IndexError(f"Question index {question_idx} out of range for held-out data.")

        item = self.held_out_data[question_idx]
        question_text = item.get('question', '')
        correct_answer = item.get('answer', '')
        
        # Static: Always include all negative candidates
        candidates = self.negative_candidates.copy()
        
        prompt_content = {
            "question": question_text,
            "correct_answer": correct_answer,
            "negative_candidates": candidates,
            "cycle_id": cycle_id,
            "prompt_type": "static_ncq"
        }
        
        return prompt_content

class StaticZPPOLoop:
    """
    Implements the static ZPPO training loop.
    Simulates a student model learning from a static NCQ prompt.
    """

    def __init__(self, config: Dict, state_store: StateStore):
        self.config = config
        self.state_store = state_store
        self.student = SimulatedStudent(config)
        self.ncq_generator = None
        self.held_out_data = None
        self.num_cycles = config.get('simulation', {}).get('num_cycles', 10)
        self.noise_sigma = config.get('simulation', {}).get('noise_sigma', 0.05)
        
        logger.info(f"Initialized StaticZPPOLoop for {self.num_cycles} cycles.")

    def initialize(self, held_out_data: List[Dict]):
        """Initialize the loop with held-out data."""
        self.held_out_data = held_out_data
        self.ncq_generator = StaticNCQGenerator(held_out_data, self.config)
        self.student.reset()
        logger.info("StaticZPPOLoop initialized with held-out data.")

    def run_one_cycle(self, cycle_id: int) -> Dict[str, Any]:
        """
        Executes a single training cycle.
        1. Generate prompt (Static NCQ)
        2. Simulate student response and confidence
        3. Inject Gaussian noise into confidence (FR-008)
        4. Update student state
        5. Record metrics
        """
        if self.ncq_generator is None or self.held_out_data is None:
            raise RuntimeError("Loop not initialized. Call initialize() first.")

        # Select a random question for this cycle (or iterate sequentially)
        # For simulation, we'll iterate or sample. Let's sample for statistical variance.
        question_idx = np.random.randint(0, len(self.held_out_data))
        
        # 1. Generate Prompt
        prompt_data = self.ncq_generator.generate_prompt(question_idx, cycle_id)
        
        # 2. Simulate Student Response
        # Get base confidence from student model based on question difficulty and current state
        base_confidence = self.student.predict_confidence(prompt_data)
        
        # 3. Inject Gaussian Noise (FR-008)
        # Add noise to the confidence score to ensure statistical variance
        noise = np.random.normal(0, self.noise_sigma)
        noisy_confidence = base_confidence + noise
        # Clip to valid probability range [0, 1]
        noisy_confidence = np.clip(noisy_confidence, 0.0, 1.0)
        
        logger.debug(f"Cycle {cycle_id}: Base Confidence={base_confidence:.4f}, Noise={noise:.4f}, Noisy={noisy_confidence:.4f}")

        # 4. Update Student State
        # In a real loop, this would update weights. Here we update the internal state for tracking.
        self.student.update_state(noisy_confidence, prompt_data)
        
        # 5. Record Metrics
        is_correct = (noisy_confidence > 0.5) # Simplified correctness metric for simulation
        
        record = CycleRecord(
            cycle_id=cycle_id,
            prompt_length=len(str(prompt_data)),
            confidence_score=noisy_confidence,
            is_correct=is_correct,
            prompt_type="static_ncq",
            candidates_count=len(prompt_data.get('negative_candidates', [])),
            timestamp=None # Handled by record creation
        )
        
        self.state_store.add_record(record)
        
        return {
            "cycle_id": cycle_id,
            "confidence": noisy_confidence,
            "correct": is_correct,
            "prompt_length": record.prompt_length
        }

    def run(self) -> List[Dict[str, Any]]:
        """
        Runs the full training loop for the configured number of cycles.
        """
        logger.info(f"Starting StaticZPPO simulation for {self.num_cycles} cycles.")
        results = []
        
        for cycle_id in range(self.num_cycles):
            try:
                result = self.run_one_cycle(cycle_id)
                results.append(result)
                log_metric("static_confidence", result["confidence"], cycle_id)
                log_metric("static_correct", 1 if result["correct"] else 0, cycle_id)
            except Exception as e:
                logger.error(f"Error in cycle {cycle_id}: {e}", exc_info=True)
                break
                
        logger.info(f"StaticZPPO simulation completed. Total cycles: {len(results)}")
        return results

def run_baseline_simulation(config_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Entry point to run the baseline static ZPPO simulation.
    """
    config = get_config(config_path)
    seed_config = config.get('seed', {})
    np.random.seed(seed_config.get('seed', 42))
    
    logger.info("Starting Baseline Simulation (Static ZPPO)")
    
    # Initialize State Store
    state_store = StateStore()
    
    # Load Held-out Data
    # For this simulation, we use the synthetic loader as per T013
    from data.loaders import load_mmlu_held_out_set
    try:
        held_out_data = load_mmlu_held_out_set(config)
    except Exception as e:
        logger.error(f"Failed to load held-out data: {e}")
        # Fallback to synthetic if real data is unavailable for simulation context
        # Note: In production, this should fail loudly as per constraints, 
        # but for the simulation runner in this specific project context, 
        # we assume T013 handles the fallback logic or data availability.
        # If T013 is strictly real-data only, this would raise.
        # Assuming T013 provides the data structure here.
        raise e

    # Initialize Loop
    loop = StaticZPPOLoop(config, state_store)
    loop.initialize(held_out_data)
    
    # Run
    results = loop.run()
    
    return results
