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
from data.semantic_validator import validate_perturbation
from utils.logging import get_perturbation_logger, init_logging

POOL_FILE = "data/processed/perturbation_candidates_raw.json"
RESULTS_FILE = "data/processed/perturbation_candidates.json"

def load_humaneval_tasks() -> List[Dict[str, Any]]:
    """
    Loads the HumanEval dataset using the datasets library.
    Returns a list of task dictionaries.
    """
    logger = get_perturbation_logger()
    logger.info("Loading HumanEval dataset...")
    # Real source: openai_humaneval from HuggingFace datasets
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
    Generates perturbation variants per task, validates them,
    and selects EXACTLY ONE valid variant per task (stopping immediately upon finding a candidate with score > 0.95).
    
    Logic:
    1. Iterate through transformation types (synonym, typo, rephrase).
    2. Generate a candidate.
    3. Validate semantic similarity.
    4. If valid (score > 0.95), log raw score, select it, and STOP for this task.
    5. If no valid variant is found after trying all types, log a warning and proceed with 0 perturbations for that task.
    
    Returns:
        Tuple of (selected_valid_candidates, all_generated_candidates_pool)
    """
    logger = get_perturbation_logger()
    threshold = get_semantic_threshold()
    logger.info(f"Generating perturbations with strict threshold > {threshold}. Stopping at first valid match.")
    
    selected_valid_candidates = []
    all_generated_candidates_pool = []
    
    for task in tasks:
        task_id = task["task_id"]
        original_prompt = task["prompt"]
        
        # We need to try types until we find a valid one.
        # generate_perturbation_variants returns a list of candidates.
        # We will iterate through the types explicitly to control the "first valid" logic if needed,
        # but the helper generates all 3. We will process the generated list and pick the first valid one.
        
        variants = generate_perturbation_variants(original_prompt, max_variants=3)
        
        task_found_valid = False
        
        for variant in variants:
            if task_found_valid:
                # We already found a valid one for this task, skip generating/validating more for budget
                # But we still log the attempt as invalid/excluded if we want full pool?
                # Task T017 says "stopping immediately upon finding a candidate".
                # So we stop processing variants for this task.
                break

            # Validate semantic similarity
            # validate_perturbation returns (is_valid, score, reason)
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
            all_generated_candidates_pool.append(candidate)
            
            if is_valid:
                logger.info(f"Selected valid candidate: {task_id} ({variant['type']}) - score: {score:.4f}")
                selected_valid_candidates.append(candidate)
                task_found_valid = True
            else:
                logger.debug(f"Invalid candidate: {task_id} ({variant['type']}) - score: {score:.4f}")
        
        if not task_found_valid:
            logger.warning(f"No valid perturbation found for task {task_id} after trying all types.")
    
    logger.info(f"Generation complete. Selected: {len(selected_valid_candidates)}, Total Pool: {len(all_generated_candidates_pool)}")
    return selected_valid_candidates, all_generated_candidates_pool

def save_results(valid_candidates: List[Dict[str, Any]], output_path: str):
    """
    Saves the final filtered set of perturbed tasks (exactly one per task) to a JSON file.
    """
    ensure_directories()
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(valid_candidates, f, indent=2, ensure_ascii=False)
    logging.info(f"Saved {len(valid_candidates)} valid candidates to {output_path}")

def save_candidates_pool(all_candidates: List[Dict[str, Any]], output_path: str):
    """
    Saves ALL generated candidates (both valid and invalid) to the raw pool file.
    This is the input for T018 (filter_perturbations).
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
    logger.info("Starting T017: Perturbation Generation Pipeline (One Valid Variant Per Task)")
    
    try:
        tasks = load_humaneval_tasks()
        valid, all_candidates = generate_and_filter_perturbations(tasks)
        
        # Save the final filtered results for inference (one per task)
        save_results(valid, str(PROJECT_ROOT / RESULTS_FILE))
        
        # Save the full raw pool for logging (T018)
        save_candidates_pool(all_candidates, str(PROJECT_ROOT / POOL_FILE))
        
        logger.info("T017 Complete.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()