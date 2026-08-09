import os
import json
import random
import numpy as np
from typing import List, Dict, Any, Optional
from utils.logging import get_logger
from utils.seeds import get_seed
from models.state_store import StateStore, CycleRecord

logger = get_logger(__name__)

def generate_synthetic_rollout_log(
    num_samples: int = 100,
    num_candidates: int = 4,
    seed: Optional[int] = None,
    task_type: str = "vlm"
) -> List[Dict[str, Any]]:
    """
    Generate a synthetic rollout log for initial state setup.
    
    This function creates a seeded random state for the simulation.
    It does NOT inject per-step noise (that is handled in the training loops).
    It generates the initial set of (question, candidate, confidence, ground_truth) records.
    
    Args:
        num_samples: Number of unique questions to generate.
        num_candidates: Number of negative candidates per question.
        seed: Random seed for reproducibility.
        task_type: Type of task ('vlm' or 'llm').
        
    Returns:
        A list of dictionaries representing the rollout log entries.
    """
    if seed is not None:
        set_seed(seed)
    
    logger.info(f"Generating synthetic rollout log: {num_samples} samples, {num_candidates} candidates, seed={seed}")
    
    log_entries = []
    
    # Define possible answer options based on task type
    if task_type == "vlm":
        # Simulating VLM tasks (e.g., image captioning or VQA)
        # We'll use generic text representations for the "image" context
        base_contexts = [
            "Describe the image content.",
            "What is happening in the scene?",
            "Identify the objects in the foreground.",
            "Explain the relationship between the entities.",
            "What is the emotional tone of the image?"
        ]
    else:
        # Standard LLM tasks (e.g., multiple choice)
        base_contexts = [
            "Which of the following is true?",
            "Select the correct option.",
            "Identify the best answer.",
            "Choose the most appropriate response.",
            "Determine the logical conclusion."
        ]
    
    for i in range(num_samples):
        context = base_contexts[i % len(base_contexts)]
        question_id = f"Q{i:04d}"
        
        # Generate ground truth (index 0-3)
        ground_truth_idx = random.randint(0, num_candidates - 1)
        
        for c_idx in range(num_candidates):
            # Generate a synthetic confidence score (0.0 to 1.0)
            # This is the INITIAL state, so it's just a random draw, not noise-injected yet
            confidence = random.random()
            
            # Generate synthetic negative candidate text
            candidate_text = f"Option {chr(65 + c_idx)}: Synthetic candidate {c_idx} for {question_id}"
            
            entry = {
                "question_id": question_id,
                "context": context,
                "candidate_idx": c_idx,
                "candidate_text": candidate_text,
                "ground_truth_idx": ground_truth_idx,
                "is_correct": (c_idx == ground_truth_idx),
                "confidence": round(confidence, 4),
                "task_type": task_type
            }
            
            log_entries.append(entry)
    
    logger.info(f"Generated {len(log_entries)} rollout log entries.")
    return log_entries


def generate_initial_state_for_store(
    state_store: StateStore,
    num_cycles: int = 1,
    num_samples: int = 10,
    seed: Optional[int] = None
) -> None:
    """
    Populate the StateStore with initial cycle data.
    
    This function sets up the initial state of the buffer by generating
    a single cycle of data (or a few cycles) to bootstrap the simulation.
    It uses the seeded random state to ensure determinism.
    
    Args:
        state_store: The StateStore instance to populate.
        num_cycles: Number of initial cycles to generate (default 1).
        num_samples: Number of samples per cycle.
        seed: Random seed for reproducibility.
    """
    if seed is not None:
        set_seed(seed)
        
    logger.info(f"Generating initial state for store: {num_cycles} cycles, {num_samples} samples/cycle")
    
    for cycle_idx in range(num_cycles):
        cycle_id = f"INIT_{cycle_idx:03d}"
        
        # Generate synthetic confidence history for this cycle
        # This represents the student's initial confidence on a set of items
        confidence_history = []
        prompt_lengths = []
        
        for _ in range(num_samples):
            # Initial confidence is random, no noise yet
            conf = random.random()
            confidence_history.append(round(conf, 4))
            # Simulate a prompt length (number of candidates in NCQ)
            # Initial state usually has full set
            prompt_lengths.append(random.randint(2, 4))
        
        record = CycleRecord(
            cycle_id=cycle_id,
            confidence_history=confidence_history,
            prompt_lengths=prompt_lengths,
            timestamp=None  # Will be set by StateStore if needed
        )
        
        state_store.add_cycle(record)
        
    logger.info(f"Added {num_cycles} initial cycles to state store.")


def set_seed(seed: int) -> None:
    """
    Set the global random seed for reproducibility.
    
    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    logger.debug(f"Global seed set to {seed}")

def get_seed(seed: Optional[int] = None) -> int:
    """
    Get the current seed or generate a new one if None.
    
    Args:
        seed: Optional seed value.
        
    Returns:
        The seed value to use.
    """
    if seed is None:
        seed = random.randint(0, 2**32 - 1)
    return seed

# Note: The actual per-step noise injection (FR-008) is handled in 
# code/loops/base_zppo.py and code/loops/cap_zppo.py as per task T027.
# This generator only handles the initial state setup with a seeded random state.