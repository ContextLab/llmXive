"""
run_baseline.py

Runs the full experiment set (library sizes ranging from small to large) with
pruning disabled and saves results to data/results/experiment_log_baseline.csv.

This serves as the baseline for SC-003 performance recovery comparison.
"""
import os
import json
import csv
import time
import logging
from typing import Dict, List, Any, Optional

# Import from existing project modules
from code.config import get_seeds, pin_seeds, get_experiment_config
from code.utils import get_embedding, cosine_similarity
from code.agent import (
    SkillLibrary,
    calculate_retrieval_precision,
    calculate_retrieval_diversity,
    execute_skill,
    run_task,
    append_to_log
)
from code.logging_config import get_logger, log_experiment_entry, CSVLogHandler

# Configure logging
logger = get_logger(__name__)

# Constants
BASELINE_OUTPUT_PATH = "data/results/experiment_log_baseline.csv"
TASKS_PATH = "data/raw/tasks.json"
SKILLS_PATH = "data/raw/skills.json"

# Library sizes to test (small to large)
LIBRARY_SIZES = [10, 25, 50, 75, 100]

# Number of tasks to run per configuration (sample size)
TASK_SAMPLE_SIZE = 20

def load_tasks() -> List[Dict[str, Any]]:
    """Load tasks from the generated JSON file."""
    if not os.path.exists(TASKS_PATH):
        raise FileNotFoundError(f"Tasks file not found: {TASKS_PATH}")
    
    with open(TASKS_PATH, 'r') as f:
        data = json.load(f)
    
    tasks = data.get('tasks', [])
    if not tasks:
        raise ValueError("No tasks found in tasks.json")
    
    logger.info(f"Loaded {len(tasks)} tasks from {TASKS_PATH}")
    return tasks

def load_skills() -> List[Dict[str, Any]]:
    """Load skills from the generated JSON file."""
    if not os.path.exists(SKILLS_PATH):
        raise FileNotFoundError(f"Skills file not found: {SKILLS_PATH}")
    
    with open(SKILLS_PATH, 'r') as f:
        data = json.load(f)
    
    skills = data.get('skills', [])
    if not skills:
        raise ValueError("No skills found in skills.json")
    
    logger.info(f"Loaded {len(skills)} skills from {SKILLS_PATH}")
    return skills

def run_baseline_experiment_for_size(
    tasks: List[Dict[str, Any]],
    all_skills: List[Dict[str, Any]],
    library_size: int,
    log_file_path: str
) -> List[Dict[str, Any]]:
    """
    Run the baseline experiment for a specific library size with pruning disabled.
    
    Args:
        tasks: List of task dictionaries
        all_skills: Complete list of available skills
        library_size: Number of skills to include in the library
        log_file_path: Path to the output CSV log file
    
    Returns:
        List of log entries for this configuration
    """
    logger.info(f"Running baseline experiment with library size: {library_size}")
    
    # Pin seeds for reproducibility
    seeds = get_seeds()
    pin_seeds(seeds)
    
    # Select a subset of skills for this library size
    # Use deterministic selection based on library_size
    import random
    random.seed(seeds['SEED_A'])
    selected_skills = random.sample(all_skills, min(library_size, len(all_skills)))
    
    logger.info(f"Selected {len(selected_skills)} skills for library size {library_size}")
    
    # Create skill library (pruning disabled for baseline)
    skill_lib = SkillLibrary(
        skills=selected_skills,
        pruning_enabled=False  # Explicitly disable pruning for baseline
    )
    
    # Sample tasks
    task_sample = tasks[:min(TASK_SAMPLE_SIZE, len(tasks))]
    logger.info(f"Running {len(task_sample)} tasks")
    
    log_entries = []
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    
    # Write header if file doesn't exist
    if not os.path.exists(log_file_path):
        with open(log_file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            # Header matching the schema from T009c
            headers = [
                'task_id', 'skill_id', 'success', 'latency', 'tokens',
                'retrieval_precision', 'retrieval_diversity', 'pruning_risk_count',
                'library_size', 'pruning_enabled'
            ]
            writer.writerow(headers)
    
    for idx, task in enumerate(task_sample):
        task_id = task.get('task_id', f'task_{idx}')
        ground_truth = task.get('ground_truth', [])
        
        logger.debug(f"Processing task {task_id}")
        
        try:
            # Run the task with the baseline agent
            result = run_task(
                task=task,
                skill_library=skill_lib,
                k=5  # Retrieve top-5 skills
            )
            
            success = result.get('success', False)
            latency = result.get('latency', 0.0)
            tokens = result.get('tokens', 0)
            
            # Calculate retrieval metrics
            retrieved_skills = result.get('retrieved_skills', [])
            retrieved_ids = [s.get('skill_id') for s in retrieved_skills]
            
            precision = calculate_retrieval_precision(retrieved_ids, ground_truth)
            diversity = calculate_retrieval_diversity(retrieved_skills, ground_truth, skill_lib.skills)
            
            # For baseline, pruning_risk_count is always 0 since pruning is disabled
            pruning_risk_count = 0
            
            # Prepare log entry
            log_entry = {
                'task_id': task_id,
                'skill_id': retrieved_ids[0] if retrieved_ids else None,
                'success': success,
                'latency': latency,
                'tokens': tokens,
                'retrieval_precision': precision,
                'retrieval_diversity': diversity,
                'pruning_risk_count': pruning_risk_count,
                'library_size': library_size,
                'pruning_enabled': False
            }
            
            # Append to log file with fsync to ensure durability
            append_to_log(log_file_path, log_entry)
            log_entries.append(log_entry)
            
            logger.info(f"Task {task_id}: success={success}, precision={precision:.4f}")
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            # Log failure entry
            failure_entry = {
                'task_id': task_id,
                'skill_id': None,
                'success': False,
                'latency': 0.0,
                'tokens': 0,
                'retrieval_precision': 0.0,
                'retrieval_diversity': 0.0,
                'pruning_risk_count': 0,
                'library_size': library_size,
                'pruning_enabled': False
            }
            append_to_log(log_file_path, failure_entry)
            log_entries.append(failure_entry)
    
    return log_entries

def main():
    """Main entry point for the baseline experiment."""
    logger.info("Starting baseline experiment (pruning disabled)")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(BASELINE_OUTPUT_PATH), exist_ok=True)
    
    # Load data
    try:
        tasks = load_tasks()
        skills = load_skills()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load data: {e}")
        raise
    
    all_log_entries = []
    
    # Run experiment for each library size
    for size in LIBRARY_SIZES:
        logger.info(f"--- Configuration: Library Size = {size} ---")
        
        entries = run_baseline_experiment_for_size(
            tasks=tasks,
            all_skills=skills,
            library_size=size,
            log_file_path=BASELINE_OUTPUT_PATH
        )
        
        all_log_entries.extend(entries)
        logger.info(f"Completed library size {size}: {len(entries)} entries")
    
    logger.info(f"Baseline experiment complete. Total entries: {len(all_log_entries)}")
    logger.info(f"Results saved to: {BASELINE_OUTPUT_PATH}")
    
    # Verify output file exists and has content
    if os.path.exists(BASELINE_OUTPUT_PATH):
        with open(BASELINE_OUTPUT_PATH, 'r') as f:
            reader = csv.reader(f)
            row_count = sum(1 for _ in reader)
            logger.info(f"Output file contains {row_count} rows (including header)")
    
    return all_log_entries

if __name__ == "__main__":
    main()