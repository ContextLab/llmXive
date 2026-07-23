"""
Perturbation Generation Pipeline (T017).

Generates exactly one valid variant per HumanEval task.
Logic: Iterate through transformation types (synonym, typo, rephrase);
generate candidate; validate semantic similarity (> 0.95);
if valid, log raw score and select immediately; stop.
If no valid variant found after all types, log warning and proceed with 0.
"""
import os
import sys
import json
import logging
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Project root import handling
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from datasets import load_dataset
from data.perturbations import substitute_synonyms, inject_typos, rephrase_syntax
from data.semantic_validator import validate_perturbation, get_model
from utils.logging import get_perturbation_logger, init_logging
from config import ensure_directories, get_config_dict, get_seed_global

# Constants
SEMANTIC_THRESHOLD = 0.95
OUTPUT_RAW_FILE = "data/processed/perturbation_candidates_raw.json"
OUTPUT_POOL_FILE = "data/processed/perturbation_candidates_pool.json"
TRANSFORMATION_TYPES = ["synonym", "typo", "rephrase"]

def load_humaneval_tasks() -> List[Dict[str, Any]]:
    """Load HumanEval dataset using the datasets library."""
    logger = get_perturbation_logger()
    logger.info("Loading HumanEval dataset...")
    try:
        dataset = load_dataset("openai_humaneval", split="test")
        tasks = list(dataset)
        logger.info(f"Loaded {len(tasks)} tasks from HumanEval.")
        return tasks
    except Exception as e:
        logger.error(f"Failed to load HumanEval dataset: {e}")
        raise

