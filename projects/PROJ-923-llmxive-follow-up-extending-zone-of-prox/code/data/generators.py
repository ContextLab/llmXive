import os
import json
import random
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from utils.logging import get_logger, info
from utils.seeds import get_rng
from config import get_config

_seed: Optional[int] = None

def set_seed(seed: int):
    global _seed
    _seed = seed
    random.seed(seed)
    np.random.seed(seed)

def get_seed() -> Optional[int]:
    return _seed

def generate_synthetic_rollout_log(task_id: str, num_cycles: int, seed: int) -> List[Dict[str, Any]]:
    """
    Generates a synthetic rollout log with explicit learning dynamics.
    
    Implements the formula specified in T012:
    new_conf = current_conf + alpha * (expert_conf - current_conf) * (- prompt_length_factor)
    
    However, based on the context of 'learning' (improvement), the task description 
    implies a positive update direction derived from the 'expert gap'. The formula 
    provided in the prompt `(- prompt_length_factor)` would mathematically decrease 
    confidence if expert_conf > current_conf (which is the learning scenario). 
    
    Re-reading T012: "Formula: `new_conf = current_conf + alpha * (expert_conf - current_conf) * (- prompt_length_factor)`"
    And T015: "Formula: `new_conf = current_conf + alpha * (expert_conf - current_conf) * (1 - prompt_length_factor)`"
    
    There is a contradiction between T012 and T015 in the provided text. 
    T012 says `(- prompt_length_factor)`. T015 says `(1 - prompt_length_factor)`.
    Given that T012 is the specific task I am implementing, and T015 is a dependent task,
    I will strictly follow T012's explicit formula, but I must ensure the logic makes sense 
    for a "learning" simulation (confidence should generally rise towards expert).
    
    If `prompt_length_factor` is positive (1/pool_size), then `(- prompt_length_factor)` is negative.
    If `expert_conf > current_conf`, the term `(expert_conf - current_conf)` is positive.
    Positive * Negative = Negative. This would reduce confidence. This contradicts "learning".
    
    Let's re-read T012 carefully: "student confidence updates based on 'expert gap' and 'prompt length' variables".
    Maybe the formula in T012 implies a specific dynamic where longer prompts hinder learning?
    Or perhaps the formula in the prompt text has a typo and meant `(1 - prompt_length_factor)` as in T015?
    
    However, T012 is the task at hand. T015 depends on T012. If I implement T012 with a formula that 
    makes confidence drop, T015 might fail or the simulation will be broken.
    
    Let's look at the T012 description again: "Formula: `new_conf = current_conf + alpha * (expert_conf - current_conf) * (- prompt_length_factor)`".
    Wait, maybe `prompt_length_factor` is defined differently? T012 says: "`prompt_length_factor` = `1 / config.initial_candidate_pool_size`".
    
    Let's assume the formula in T012 is the absolute truth for this task, even if it seems counter-intuitive for "learning" 
    (perhaps it simulates a specific failure mode or a specific ZPPO variant where prompt length penalizes learning rate).
    BUT, T015 says: "MUST implement confidence update logic using the formula from T012." and then lists `(1 - prompt_length_factor)`.
    This is a direct contradiction in the prompt text between T012 and T015 descriptions.
    
    Given T015 is a dependent task that *uses* the logic, and T015 explicitly writes `(1 - prompt_length_factor)` 
    while calling it "the formula from T012", it is highly likely the T012 text `(- prompt_length_factor)` was a typo 
    for `(1 - prompt_length_factor)` or the user meant `1 - prompt_length_factor`.
    
    However, as an implementer, I must follow the task description. If I strictly follow T012's `(- factor)`, 
    the student confidence will decrease if they are below the expert. This seems wrong for a "learning" simulation.
    
    Let's look at the T012 text again: "Formula: `new_conf = current_conf + alpha * (expert_conf - current_conf) * (- prompt_length_factor)`".
    Maybe the `prompt_length_factor` is actually `1 - (1/pool)`? No, it says `1 / config.initial_candidate_pool_size`.
    
    Decision: I will implement the logic as described in T015's reference to T012, which is `(1 - prompt_length_factor)`, 
    because that creates a valid learning dynamic (positive update) and T015 explicitly references it as "the formula from T012".
    The `(- prompt_length_factor)` in T012 is likely a typo for `(1 - prompt_length_factor)` or the user intended the 
    factor to be subtracted from 1. Using `(1 - prompt_length_factor)` ensures that as pool size increases, the learning 
    rate decreases, which makes sense.
    
    Wait, I should check if `prompt_length_factor` is meant to be a penalty. 
    If I use `(- prompt_length_factor)`, the update is negative.
    If I use `(1 - prompt_length_factor)`, the update is positive but scaled.
    
    I will use `(1 - prompt_length_factor)` to ensure the simulation produces a "learning curve" (increasing confidence) 
    as expected for a ZPPO baseline. This aligns with T015's explicit formula.
    """
    rng = get_rng(seed)
    config = get_config()
    alpha = config.alpha
    initial_pool = config.initial_candidate_pool_size
    prompt_length_factor = 1 / initial_pool

    log = []
    current_conf = 0.5 # Start with neutral confidence
    expert_conf = 0.95 # Expert is highly confident

    for cycle in range(num_cycles):
        # Calculate the learning delta based on the expert gap and prompt length factor.
        # Using (1 - prompt_length_factor) as per T015's clarification of T012's formula to ensure positive learning.
        # If T012's `(- factor)` was literal, learning would be negative. Assuming T015's version is the intended logic.
        learning_rate = 1 - prompt_length_factor
        delta = alpha * (expert_conf - current_conf) * learning_rate
        
        current_conf += delta
        current_conf = float(np.clip(current_conf, 0.0, 1.0))

        # Add noise for realism as per T026 (though T026 is called in the loop, we add a small amount here 
        # to simulate the state before the loop's noise injection if needed, or just for realism in the log).
        # Note: T026 injects noise in the loop. This generator creates the "ground truth" or "expected" dynamics.
        # We add a small noise here to make the log look realistic, but the main noise injection happens in the loop.
        # The task says "Includes LLM/VLM tasks, confidence scores, ground truth".
        # We will add a small noise to the recorded confidence to simulate the 'observed' value, 
        # but the 'expert' and 'true' dynamics are the base.
        noisy_conf = float(rng.normal(current_conf, 0.02))
        noisy_conf = float(np.clip(noisy_conf, 0.0, 1.0))

        # Determine correctness based on the noisy confidence (probabilistic)
        correct = bool(rng.random() < noisy_conf)

        record = {
            "task_id": task_id,
            "cycle": cycle,
            "student_confidence": noisy_conf,
            "expert_confidence": expert_conf,
            "prompt_length": initial_pool, # Static for baseline
            "correct": correct
        }
        log.append(record)

        # Slight decay in expert confidence to simulate a moving target or difficulty increase, 
        # ensuring the student doesn't reach 1.0 too easily.
        expert_conf = max(0.9, expert_conf - 0.001) 

    return log

def generate_initial_state_for_store(project_id: str) -> Dict[str, Any]:
    """Generates initial state for the state store."""
    return {
        "project_id": project_id,
        "history": []
    }