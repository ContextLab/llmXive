"""
run_experiment.py

Iterates through configured library sizes, invokes the agent execution loop,
and aggregates results into data/results/metrics.json.

This script orchestrates the full experiment by:
1. Loading configuration (library sizes, seeds).
2. Iterating through each library size.
3. Calling agent.py logic (run_task) for the full dataset.
4. Aggregating success rates, latency, and retrieval metrics.
5. Saving the summary to data/results/metrics.json.
"""

import os
import json
import time
import logging
import csv
from typing import Dict, List, Any, Optional

# Import from local project modules (matching API surface)
from config import get_seeds, LIBRARY_SIZES
from utils import get_embedding, cosine_similarity
from agent import (
    SkillLibrary,
    calculate_retrieval_precision,
    calculate_retrieval_diversity,
    append_to_log,
    run_task
)

# Configure logging for this script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure output directories exist
os.makedirs("data/results", exist_ok=True)

def load_tasks(tasks_path: str = "data/raw/tasks.json") -> List[Dict[str, Any]]:
    """Load the generated tasks from the raw data file."""
    if not os.path.exists(tasks_path):
        raise FileNotFoundError(
            f"Tasks file not found at {tasks_path}. "
            "Please run generate_data.py first."
        )
    with open(tasks_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_skills(skills_path: str = "data/raw/skills.json") -> List[Dict[str, Any]]:
    """Load the generated skills from the raw data file."""
    if not os.path.exists(skills_path):
        raise FileNotFoundError(
            f"Skills file not found at {skills_path}. "
            "Please run generate_data.py first."
        )
    with open(skills_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_experiment_for_size(
    library_size: int,
    tasks: List[Dict[str, Any]],
    all_skills: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Run the agent experiment for a specific library size.

    Returns a dictionary containing aggregated metrics for this library size.
    """
    logger.info(f"Starting experiment for library size: {library_size}")

    # Initialize the SkillLibrary with the specified size
    # The agent.py logic expects a subset of skills or a library object
    # We simulate the "active library" by taking the first N skills for determinism
    # or by shuffling if a seed is required for selection (here we use deterministic slicing
    # based on the assumption that skills are pre-generated and ordered).
    # To ensure reproducibility across runs with the same seed, we rely on the
    # generate_data.py ordering.
    active_skills = all_skills[:library_size]

    # Re-initialize the SkillLibrary with the subset
    # Note: In a real scenario, we might need to re-embed or filter based on the subset.
    # Here we pass the subset directly.
    skill_lib = SkillLibrary(active_skills)

    # Metrics tracking
    total_tasks = len(tasks)
    successful_tasks = 0
    total_latency = 0.0
    total_tokens = 0
    retrieval_precisions = []
    retrieval_diversities = []
    log_entries = []

    # Reset the log file for this specific run configuration?
    # Per T022, we append to the log. For aggregation, we track in memory.
    # We will write to the CSV log as we go.
    
    # Clear the CSV log header if it's a fresh run, but since we append,
    # we assume the header exists from T022.
    # If the file doesn't exist, we write the header.
    log_file_path = "data/results/experiment_log.csv"
    if not os.path.exists(log_file_path):
        with open(log_file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "task_id", "skill_id", "success", "latency", "tokens",
                "retrieval_precision", "retrieval_diversity", "pruning_risk_count",
                "library_size", "pruning_enabled"
            ])

    for idx, task in enumerate(tasks):
        task_id = task.get("id", f"task_{idx}")
        ground_truth_skills = task.get("ground_truth", [])
        
        # Run the task
        start_time = time.time()
        result = run_task(task, skill_lib)
        end_time = time.time()

        latency = end_time - start_time
        success = result.get("success", False)
        tokens = result.get("tokens", 0)
        retrieved_skills = result.get("retrieved_skills", [])

        # Calculate metrics
        precision = calculate_retrieval_precision(retrieved_skills, ground_truth_skills)
        diversity = calculate_retrieval_diversity(retrieved_skills, ground_truth_skills, skill_lib)
        
        # For pruning risk, we assume 0 unless the agent logic explicitly counts it
        # T027 handles the counting, but for this aggregator we just read the result
        # if the agent returns it, otherwise default to 0 for this batch.
        pruning_risk = result.get("pruning_risk_count", 0)

        # Update aggregates
        if success:
            successful_tasks += 1
        total_latency += latency
        total_tokens += tokens
        retrieval_precisions.append(precision)
        retrieval_diversities.append(diversity)

        # Log entry
        log_entry = {
            "task_id": task_id,
            "skill_id": retrieved_skills[0] if retrieved_skills else None, # Primary skill used
            "success": success,
            "latency": round(latency, 4),
            "tokens": tokens,
            "retrieval_precision": round(precision, 4),
            "retrieval_diversity": round(diversity, 4),
            "pruning_risk_count": pruning_risk,
            "library_size": library_size,
            "pruning_enabled": True # Assuming pruning is on per US2/T027
        }
        
        # Append to CSV
        append_to_log(log_entry)
        
        if (idx + 1) % 50 == 0:
            logger.info(f"Processed {idx + 1}/{total_tasks} tasks for size {library_size}")

    # Calculate averages
    avg_latency = total_latency / total_tasks if total_tasks > 0 else 0
    success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0
    avg_precision = sum(retrieval_precisions) / len(retrieval_precisions) if retrieval_precisions else 0
    avg_diversity = sum(retrieval_diversities) / len(retrieval_diversities) if retrieval_diversities else 0

    return {
        "library_size": library_size,
        "total_tasks": total_tasks,
        "successful_tasks": successful_tasks,
        "success_rate": round(success_rate, 4),
        "avg_latency_seconds": round(avg_latency, 4),
        "total_tokens": total_tokens,
        "avg_retrieval_precision": round(avg_precision, 4),
        "avg_retrieval_diversity": round(avg_diversity, 4),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

def main():
    """
    Main entry point for the experiment runner.
    Iterates through all configured library sizes and aggregates results.
    """
    logger.info("Loading configuration and data...")
    seeds = get_seeds()
    logger.info(f"Seeds loaded: A={seeds['seed_a']}, B={seeds['seed_b']}")

    # Load data
    tasks = load_tasks()
    all_skills = load_skills()

    if not tasks:
        logger.error("No tasks found. Exiting.")
        return

    if not all_skills:
        logger.error("No skills found. Exiting.")
        return

    logger.info(f"Loaded {len(tasks)} tasks and {len(all_skills)} total skills.")

    results = []
    
    # Iterate through library sizes defined in config
    # T005 defines: 10, 30, 50, 100
    sizes_to_run = LIBRARY_SIZES
    
    logger.info(f"Running experiments for library sizes: {sizes_to_run}")

    for size in sizes_to_run:
        if size > len(all_skills):
            logger.warning(f"Library size {size} exceeds total skills {len(all_skills)}. Skipping.")
            continue

        try:
            result = run_experiment_for_size(size, tasks, all_skills)
            results.append(result)
            logger.info(f"Completed size {size}: Success Rate = {result['success_rate']}")
        except Exception as e:
            logger.error(f"Experiment failed for library size {size}: {e}", exc_info=True)
            # Continue to next size to ensure partial results are saved
            results.append({
                "library_size": size,
                "error": str(e),
                "success_rate": 0.0
            })

    # Aggregate and save final metrics
    output_path = "data/results/metrics.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "experiment_config": {
                "seeds": seeds,
                "library_sizes_tested": sizes_to_run,
                "total_skills_available": len(all_skills)
            },
            "results": results
        }, f, indent=2)

    logger.info(f"Experiment complete. Results saved to {output_path}")
    print(f"Experiment finished. See {output_path} for details.")

if __name__ == "__main__":
    main()