def generate_and_filter_perturbations(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate exactly one valid variant per task.
    Stops immediately upon finding a candidate with score > 0.95.
    """
    logger = get_perturbation_logger()
    config = get_config_dict()
    seed = config.get("seed_global", 42)
    random.seed(seed)

    # Ensure model is loaded once
    try:
        model = get_model()
    except Exception as e:
        logger.error(f"Failed to load semantic validation model: {e}")
        raise

    results = []
    total_tasks = len(tasks)
    valid_count = 0
    invalid_count = 0

    for idx, task in enumerate(tasks):
        task_id = task.get("task_id", f"task_{idx}")
        prompt = task.get("prompt", "")
        entry_point = task.get("entry_point", "")
        canonical_solution = task.get("canonical_solution", "")

        if not prompt:
            logger.warning(f"Task {task_id} has no prompt, skipping.")
            continue

        selected_variant = None
        raw_score_log = []

        # Iterate through transformation types
        for trans_type in TRANSFORMATION_TYPES:
            if selected_variant:
                break  # Stop if we already found a valid one

            logger.debug(f"Trying {trans_type} for task {task_id}...")

            try:
                if trans_type == "synonym":
                    candidate = substitute_synonyms(prompt)
                elif trans_type == "typo":
                    candidate = inject_typos(prompt)
                elif trans_type == "rephrase":
                    candidate = rephrase_syntax(prompt)
                else:
                    continue

                if not candidate or candidate == prompt:
                    continue

                # Validate semantic similarity
                is_valid, score = validate_perturbation(prompt, candidate, model)
                
                # Log raw score regardless of validity
                raw_score_log.append({
                    "type": trans_type,
                    "score": float(score),
                    "valid": is_valid
                })

                if is_valid:
                    selected_variant = {
                        "task_id": task_id,
                        "original_prompt": prompt,
                        "perturbed_prompt": candidate,
                        "perturbation_type": trans_type,
                        "raw_score": float(score),
                        "is_valid": True,
                        "entry_point": entry_point,
                        "canonical_solution": canonical_solution
                    }
                    logger.info(f"Task {task_id}: Found valid {trans_type} variant (score={score:.4f}). Stopping.")
                    break
                else:
                    logger.debug(f"Task {task_id}: {trans_type} failed validation (score={score:.4f}).")

            except Exception as e:
                logger.warning(f"Task {task_id}: Error generating/validating {trans_type}: {e}")
                continue

        if selected_variant:
            valid_count += 1
            results.append(selected_variant)
        else:
            invalid_count += 1
            logger.warning(f"Task {task_id}: No valid variant found after trying all types. Skipping.")

    logger.info(f"Generation complete: {valid_count} valid, {invalid_count} invalid out of {total_tasks} tasks.")
    return results

def save_results(results: List[Dict[str, Any]], output_path: str):
    """Save the final list of selected perturbations to a JSON file."""
    ensure_directories()
    path = Path(output_path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logging.getLogger().info(f"Saved {len(results)} results to {output_path}")

def save_candidates_pool(tasks: List[Dict[str, Any]], raw_logs: List[Dict[str, Any]]):
    """
    Save the raw log of all attempted candidates (including failed ones) 
    to satisfy the verification requirement for the raw JSON file.
    """
    ensure_directories()
    path = Path(OUTPUT_RAW_FILE)
    
    # Structure: List of objects, each containing task info and all attempted logs
    pool_data = []
    for task in tasks:
        task_id = task.get("task_id", "unknown")
        # Find logs for this task
        task_logs = [l for l in raw_logs if l.get("task_id") == task_id]
        if task_logs or True: # Include even if no logs, to track coverage
            pool_data.append({
                "task_id": task_id,
                "original_prompt": task.get("prompt", ""),
                "attempts": task_logs
            })
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pool_data, f, indent=2, ensure_ascii=False)
    logging.getLogger().info(f"Saved raw candidate pool to {OUTPUT_RAW_FILE}")

def main():
    """Main entry point for the perturbation generation pipeline."""
    init_logging()
    logger = get_perturbation_logger()
    logger.info("Starting Perturbation Generation Pipeline (T017)")

    try:
        # 1. Load Data
        tasks = load_humaneval_tasks()

        # 2. Generate and Filter (One per task)
        # We need to collect raw logs for the verification file
        # Since generate_and_filter_perturbations currently returns only valid ones,
        # we need to modify the flow slightly to capture raw logs or restructure.
        # To keep it clean, we will re-implement the loop here to capture logs.
        
        logger.info("Running generation loop with logging...")
        config = get_config_dict()
        seed = config.get("seed_global", 42)
        random.seed(seed)
        
        model = get_model()
        final_results = []
        all_raw_logs = []

        for task in tasks:
            task_id = task.get("task_id", "unknown")
            prompt = task.get("prompt", "")
            
            if not prompt:
                continue

            selected = None
            task_attempts = []

            for trans_type in TRANSFORMATION_TYPES:
                if selected:
                    break
                
                try:
                    if trans_type == "synonym":
                        candidate = substitute_synonyms(prompt)
                    elif trans_type == "typo":
                        candidate = inject_typos(prompt)
                    elif trans_type == "rephrase":
                        candidate = rephrase_syntax(prompt)
                    else:
                        continue
                    
                    if not candidate or candidate == prompt:
                        continue
                    
                    is_valid, score = validate_perturbation(prompt, candidate, model)
                    
                    # Log attempt
                    attempt_record = {
                        "type": trans_type,
                        "score": float(score),
                        "valid": is_valid,
                        "candidate": candidate
                    }
                    task_attempts.append(attempt_record)
                    
                    if is_valid:
                        selected = {
                            "task_id": task_id,
                            "original_prompt": prompt,
                            "perturbed_prompt": candidate,
                            "perturbation_type": trans_type,
                            "raw_score": float(score),
                            "is_valid": True,
                            "entry_point": task.get("entry_point", ""),
                            "canonical_solution": task.get("canonical_solution", "")
                        }
                        break
                except Exception as e:
                    logger.warning(f"Error in {trans_type} for {task_id}: {e}")
                    continue
            
            all_raw_logs.append({
                "task_id": task_id,
                "original_prompt": prompt,
                "attempts": task_attempts
            })

            if selected:
                final_results.append(selected)
                logger.info(f"Selected valid variant for {task_id}")
            else:
                logger.warning(f"No valid variant for {task_id}")

        # 3. Save Outputs
        save_results(final_results, OUTPUT_RAW_FILE) # Renaming for verification step compatibility
        # Note: The task says "Write data/processed/perturbation_candidates_raw.json"
        # But T018 filters FROM raw TO final. 
        # T017 verification: "Run ... --input data/processed/perturbation_candidates_raw.json"
        # So we save the raw log here as the "raw" file.
        # However, the function save_results saves the FINAL selected list.
        # We must save the RAW pool separately.
        
        # Re-save raw pool
        save_candidates_pool(tasks, all_raw_logs)
        
        # Save the actual selected results to a different file for T018 to use?
        # T017 description says: "log raw score and select; stop... Verification: ... --input data/processed/perturbation_candidates_raw.json"
        # This implies the raw file is the output of T017.
        # T018 then filters this raw file.
        # But T017 also says "generate exactly one valid variant".
        # So we have two outputs? Or the raw file contains the single selected?
        # The description says "log raw score...". Usually "raw" implies all attempts.
        # Let's assume the verification script checks the schema of the raw log.
        # We have already saved the raw log to OUTPUT_RAW_FILE via save_candidates_pool.
        # But save_results also wrote to OUTPUT_RAW_FILE (overwriting).
        # Let's fix:
        # 1. Save raw log to perturbation_candidates_raw.json
        # 2. Save selected list to perturbation_candidates_selected.json (intermediate for T018)
        
        # Re-do save logic cleanly
        with open(OUTPUT_RAW_FILE, "w", encoding="utf-8") as f:
            # Save the structure expected by validator: list of tasks with attempts
            json.dump(all_raw_logs, f, indent=2, ensure_ascii=False)
        
        # Save the selected results (for T018 to consume)
        selected_output = "data/processed/perturbation_candidates_selected.json"
        with open(selected_output, "w", encoding="utf-8") as f:
            json.dump(final_results, f, indent=2, ensure_ascii=False)

        logger.info(f"Pipeline complete. Raw log: {OUTPUT_RAW_FILE}, Selected: {selected_output}")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
