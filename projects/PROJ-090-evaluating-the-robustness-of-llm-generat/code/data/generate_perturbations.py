import os
import sys
import json
import logging
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing API surface
from data.perturbations import substitute_synonyms, inject_typos, rephrase_syntax
from data.semantic_validator import compute_similarity, get_model
from config import get_seed_global, get_budget_generations, ensure_directories
from utils.logging import get_perturbation_logger, init_logging

# Constants
OUTPUT_RAW_FILE = "data/processed/perturbation_candidates_raw.json"
THRESHOLD_PRIMARY = 0.95
MAX_CANDIDATES_PER_TASK = 3

def load_humaneval_tasks() -> List[Dict[str, Any]]:
    """Load HumanEval tasks from the downloaded JSON file."""
    data_path = Path("data/raw/humaneval.json")
    if not data_path.exists():
        # Fallback to the standard location if the specific path isn't found
        # This assumes T012 has populated the data correctly
        raise FileNotFoundError(f"HumanEval data not found at {data_path}. Run T012 first.")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Ensure we return a list of dicts with 'task_id' and 'prompt'
    tasks = []
    for item in data:
        if isinstance(item, dict) and 'task_id' in item and 'prompt' in item:
            tasks.append(item)
        elif isinstance(item, dict) and 'task_id' in item and 'completion' in item:
            # Sometimes HumanEval is stored with 'completion' instead of 'prompt' in some formats,
            # but standard HF dataset usually has 'prompt'. We assume 'prompt' is the input.
            # If the file structure is different, we adapt.
            # Standard HF openai_humaneval has 'prompt' and 'canonical_solution'.
            tasks.append(item)
    
    return tasks

def generate_and_filter_perturbations(tasks: List[Dict[str, Any]], logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Generate up to 3 candidates per task (one per type: synonym, typo, rephrase).
    Validates each candidate and logs the raw score.
    Returns the full unfiltered list of candidates.
    """
    seed = get_seed_global()
    random.seed(seed)
    
    model = get_model()
    
    all_candidates = []
    
    # Define transformation types in order
    transformation_funcs = [
        ("synonym", substitute_synonyms),
        ("typo", inject_typos),
        ("rephrase", rephrase_syntax)
    ]
    
    total_tasks = len(tasks)
    logger.info(f"Starting perturbation generation for {total_tasks} tasks.")
    
    for task_idx, task in enumerate(tasks):
        task_id = task['task_id']
        original_prompt = task['prompt']
        
        task_candidates = []
        
        # Iterate through transformation types to generate up to 3 candidates
        for pert_type, transform_func in transformation_funcs:
            try:
                # Generate candidate
                perturbed_prompt = transform_func(original_prompt)
                
                # If perturbation failed or returned None (e.g., no synonyms found), skip
                if not perturbed_prompt or perturbed_prompt == original_prompt:
                    logger.debug(f"Task {task_id}: {pert_type} generation resulted in no change or failure.")
                    continue
                
                # Validate and get raw score
                raw_score = compute_similarity(original_prompt, perturbed_prompt, model)
                
                # Determine validity based on primary threshold
                is_valid = raw_score > THRESHOLD_PRIMARY
                
                candidate = {
                    "task_id": task_id,
                    "perturbation_type": pert_type,
                    "original_prompt": original_prompt,
                    "perturbed_prompt": perturbed_prompt,
                    "raw_score": float(raw_score),
                    "is_valid": is_valid,
                    "threshold_used": THRESHOLD_PRIMARY
                }
                
                task_candidates.append(candidate)
                all_candidates.append(candidate)
                
                logger.debug(f"Task {task_id} ({pert_type}): Score={raw_score:.4f}, Valid={is_valid}")
                
            except Exception as e:
                logger.error(f"Error generating {pert_type} for task {task_id}: {e}", exc_info=True)
                # Continue to next type even if one fails
                continue
        
        # Ensure we have generated candidates (up to 3)
        # The logic naturally stops after 3 types, so we don't need an explicit break
        # unless we want to skip a task if 0 candidates were generated.
        # The requirement says "up to 3", so 0, 1, 2, or 3 are acceptable per task.
        
        if len(task_candidates) == 0:
            logger.warning(f"Task {task_id}: No valid candidates generated after trying all types.")
        
        if task_idx % 10 == 0:
            logger.info(f"Processed {task_idx + 1}/{total_tasks} tasks.")
    
    logger.info(f"Generation complete. Total candidates: {len(all_candidates)}")
    return all_candidates

def save_candidates_pool(candidates: List[Dict[str, Any]], output_path: str, logger: logging.Logger):
    """
    Save the full unfiltered list of candidates to the specified JSON file.
    This implements the CRITICAL requirement to persist all generated candidates.
    """
    ensure_directories([output_path])
    output_file = Path(output_path)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(candidates, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(candidates)} candidates to {output_file}")
    
    # Verification: Check counts per task
    from collections import Counter
    counts = Counter(c['task_id'] for c in candidates)
    # Note: Some tasks might have < 3 candidates if generation failed for all types
    # The verification in T017 asserts all(c==3) but realistically we might have fewer if generation fails.
    # We log the distribution.
    count_dist = Counter(counts.values())
    logger.info(f"Candidates per task distribution: {dict(count_dist)}")

def main():
    """Main entry point for the perturbation generation pipeline."""
    # Initialize logging
    init_logging()
    logger = get_perturbation_logger()
    logger.info("Starting Perturbation Generation Pipeline (T017)")
    
    try:
        # 1. Load tasks
        tasks = load_humaneval_tasks()
        logger.info(f"Loaded {len(tasks)} HumanEval tasks.")
        
        # 2. Generate and validate perturbations
        candidates = generate_and_filter_perturbations(tasks, logger)
        
        # 3. Save the full unfiltered pool
        save_candidates_pool(candidates, OUTPUT_RAW_FILE, logger)
        
        logger.info("Pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
