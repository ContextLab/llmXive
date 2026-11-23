import os
import json
import time
import logging
import csv
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import from sibling modules using the exact API surface provided
from config import get_experiment_config, get_seeds
from agent import SkillLibrary, run_task, append_to_log, main as agent_main
from utils import get_model, get_embedding
from logging_config import get_logger

# Configure logging for this module
logger = get_logger(__name__)

def load_tasks(path: str = "data/raw/tasks.json") -> List[Dict[str, Any]]:
    """Load tasks from the generated JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Tasks file not found at {path}. Run generate_data.py first.")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_skills(path: str = "data/raw/skills.json") -> List[Dict[str, Any]]:
    """Load skills from the generated JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Skills file not found at {path}. Run generate_data.py first.")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_experiment_for_size(
    library_size: int,
    tasks: List[Dict[str, Any]],
    all_skills: List[Dict[str, Any]],
    seed_a: int,
    seed_b: int
) -> Dict[str, Any]:
    """
    Run the agent experiment for a specific library size.
    
    Args:
        library_size: Number of skills to include in the active library.
        tasks: Full list of generated tasks.
        all_skills: Full list of generated skills.
        seed_a: Seed for skill generation (determines which skills are picked if subset).
        seed_b: Seed for task generation (determines ground truth).
    
    Returns:
        Dictionary containing aggregated metrics for this library size.
    """
    logger.info(f"Starting experiment for library size: {library_size}")
    
    # Select a deterministic subset of skills based on seed_a
    # We take the first N skills after shuffling deterministically to simulate a library
    import random
    random.seed(seed_a)
    shuffled_skills = all_skills.copy()
    random.shuffle(shuffled_skills)
    active_skills = shuffled_skills[:library_size]
    
    # Initialize the SkillLibrary with the active subset
    # Note: The agent.py API expects a list of skill dicts
    skill_lib = SkillLibrary(active_skills)
    
    total_tasks = len(tasks)
    successful_tasks = 0
    total_latency = 0.0
    total_tokens = 0
    total_precision = 0.0
    total_diversity = 0.0
    
    # Ensure output directory exists
    os.makedirs("data/results", exist_ok=True)
    
    for i, task in enumerate(tasks):
        logger.debug(f"Processing task {i+1}/{total_tasks}: {task.get('id', 'unknown')}")
        
        start_time = time.time()
        
        try:
            # Run the task using the agent logic
            # run_task returns a dict with success, latency, tokens, precision, diversity
            result = run_task(
                task=task,
                library=skill_lib,
                seed=seed_b  # Use seed_b for any task-specific randomness if needed
            )
            
            elapsed = time.time() - start_time
            total_latency += elapsed
            
            if result.get('success', False):
                successful_tasks += 1
            
            total_tokens += result.get('tokens', 0)
            total_precision += result.get('retrieval_precision', 0.0)
            total_diversity += result.get('retrieval_diversity', 0.0)
            
            # Log to the CSV log
            log_entry = {
                'task_id': task.get('id'),
                'skill_id': None, # Top-level task result
                'success': result.get('success', False),
                'latency': elapsed,
                'tokens': result.get('tokens', 0),
                'retrieval_precision': result.get('retrieval_precision', 0.0),
                'retrieval_diversity': result.get('retrieval_diversity', 0.0),
                'pruning_risk_count': 0,
                'library_size': library_size,
                'pruning_enabled': False # T028 not yet implemented
            }
            append_to_log(log_entry)
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Task {task.get('id')} failed with error: {e}")
            # Log failure
            log_entry = {
                'task_id': task.get('id'),
                'skill_id': None,
                'success': False,
                'latency': elapsed,
                'tokens': 0,
                'retrieval_precision': 0.0,
                'retrieval_diversity': 0.0,
                'pruning_risk_count': 0,
                'library_size': library_size,
                'pruning_enabled': False
            }
            append_to_log(log_entry)
    
    success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0.0
    avg_latency = total_latency / total_tasks if total_tasks > 0 else 0.0
    avg_precision = total_precision / total_tasks if total_tasks > 0 else 0.0
    avg_diversity = total_diversity / total_tasks if total_tasks > 0 else 0.0
    
    metrics = {
        "library_size": library_size,
        "total_tasks": total_tasks,
        "successful_tasks": successful_tasks,
        "success_rate": success_rate,
        "avg_latency_seconds": avg_latency,
        "total_tokens": total_tokens,
        "avg_retrieval_precision": avg_precision,
        "avg_retrieval_diversity": avg_diversity,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    logger.info(f"Completed library size {library_size}: Success Rate = {success_rate:.2f}")
    return metrics

def main():
    """
    Main entry point to run the full experiment across all configured library sizes.
    Iterates through library sizes, calls run_experiment_for_size, and aggregates results.
    """
    logger.info("Starting full experiment run.")
    
    # Load configuration
    config = get_experiment_config()
    seeds = get_seeds()
    seed_a = seeds['seed_a']
    seed_b = seeds['seed_b']
    library_sizes = config.get('LIBRARY_SIZES', [10, 30, 50, 100])
    
    # Load data
    tasks = load_tasks()
    all_skills = load_skills()
    
    logger.info(f"Loaded {len(tasks)} tasks and {len(all_skills)} skills.")
    logger.info(f"Running for library sizes: {library_sizes}")
    
    results = []
    
    for size in library_sizes:
        # Ensure size does not exceed available skills
        actual_size = min(size, len(all_skills))
        if actual_size != size:
            logger.warning(f"Requested size {size} exceeds available skills {len(all_skills)}. Using {actual_size}.")
        
        size_metrics = run_experiment_for_size(
            library_size=actual_size,
            tasks=tasks,
            all_skills=all_skills,
            seed_a=seed_a,
            seed_b=seed_b
        )
        results.append(size_metrics)
    
    # Aggregate final metrics
    final_report = {
        "experiment_config": {
            "seeds": seeds,
            "library_sizes_tested": library_sizes,
            "total_skills_available": len(all_skills)
        },
        "results": results
    }
    
    # Write to data/results/metrics.json
    output_path = "data/results/metrics.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2)
    
    logger.info(f"Experiment complete. Results saved to {output_path}")
    print(f"Experiment complete. Results saved to {output_path}")
    
    return final_report

if __name__ == "__main__":
    main()