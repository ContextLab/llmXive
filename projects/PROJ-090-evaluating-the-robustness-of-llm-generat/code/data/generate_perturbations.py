import json
import logging
import os
import random
import sys
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing API surface
from config import get_seed_global, get_budget_generations, ensure_directories
from data.perturbations import substitute_synonyms, inject_typos, rephrase_syntax
from utils.logging import get_perturbation_logger, init_logging

# Constants
BUDGET_CAP = 656
MAX_CANDIDATES_PER_TASK = 3
TRANSFORMATION_TYPES = ["rephrase", "synonym", "typo"]  # Sorted alphabetically for determinism

def setup_logging():
    """Initialize logging for the perturbation generation pipeline."""
    ensure_directories()
    logger = get_perturbation_logger()
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger

def load_humaneval_tasks() -> List[Dict[str, Any]]:
    """Load HumanEval tasks from the downloaded dataset."""
    data_path = Path("data/processed/humaneval_tasks.json")
    if not data_path.exists():
        raise FileNotFoundError(f"HumanEval dataset not found at {data_path}. Run T012 first.")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    
    return tasks

def generate_single_candidate(task: Dict[str, Any], perturbation_type: str, logger: logging.Logger) -> Dict[str, Any]:
    """
    Generate a single perturbed candidate for a given task and perturbation type.
    
    Args:
        task: The original HumanEval task dictionary.
        perturbation_type: One of 'synonym', 'typo', 'rephrase'.
        logger: Logger instance.
        
    Returns:
        A dictionary containing the candidate data with schema:
        {
            "task_id": str,
            "perturbation_type": str,
            "raw_score": float,
            "is_valid": bool,
            "candidate_text": str
        }
    Note:
        raw_score and is_valid are placeholders here as per T017 scope.
        T016 will compute the actual semantic similarity scores.
    """
    task_id = task["task_id"]
    original_prompt = task["prompt"]
    
    # Select the appropriate perturbation function
    if perturbation_type == "synonym":
        candidate_text = substitute_synonyms(original_prompt)
    elif perturbation_type == "typo":
        candidate_text = inject_typos(original_prompt)
    elif perturbation_type == "rephrase":
        candidate_text = rephrase_syntax(original_prompt)
    else:
        raise ValueError(f"Unknown perturbation type: {perturbation_type}")
    
    # T017 Requirement: Log raw score for EVERY candidate.
    # Since T016 (semantic validation) has not run yet, we set:
    # - raw_score: 0.0 (placeholder, to be updated by T016)
    # - is_valid: False (placeholder, to be updated by T016)
    # This ensures the schema is complete and T016 can update these fields.
    candidate = {
        "task_id": task_id,
        "perturbation_type": perturbation_type,
        "raw_score": 0.0,  # Placeholder for T016
        "is_valid": False, # Placeholder for T016
        "candidate_text": candidate_text
    }
    
    logger.info(f"Generated candidate for task {task_id} (type: {perturbation_type})")
    return candidate

def generate_and_filter_perturbations(tasks: List[Dict[str, Any]], logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Generate up to 3 candidates per task (one per transformation type).
    Enforce the global budget cap of 656.
    
    Logic:
    1. Sort tasks by task_id ascending for deterministic ordering.
    2. Iterate through transformation types (alphabetically: rephrase, synonym, typo).
    3. Generate candidate.
    4. Add to pool if under budget.
    5. Stop when budget is reached.
    
    Returns:
        List of candidate dictionaries.
    """
    random.seed(get_seed_global())
    
    # Sort tasks by task_id for deterministic processing
    sorted_tasks = sorted(tasks, key=lambda x: x["task_id"])
    
    candidates_pool = []
    budget_remaining = BUDGET_CAP
    
    # Iterate through transformation types
    for pert_type in TRANSFORMATION_TYPES:
        if budget_remaining <= 0:
            logger.warning(f"Budget cap ({BUDGET_CAP}) reached. Stopping generation.")
            break
        
        for task in sorted_tasks:
            if budget_remaining <= 0:
                break
            
            try:
                candidate = generate_single_candidate(task, pert_type, logger)
                candidates_pool.append(candidate)
                budget_remaining -= 1
            except Exception as e:
                logger.error(f"Error generating candidate for task {task['task_id']} type {pert_type}: {e}")
                # Continue to next task even if one fails
                continue
    
    logger.info(f"Generation complete. Total candidates: {len(candidates_pool)}")
    return candidates_pool

def save_candidates_pool(candidates: List[Dict[str, Any]], logger: logging.Logger):
    """
    Save the full unfiltered list of candidates to data/processed/perturbation_candidates_raw.json.
    
    Schema:
    [
      {
        "task_id": str,
        "perturbation_type": str,
        "raw_score": float,
        "is_valid": bool,
        "candidate_text": str
      },
      ...
    ]
    """
    output_path = Path("data/processed/perturbation_candidates_raw.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(candidates, f, indent=2)
    
    logger.info(f"Saved {len(candidates)} candidates to {output_path}")
    
    # Verification: Check that no task has more than 3 candidates
    counts = Counter(c["task_id"] for c in candidates)
    max_count = max(counts.values()) if counts else 0
    logger.info(f"Max candidates per task: {max_count}")
    if max_count > MAX_CANDIDATES_PER_TASK:
        logger.warning(f"Verification failed: Some tasks have more than {MAX_CANDIDATES_PER_TASK} candidates.")
    else:
        logger.info("Verification passed: All tasks have <= 3 candidates.")

def main():
    """Main entry point for T017."""
    logger = setup_logging()
    logger.info("Starting perturbation generation pipeline (T017)...")
    
    try:
        tasks = load_humaneval_tasks()
        logger.info(f"Loaded {len(tasks)} HumanEval tasks.")
        
        candidates = generate_and_filter_perturbations(tasks, logger)
        
        save_candidates_pool(candidates, logger)
        
        logger.info("T017 completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
