"""
Baseline experiment runner for User Story 3.

Runs the full experiment set with PRUNING DISABLED to satisfy SC-003
(performance recovery comparison).

Outputs: data/results/experiment_log_baseline.csv
"""
import os
import json
import csv
import time
import logging
from typing import Dict, List, Any, Optional

# Import from existing project modules
from config import get_seeds
from agent import (
    get_model,
    SkillLibrary,
    calculate_retrieval_precision,
    calculate_retrieval_diversity,
    append_to_log,
    run_task,
    main as agent_main
)
from utils import get_embedding, cosine_similarity
from generate_data import generate_skills, generate_tasks_with_ground_truth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants from config (assuming T005 defines these)
# If not defined in config, we define them here for the baseline run
LIBRARY_SIZES = [10, 30, 50, 100]
OUTPUT_FILE = "data/results/experiment_log_baseline.csv"

def load_tasks(tasks_path: str = "data/raw/tasks.json") -> List[Dict[str, Any]]:
    """Load tasks from JSON file."""
    if not os.path.exists(tasks_path):
        raise FileNotFoundError(f"Tasks file not found: {tasks_path}")
    with open(tasks_path, 'r') as f:
        return json.load(f)

def load_skills(skills_path: str = "data/raw/skills.json") -> List[Dict[str, Any]]:
    """Load skills from JSON file."""
    if not os.path.exists(skills_path):
        raise FileNotFoundError(f"Skills file not found: {skills_path}")
    with open(skills_path, 'r') as f:
        return json.load(f)

def run_baseline_experiment_for_size(
    library_size: int,
    tasks: List[Dict[str, Any]],
    all_skills: List[Dict[str, Any]],
    model,
    log_file_path: str
) -> Dict[str, Any]:
    """
    Run experiment for a specific library size with pruning DISABLED.

    Args:
        library_size: Number of skills to include in the library
        tasks: List of all tasks
        all_skills: List of all available skills
        model: SentenceTransformer model
        log_file_path: Path to the CSV log file

    Returns:
        Dictionary with aggregated metrics
    """
    logger.info(f"Running baseline experiment for library size: {library_size}")

    # Select subset of skills (first N skills for simplicity)
    # In a real scenario, we might want random selection with fixed seed
    selected_skills = all_skills[:library_size]
    skill_library = SkillLibrary(selected_skills, model)

    # Metrics aggregation
    total_tasks = 0
    successful_tasks = 0
    total_latency = 0.0
    total_tokens = 0
    total_precision = 0.0
    total_diversity = 0.0

    # Process tasks
    for task in tasks:
        task_id = task.get('task_id', 'unknown')
        ground_truth = task.get('ground_truth', [])

        start_time = time.time()
        
        # Run task with pruning DISABLED
        # We pass pruning_enabled=False to run_task
        result = run_task(
            task=task,
            skill_library=skill_library,
            model=model,
            pruning_enabled=False,  # CRITICAL: Pruning disabled for baseline
            logger=logger
        )
        
        end_time = time.time()
        latency = end_time - start_time

        total_tasks += 1
        total_latency += latency

        if result.get('success', False):
            successful_tasks += 1

        total_tokens += result.get('tokens', 0)

        # Calculate retrieval metrics
        retrieved = result.get('retrieved_skills', [])
        precision = calculate_retrieval_precision(retrieved, ground_truth)
        diversity = calculate_retrieval_diversity(retrieved, ground_truth, model)

        total_precision += precision
        total_diversity += diversity

        # Log to CSV (append mode)
        append_to_log(
            log_file=log_file_path,
            task_id=task_id,
            skill_id=None,  # Not applicable for full task run
            success=result.get('success', False),
            latency=latency,
            tokens=result.get('tokens', 0),
            retrieval_precision=precision,
            retrieval_diversity=diversity,
            pruning_risk_count=0,  # No pruning, so 0
            library_size=library_size,
            pruning_enabled=False
        )

        if total_tasks % 50 == 0:
            logger.info(f"Processed {total_tasks}/{len(tasks)} tasks")

    # Calculate averages
    avg_success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0.0
    avg_latency = total_latency / total_tasks if total_tasks > 0 else 0.0
    avg_tokens = total_tokens / total_tasks if total_tasks > 0 else 0.0
    avg_precision = total_precision / total_tasks if total_tasks > 0 else 0.0
    avg_diversity = total_diversity / total_tasks if total_tasks > 0 else 0.0

    return {
        'library_size': library_size,
        'total_tasks': total_tasks,
        'successful_tasks': successful_tasks,
        'success_rate': avg_success_rate,
        'avg_latency': avg_latency,
        'avg_tokens': avg_tokens,
        'avg_precision': avg_precision,
        'avg_diversity': avg_diversity,
        'pruning_enabled': False
    }

def main():
    """Main entry point for baseline experiment."""
    logger.info("Starting baseline experiment (pruning disabled)")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # Load data
    try:
        tasks = load_tasks()
        all_skills = load_skills()
        logger.info(f"Loaded {len(tasks)} tasks and {len(all_skills)} skills")
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        logger.error("Please run code/generate_data.py first to create data/raw/tasks.json and data/raw/skills.json")
        return

    # Load model
    model = get_model()

    # Clear existing log file to start fresh for baseline
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
        logger.info(f"Removed existing baseline log file: {OUTPUT_FILE}")

    # Write header to CSV
    with open(OUTPUT_FILE, 'w', newline='') as csvfile:
        fieldnames = [
            'task_id', 'skill_id', 'success', 'latency', 'tokens',
            'retrieval_precision', 'retrieval_diversity', 'pruning_risk_count',
            'library_size', 'pruning_enabled'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    # Run experiments for each library size
    all_results = []
    for size in LIBRARY_SIZES:
        result = run_baseline_experiment_for_size(
            library_size=size,
            tasks=tasks,
            all_skills=all_skills,
            model=model,
            log_file_path=OUTPUT_FILE
        )
        all_results.append(result)
        logger.info(f"Completed library size {size}: Success Rate = {result['success_rate']:.4f}")

    # Save aggregated metrics to JSON
    metrics_output = "data/results/baseline_metrics.json"
    with open(metrics_output, 'w') as f:
        json.dump(all_results, f, indent=2)
    logger.info(f"Saved aggregated baseline metrics to {metrics_output}")

    logger.info("Baseline experiment completed successfully")
    logger.info(f"Results saved to: {OUTPUT_FILE}")
    logger.info(f"Aggregated metrics saved to: {metrics_output}")

if __name__ == "__main__":
    main()