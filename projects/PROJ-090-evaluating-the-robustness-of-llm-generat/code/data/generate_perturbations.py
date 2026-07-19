import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datasets import load_dataset
from config import get_semantic_threshold, get_budget_generations, ensure_directories
from data.perturbations import generate_perturbation_variants
from data.semantic_validator import validate_perturbation_batch
from utils.logging import get_perturbation_logger, init_logging

POOL_FILE = "data/processed/perturbation_pool.json"
RESULTS_FILE = "data/processed/perturbation_results.json"

def load_humaneval_tasks() -> List[Dict[str, Any]]:
    """
    Loads the HumanEval dataset using the datasets library.
    Returns a list of task dictionaries.
    """
    logger = get_perturbation_logger()
    logger.info("Loading HumanEval dataset...")
    dataset = load_dataset("openai_humaneval", split="test")
    tasks = []
    for item in dataset:
        tasks.append({
            "task_id": item["task_id"],
            "prompt": item["prompt"],
            "canonical_solution": item["canonical_solution"],
            "test": item["test"]
        })
    logger.info(f"Loaded {len(tasks)} tasks.")
    return tasks

def generate_and_filter_perturbations(tasks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generates up to 3 perturbation variants per task, validates them,
    and filters based on the semantic threshold (> 0.95).
    
    Returns:
        Tuple of (valid_candidates, invalid_candidates)
    """
    logger = get_perturbation_logger()
    threshold = get_semantic_threshold()
    logger.info(f"Generating perturbations with threshold > {threshold}")
    
    all_candidates = []
    
    for task in tasks:
        task_id = task["task_id"]
        original_prompt = task["prompt"]
        
        # Generate up to 3 variants
        variants = generate_perturbation_variants(original_prompt, max_variants=3)
        
        for variant in variants:
            # Validate semantic similarity
            is_valid, score, reason = validate_perturbation(
                original_prompt, 
                variant["text"], 
                threshold
            )
            
            candidate = {
                "task_id": task_id,
                "perturbation_type": variant["type"],
                "original_text": original_prompt,
                "perturbed_text": variant["text"],
                "raw_score": score,
                "is_valid": is_valid,
                "reason": reason
            }
            all_candidates.append(candidate)
            
            if is_valid:
                logger.debug(f"Valid candidate: {task_id} ({variant['type']}) - {score}")
            else:
                logger.debug(f"Invalid candidate: {task_id} ({variant['type']}) - {score}")
    
    valid = [c for c in all_candidates if c["is_valid"]]
    invalid = [c for c in all_candidates if not c["is_valid"]]
    
    logger.info(f"Generation complete. Valid: {len(valid)}, Invalid: {len(invalid)}")
    return valid, all_candidates

def save_results(valid_candidates: List[Dict[str, Any]], output_path: str):
    """
    Saves the final filtered set of perturbed tasks to a JSON file.
    """
    ensure_directories()
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(valid_candidates, f, indent=2, ensure_ascii=False)
    logging.info(f"Saved {len(valid_candidates)} valid candidates to {output_path}")

def save_candidates_pool(all_candidates: List[Dict[str, Any]], output_path: str):
    """
    Saves ALL generated candidates (both valid and invalid) to the pool file.
    This is the input for T018 (log_perturbation_candidates).
    """
    ensure_directories()
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_candidates, f, indent=2, ensure_ascii=False)
    logging.info(f"Saved {len(all_candidates)} total candidates to {output_path}")

def main():
    """
    Main execution pipeline for T017.
    """
    init_logging()
    logger = get_perturbation_logger()
    logger.info("Starting T017: Perturbation Generation Pipeline")
    
    try:
        tasks = load_humaneval_tasks()
        valid, all_candidates = generate_and_filter_perturbations(tasks)
        
        # Save the final filtered results for inference
        save_results(valid, str(PROJECT_ROOT / RESULTS_FILE))
        
        # Save the full pool for logging (T018)
        save_candidates_pool(all_candidates, str(PROJECT_ROOT / POOL_FILE))
        
        logger.info("T017 Complete.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
