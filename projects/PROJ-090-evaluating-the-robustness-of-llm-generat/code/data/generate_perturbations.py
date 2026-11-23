import json
import logging
import os
import random
import sys
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing API surface
from data.perturbations import substitute_synonyms, inject_typos, rephrase_syntax
from config import ensure_directories, get_seed_global, get_seed_dataset, get_budget_generations
from utils.logging import get_perturbation_logger, init_logging

# Constants
PERTURBATION_TYPES = ["synonym", "typo", "rephrase"]
MAX_CANDIDATES_PER_TASK = 3
TOTAL_BUDGET_CAP = 656
OUTPUT_FILE = "data/processed/perturbation_candidates_raw.json"

def setup_logging():
    """Initialize logging for perturbation generation."""
    ensure_directories(["data/processed", "data/logs"])
    init_logging()
    logger = get_perturbation_logger()
    logger.info("Setting up perturbation generation pipeline...")
    return logger

def load_humaneval_tasks() -> List[Dict[str, Any]]:
    """Load HumanEval tasks from the downloaded dataset."""
    input_file = "data/raw/humaneval.json"
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"HumanEval data not found at {input_file}. Run T012 first.")

    with open(input_file, 'r', encoding='utf-8') as f:
        tasks = json.load(f)

    # Ensure deterministic ordering by task_id
    tasks.sort(key=lambda x: x.get("task_id", ""))
    return tasks

def generate_single_candidate(
    task: Dict[str, Any],
    perturbation_type: str,
    logger: logging.Logger
) -> Optional[Dict[str, Any]]:
    """
    Generate a single perturbation candidate for a task.
    Returns a dict with: task_id, perturbation_type, raw_score, is_valid, candidate_text.
    Note: raw_score and is_valid are placeholders for this stage; 
    actual scoring happens in T016.
    """
    task_id = task.get("task_id", "unknown")
    original_prompt = task.get("prompt", "")

    if not original_prompt:
        logger.warning(f"Task {task_id} has no prompt, skipping.")
        return None

    candidate_text = None
    raw_score = 0.0  # Placeholder; will be computed in T016
    is_valid = False  # Placeholder; will be computed in T016

    try:
        if perturbation_type == "synonym":
            candidate_text = substitute_synonyms(original_prompt)
        elif perturbation_type == "typo":
            candidate_text = inject_typos(original_prompt)
        elif perturbation_type == "rephrase":
            candidate_text = rephrase_syntax(original_prompt)
        else:
            logger.error(f"Unknown perturbation type: {perturbation_type}")
            return None

        if not candidate_text or candidate_text.strip() == "":
            logger.warning(f"Generated empty candidate for {task_id} ({perturbation_type})")
            return None

    except Exception as e:
        logger.error(f"Error generating {perturbation_type} for {task_id}: {e}")
        return None

    return {
        "task_id": str(task_id),
        "perturbation_type": perturbation_type,
        "raw_score": raw_score,  # Placeholder
        "is_valid": is_valid,    # Placeholder
        "candidate_text": candidate_text
    }

def generate_and_filter_perturbations(
    tasks: List[Dict[str, Any]],
    logger: logging.Logger
) -> List[Dict[str, Any]]:
    """
    Generate up to MAX_CANDIDATES_PER_TASK (3) candidates per task.
    Iterate through perturbation types: synonym, typo, rephrase.
    Enforce TOTAL_BUDGET_CAP (656) globally.
    Prioritize original prompts (not applicable here as we only generate perturbations),
    then fill remaining slots with perturbed prompts in deterministic order.
    """
    all_candidates = []
    budget_remaining = TOTAL_BUDGET_CAP
    random.seed(get_seed_global())

    # Deterministic order: task_id ascending, then perturbation_type alphabetically
    # Tasks are already sorted by task_id in load_humaneval_tasks()
    # Perturbation types are sorted alphabetically: ["rephrase", "synonym", "typo"]
    sorted_types = sorted(PERTURBATION_TYPES)

    for task in tasks:
        if budget_remaining <= 0:
            logger.warning(f"Budget cap ({TOTAL_BUDGET_CAP}) reached. Stopping generation.")
            break

        task_id = task.get("task_id", "unknown")
        generated_for_task = 0

        for pert_type in sorted_types:
            if budget_remaining <= 0 or generated_for_task >= MAX_CANDIDATES_PER_TASK:
                break

            candidate = generate_single_candidate(task, pert_type, logger)
            if candidate:
                all_candidates.append(candidate)
                budget_remaining -= 1
                generated_for_task += 1
                logger.debug(f"Generated {pert_type} for {task_id}")

    return all_candidates

def save_candidates_pool(
    candidates: List[Dict[str, Any]],
    logger: logging.Logger
) -> str:
    """Save the full unfiltered list of candidates to JSON."""
    output_path = Path(OUTPUT_FILE)
    ensure_directories([str(output_path.parent)])

    # Sort by task_id ascending, then perturbation_type alphabetically for determinism
    sorted_candidates = sorted(
        candidates,
        key=lambda x: (x.get("task_id", ""), x.get("perturbation_type", ""))
    )

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_candidates, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(sorted_candidates)} candidates to {output_path}")
    return str(output_path)

def main():
    """Main entry point for perturbation generation pipeline."""
    logger = setup_logging()
    logger.info("Starting perturbation generation pipeline (T017)...")

    try:
        tasks = load_humaneval_tasks()
        logger.info(f"Loaded {len(tasks)} HumanEval tasks.")

        candidates = generate_and_filter_perturbations(tasks, logger)
        logger.info(f"Generated {len(candidates)} perturbation candidates.")

        # Verify cap logic
        task_counts = Counter(c["task_id"] for c in candidates)
        max_per_task = max(task_counts.values()) if task_counts else 0
        if max_per_task > MAX_CANDIDATES_PER_TASK:
            logger.error(f"ERROR: Max candidates per task exceeded: {max_per_task}")
            sys.exit(1)

        if len(candidates) > TOTAL_BUDGET_CAP:
            logger.error(f"ERROR: Total budget cap exceeded: {len(candidates)} > {TOTAL_BUDGET_CAP}")
            sys.exit(1)

        output_file = save_candidates_pool(candidates, logger)

        # Verification log
        logger.info(f"Verification: Task counts max={max_per_task}, Total={len(candidates)}")
        logger.info(f"Output file: {output_file}")
        logger.info("T017 completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
