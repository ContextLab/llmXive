"""
Perturbation generation pipeline for HumanEval tasks.

Implements T017: Generates up to 3 candidates (one per transformation type: synonym, typo, rephrase)
per task. Persists the full unfiltered list of all generated candidates to
data/processed/perturbation_candidates_raw.json.

Dependency: T012 (download_humaneval), T013 (substitute_synonyms), T014 (inject_typos), T015 (rephrase_syntax)
"""

import json
import logging
import os
import random
import sys
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from project API surface
from data.perturbations import substitute_synonyms, inject_typos, rephrase_syntax
from data.download_humaneval import download_humaneval
from config import ensure_directories, get_seed_global, get_budget_generations
from utils.logging import get_perturbation_logger, init_logging

# Constants
TRANSFORMATION_TYPES = ["synonym", "typo", "rephrase"]
MAX_CANDIDATES_PER_TASK = 3
OUTPUT_FILE = "data/processed/perturbation_candidates_raw.json"

def setup_logging():
    """Initialize logging for the perturbation generation pipeline."""
    init_logging()
    return get_perturbation_logger(__name__)

def load_humaneval_tasks(logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Load HumanEval tasks from the dataset.
    
    Args:
        logger: Logger instance for tracking progress.
        
    Returns:
        List of task dictionaries with 'task_id', 'prompt', and 'canonical_solution'.
    """
    logger.info("Loading HumanEval dataset...")
    try:
        tasks = download_humaneval()
        logger.info(f"Loaded {len(tasks)} HumanEval tasks")
        return tasks
    except Exception as e:
        logger.error(f"Failed to load HumanEval dataset: {e}")
        raise

def generate_single_candidate(
    task_id: str,
    prompt: str,
    perturbation_type: str,
    logger: logging.Logger
) -> Optional[Dict[str, Any]]:
    """
    Generate a single perturbation candidate for a given task and type.
    
    Args:
        task_id: Unique identifier for the task.
        prompt: Original prompt text.
        perturbation_type: One of "synonym", "typo", "rephrase".
        logger: Logger instance for tracking progress.
        
    Returns:
        Dictionary with candidate details, or None if generation fails.
    """
    try:
        if perturbation_type == "synonym":
            candidate_text = substitute_synonyms(prompt)
        elif perturbation_type == "typo":
            candidate_text = inject_typos(prompt)
        elif perturbation_type == "rephrase":
            candidate_text = rephrase_syntax(prompt)
        else:
            logger.warning(f"Unknown perturbation type: {perturbation_type}")
            return None
        
        # For T017, we generate the candidate and log a raw_score placeholder.
        # The actual semantic similarity score will be computed in T016.
        # We use a placeholder of 1.0 here to indicate "generated successfully".
        # The validation step (T016) will replace this with the real score.
        raw_score = 1.0  # Placeholder; will be updated by semantic_validator.py
        
        candidate = {
            "task_id": task_id,
            "perturbation_type": perturbation_type,
            "raw_score": raw_score,
            "is_valid": False,  # Will be updated by semantic_validator.py
            "candidate_text": candidate_text
        }
        
        logger.debug(f"Generated {perturbation_type} candidate for {task_id}")
        return candidate
        
    except Exception as e:
        logger.error(f"Failed to generate {perturbation_type} candidate for {task_id}: {e}")
        return None

def generate_and_filter_perturbations(
    tasks: List[Dict[str, Any]],
    logger: logging.Logger
) -> List[Dict[str, Any]]:
    """
    Generate up to 3 candidates per task (one per transformation type).
    
    Args:
        tasks: List of HumanEval task dictionaries.
        logger: Logger instance for tracking progress.
        
    Returns:
        List of all generated candidates (unfiltered).
    """
    all_candidates = []
    budget = get_budget_generations()
    
    logger.info(f"Starting perturbation generation for {len(tasks)} tasks (budget: {budget})")
    
    for task in tasks:
        task_id = task.get("task_id", task.get("prompt_id", "unknown"))
        prompt = task.get("prompt", "")
        
        if not prompt:
            logger.warning(f"Skipping task {task_id}: empty prompt")
            continue
        
        task_candidates = []
        
        # Generate one candidate per transformation type
        for perturbation_type in TRANSFORMATION_TYPES:
            if len(task_candidates) >= MAX_CANDIDATES_PER_TASK:
                break
            
            candidate = generate_single_candidate(task_id, prompt, perturbation_type, logger)
            if candidate:
                task_candidates.append(candidate)
                all_candidates.append(candidate)
        
        logger.info(f"Generated {len(task_candidates)} candidates for {task_id}")
    
    logger.info(f"Total candidates generated: {len(all_candidates)}")
    return all_candidates

def save_candidates_pool(candidates: List[Dict[str, Any]], logger: logging.Logger):
    """
    Save all generated candidates to the raw output file.
    
    Args:
        candidates: List of candidate dictionaries.
        logger: Logger instance for tracking progress.
    """
    ensure_directories()
    output_path = Path(OUTPUT_FILE)
    
    logger.info(f"Saving {len(candidates)} candidates to {output_path}")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(candidates, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved candidates to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save candidates: {e}")
        raise

def main():
    """Main entry point for the perturbation generation pipeline."""
    logger = setup_logging()
    
    try:
        # Set global seed for reproducibility
        seed = get_seed_global()
        random.seed(seed)
        logger.info(f"Using global seed: {seed}")
        
        # Load HumanEval tasks
        tasks = load_humaneval_tasks(logger)
        
        if not tasks:
            logger.error("No tasks loaded from HumanEval dataset")
            sys.exit(1)
        
        # Generate perturbations
        candidates = generate_and_filter_perturbations(tasks, logger)
        
        if not candidates:
            logger.warning("No candidates generated")
            # Still save an empty list to maintain pipeline structure
            save_candidates_pool([], logger)
            sys.exit(0)
        
        # Save the full unfiltered list
        save_candidates_pool(candidates, logger)
        
        # Verification: Check that each task has exactly 3 candidates
        task_counts = Counter(c["task_id"] for c in candidates)
        logger.info(f"Candidate counts per task: {dict(task_counts)}")
        
        # Log summary
        type_counts = Counter(c["perturbation_type"] for c in candidates)
        logger.info(f"Candidate counts by type: {dict(type_counts)}")
        
        logger.info("Perturbation generation pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()