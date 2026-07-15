"""
Perturbation Generation Pipeline (T018)

Implements the core pipeline to:
1. Load HumanEval tasks from data/raw/humaneval.jsonl
2. Generate up to 3 perturbation variants per task (synonym, typo, rephrase)
3. Score all candidates for semantic similarity
4. Filter to retain only those with similarity > 0.95
5. Output the final filtered set to data/processed/perturbed_prompts.jsonl
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_directories
from data.download_humaneval import download_humaneval
from data.perturbations import generate_perturbation_variants
from data.semantic_validator import validate_perturbation_batch
from utils.logging import get_perturbation_logger, init_logging

# Constants
MAX_VARIANTS_PER_TASK = 3
SEMANTIC_THRESHOLD = 0.95
RAW_DATA_PATH = "data/raw/humaneval.jsonl"
PROCESSED_OUTPUT_PATH = "data/processed/perturbed_prompts.jsonl"
LOG_PATH = "data/logs/perturbation_raw.log"

def load_humaneval_tasks() -> List[Dict[str, Any]]:
    """
    Load HumanEval tasks from the downloaded JSONL file.
    Falls back to re-downloading if the file does not exist.
    """
    raw_path = Path(RAW_DATA_PATH)
    if not raw_path.exists():
        logging.info(f"Raw HumanEval data not found at {raw_path}. Downloading...")
        download_humaneval()
    
    tasks = []
    with open(raw_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                tasks.append(json.loads(line))
    return tasks

def generate_and_filter_perturbations(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Core pipeline:
    1. For each task, generate up to MAX_VARIANTS_PER_TASK candidates.
    2. Score all candidates using semantic similarity.
    3. Filter candidates where similarity > SEMANTIC_THRESHOLD.
    4. Return the list of valid perturbed prompts.
    """
    logger = get_perturbation_logger()
    all_valid_perturbations = []
    
    total_tasks = len(tasks)
    logger.info(f"Starting perturbation pipeline for {total_tasks} tasks.")

    for idx, task in enumerate(tasks):
        task_id = task.get("task_id", f"task_{idx}")
        prompt = task.get("prompt", "")
        
        if not prompt:
            logger.warning(f"Skipping task {task_id}: missing prompt.")
            continue

        # Generate variants
        # Returns a list of dicts: {'type': str, 'text': str, 'original': str}
        candidates = generate_perturbation_variants(prompt, max_variants=MAX_VARIANTS_PER_TASK)
        
        if not candidates:
            logger.debug(f"No candidates generated for {task_id}.")
            continue

        # Prepare batch for validation
        # We need to map original text to candidates for the validator
        batch_data = []
        for c in candidates:
            batch_data.append({
                "original": prompt,
                "perturbed": c["text"],
                "type": c["type"],
                "task_id": task_id
            })

        # Validate batch (computes similarity scores)
        # Returns list of dicts with 'score', 'valid', 'type', etc.
        validated_results = validate_perturbation_batch(batch_data, threshold=SEMANTIC_THRESHOLD)

        valid_count = 0
        for res in validated_results:
            if res.get("valid", False):
                # Construct the full record for the output
                new_task = task.copy()
                new_task["perturbation_type"] = res["type"]
                new_task["original_prompt"] = prompt
                new_task["perturbed_prompt"] = res["perturbed"]
                new_task["semantic_score"] = res["score"]
                new_task["is_perturbed"] = True
                
                all_valid_perturbations.append(new_task)
                valid_count += 1
            else:
                # Log excluded perturbation
                logger.info(
                    f"Excluded perturbation for {task_id} (Type: {res['type']}, "
                    f"Score: {res['score']:.4f} < {SEMANTIC_THRESHOLD})"
                )

        logger.info(f"Task {idx+1}/{total_tasks} ({task_id}): Generated {len(candidates)}, "
                    f"Retained {valid_count}.")

    return all_valid_perturbations

def save_results(perturbations: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save the filtered perturbation dataset to JSONL.
    """
    out_file = Path(output_path)
    ensure_directories() # Ensure directories exist
    
    with open(out_file, 'w', encoding='utf-8') as f:
        for item in perturbations:
            f.write(json.dumps(item) + '\n')
    
    logging.info(f"Saved {len(perturbations)} perturbed prompts to {output_path}")

def main():
    """
    Entry point for the perturbation generation pipeline.
    """
    # Initialize logging
    init_logging()
    logger = get_perturbation_logger()
    logger.info("Starting Perturbation Generation Pipeline (T018)")

    # 1. Load Data
    tasks = load_humaneval_tasks()
    logger.info(f"Loaded {len(tasks)} HumanEval tasks.")

    # 2. Generate and Filter
    final_perturbations = generate_and_filter_perturbations(tasks)
    
    # 3. Save Results
    save_results(final_perturbations, PROCESSED_OUTPUT_PATH)

    logger.info(f"Pipeline complete. Total valid perturbations: {len(final_perturbations)}")

if __name__ == "__main__":
    main()
