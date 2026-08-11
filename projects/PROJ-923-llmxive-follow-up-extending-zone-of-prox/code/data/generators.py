"""
Synthetic Rollout Log Generator for ZPPO Simulation.

Implements explicit learning dynamics for student confidence updates based on
'expert gap' and 'prompt length' variables as defined in Plan Step 1.

Formula:
new_conf = current_conf + alpha * (expert_conf - current_conf) * (1 - prompt_length_factor)

This module generates a realistic synthetic rollout log for the baseline simulation.
It simulates a student learning process over multiple cycles, interacting with
a set of tasks (MMLU subjects).
"""
import os
import json
import random
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from utils.logging import get_logger
from utils.seeds import get_rng, set_global_seed
from config import get_config

logger = get_logger(__name__)

# Default hyperparameters for the simulation dynamics
DEFAULT_ALPHA = 0.15  # Learning rate
DEFAULT_INITIAL_CONF = 0.45  # Starting confidence
DEFAULT_EXPERT_CONF = 0.95  # Expert target confidence
NOISE_SIGMA = 0.02  # Small intrinsic noise in the simulation

def set_seed(seed: int) -> None:
    """
    Sets the global seed for reproducibility.
    DEPRECATED in favor of utils.seeds.set_global_seed, but kept for API compatibility.
    """
    set_global_seed(seed)

def get_seed() -> Optional[int]:
    """
    Returns the current global seed.
    DEPRECATED in favor of utils.seeds.get_global_seed, but kept for API compatibility.
    """
    from utils.seeds import get_global_seed
    return get_global_seed()

def generate_synthetic_rollout_log(
    seed: int,
    num_tasks: int = 10,
    num_cycles: int = 20,
    num_candidates: int = 5,
    output_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Generates a synthetic rollout log simulating the student's learning dynamics.

    This function implements the core learning formula:
    new_conf = current_conf + alpha * (expert_conf - current_conf) * (1 - prompt_length_factor)

    Where:
    - alpha: Learning rate (how fast the student learns)
    - expert_conf: The confidence of the expert (target)
    - prompt_length_factor: A factor derived from the number of negative candidates in the prompt.
                            More candidates -> higher factor -> slower learning (cognitive load).

    Args:
        seed: Random seed for reproducibility.
        num_tasks: Number of distinct tasks (MMLU subjects) to simulate.
        num_cycles: Number of training cycles to simulate.
        num_candidates: Number of negative candidates to generate per task per cycle.
        output_path: Optional path to save the generated log as JSON.

    Returns:
        A list of dictionaries representing the rollout log entries.
    """
    rng = get_rng(seed)
    config = get_config()

    # Determine task names (simulating MMLU subjects)
    # We use a fixed list of common MMLU subjects for determinism
    all_subjects = [
        "abstract_algebra", "anatomy", "astronomy", "business_ethics", "clinical_knowledge",
        "college_biology", "college_chemistry", "college_computer_science", "college_mathematics",
        "college_medicine", "college_physics", "computer_security", "conceptual_physics",
        "econometrics", "electrical_engineering", "elementary_mathematics", "formal_logic",
        "global_facts", "high_school_biology", "high_school_chemistry", "high_school_computer_science",
        "high_school_european_history", "high_school_geography", "high_school_government_and_politics",
        "high_school_macroeconomics", "high_school_mathematics", "high_school_microeconomics",
        "high_school_physics", "high_school_psychology", "high_school_statistics",
        "high_school_us_history", "high_school_world_history", "human_aging", "human_sexuality",
        "international_law", "jurisprudence", "logical_fallacies", "machine_learning",
        "management", "marketing", "medical_genetics", "miscellaneous", "moral_disputes",
        "moral_scenarios", "nutrition", "philosophy", "prehistory", "professional_accounting",
        "professional_law", "professional_medicine", "professional_psychology", "public_relations",
        "security_studies", "sociology", "us_foreign_policy", "virology", "world_religions"
    ]

    # Select tasks deterministically based on seed if we need fewer than total
    selected_tasks = all_subjects[:num_tasks]
    if num_tasks > len(all_subjects):
        logger.warning(f"Requested {num_tasks} tasks, but only {len(all_subjects)} available. Using all.")
        selected_tasks = all_subjects

    log_entries = []
    
    # Initialize student state per task
    # Each task starts with a slightly different initial confidence to simulate variance
    task_states = {}
    for task in selected_tasks:
        task_states[task] = {
            "current_conf": rng.uniform(0.3, 0.6), # Initial confidence varies
            "correct_count": 0,
            "total_count": 0
        }

    for cycle in range(num_cycles):
        # Calculate prompt length factor for this cycle
        # In the baseline (Static ZPPO), the prompt length is constant (all candidates)
        # We simulate a "cognitive load" factor. 
        # Factor = 1 / (1 + k * num_candidates). More candidates = higher load = lower factor in (1-factor).
        # Actually, the formula uses (1 - prompt_length_factor).
        # Let's define prompt_length_factor = num_candidates / (num_candidates + 10). 
        # If candidates=0, factor=0 -> (1-0)=1 (max learning).
        # If candidates=10, factor=0.5 -> (1-0.5)=0.5 (half learning speed).
        # If candidates=50, factor=0.83 -> (1-0.83)=0.17 (slow learning).
        prompt_length_factor = num_candidates / (num_candidates + 10.0)

        for task in selected_tasks:
            state = task_states[task]
            
            # 1. Generate Ground Truth and Student Response
            # Simulate a correct/incorrect outcome based on current confidence
            is_correct = rng.random() < state["current_conf"]
            
            # Generate a synthetic "expert" confidence for this specific instance
            # In a real scenario, this might vary, but we use a high baseline for experts
            expert_conf = DEFAULT_EXPERT_CONF + rng.normal(0, 0.02)
            expert_conf = np.clip(expert_conf, 0.0, 1.0)

            # 2. Calculate New Confidence (Learning Dynamics)
            # Formula: new_conf = current_conf + alpha * (expert_conf - current_conf) * (1 - prompt_length_factor)
            alpha = DEFAULT_ALPHA
            learning_gain = alpha * (expert_conf - state["current_conf"]) * (1 - prompt_length_factor)
            
            # Add small intrinsic noise to the update
            learning_gain += rng.normal(0, NOISE_SIGMA)
            
            new_conf = state["current_conf"] + learning_gain
            new_conf = np.clip(new_conf, 0.0, 1.0)

            # 3. Generate Negative Candidates
            # In the baseline, we always have the full set of candidates
            candidates = []
            for i in range(num_candidates):
                # Generate a random confidence for a negative candidate
                # These are typically lower confidence or "distractors"
                cand_conf = rng.uniform(0.05, 0.45) 
                candidates.append({
                    "candidate_id": f"{task}_cand_{i}",
                    "confidence": round(cand_conf, 4),
                    "is_negative": True
                })

            # 4. Construct Log Entry
            entry = {
                "cycle": cycle,
                "task_id": task,
                "student_confidence": round(state["current_conf"], 4),
                "expert_confidence": round(expert_conf, 4),
                "prompt_length_factor": round(prompt_length_factor, 4),
                "num_candidates": num_candidates,
                "is_correct": is_correct,
                "ground_truth": "correct" if is_correct else "incorrect",
                "new_confidence": round(new_conf, 4),
                "negative_candidates": candidates
            }

            log_entries.append(entry)

            # Update state for next cycle
            state["current_conf"] = new_conf
            state["total_count"] += 1
            if is_correct:
                state["correct_count"] += 1

    # Save to file if path provided
    if output_path:
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(log_entries, f, indent=2)
        logger.info(f"Synthetic rollout log saved to {output_path}")

    return log_entries

def generate_initial_state_for_store(
    seed: int,
    tasks: List[str],
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates the initial state for the State Store (T009).
    This provides the baseline historical confidence data before the simulation starts.
    """
    rng = get_rng(seed)
    initial_state = {
        "timestamp": "2023-01-01T00:00:00Z",
        "seeds": {"initial": seed},
        "tasks": {}
    }

    for task in tasks:
        initial_state["tasks"][task] = {
            "history": [],
            "current_conf": round(rng.uniform(0.3, 0.6), 4),
            "stats": {
                "mean_conf": 0.0,
                "var_conf": 0.0,
                "count": 0
            }
        }

    if output_path:
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(initial_state, f, indent=2)
        logger.info(f"Initial state saved to {output_path}")

    return initial_state