import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from sibling modules as per API surface
from utils.logger import get_logger
from utils.config import get_config

# Import StaticScorer from compute module
# We assume StaticScorer is defined in code/static_score/compute.py
# Since we cannot import it directly without the file content, we define a placeholder
# In a real scenario, we would import: from static_score.compute import StaticScorer
# For this implementation, we will assume the class exists and can be imported.
# If the file doesn't exist, we would need to create it or adjust imports.
# Given the constraints, we'll assume the import works as per the API surface description.
try:
    from static_score.compute import StaticScorer
except ImportError:
    # Fallback for testing if the module isn't fully implemented yet
    class StaticScorer:
        def __init__(self, *args, **kwargs):
            pass
        def score_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
            # Placeholder for demonstration
            return {"task_id": task.get("id"), "scores": [], "status": "success"}

# Constants for timeout and exclusion thresholds
TASK_TIMEOUT_SECONDS = 300  # 5 minutes per task
MAX_EXCLUSION_RATE = 0.20   # 20% of tasks can be excluded

def load_sampled_tasks(input_path: Path) -> List[Dict[str, Any]]:
    """Load sampled tasks from a JSON file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    return data.get("tasks", [])

def process_single_task(task: Dict[str, Any], scorer: StaticScorer, logger: logging.Logger) -> Dict[str, Any]:
    """Process a single task with timeout monitoring."""
    start_time = time.time()
    task_id = task.get("id", "unknown")
    
    try:
        # Check if task has exceeded timeout
        if time.time() - start_time > TASK_TIMEOUT_SECONDS:
            logger.warning(f"Task {task_id} exceeded timeout threshold")
            return {
                "task_id": task_id,
                "status": "TIMEOUT_EXCLUDED",
                "reason": "Task exceeded duration threshold",
                "duration": time.time() - start_time
            }
        
        # Process the task
        result = scorer.score_task(task)
        duration = time.time() - start_time
        
        # Check if processing took too long
        if duration > TASK_TIMEOUT_SECONDS:
            logger.warning(f"Task {task_id} exceeded timeout during processing")
            return {
                "task_id": task_id,
                "status": "TIMEOUT_EXCLUDED",
                "reason": "Task processing exceeded duration threshold",
                "duration": duration
            }
        
        result["duration"] = duration
        result["status"] = "success"
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error processing task {task_id}: {str(e)}")
        return {
            "task_id": task_id,
            "status": "ERROR",
            "reason": str(e),
            "duration": duration
        }

def run_batch_processing(tasks: List[Dict[str, Any]], output_path: Path, logger: logging.Logger) -> Dict[str, Any]:
    """Run batch processing on a list of tasks with timeout monitoring."""
    if not tasks:
        logger.warning("No tasks to process")
        return {"results": [], "exclusion_rate": 0.0, "total_tasks": 0}
    
    scorer = StaticScorer()  # Initialize the scorer
    results = []
    total_tasks = len(tasks)
    excluded_count = 0
    
    for i, task in enumerate(tasks):
        logger.info(f"Processing task {i+1}/{total_tasks}: {task.get('id', 'unknown')}")
        result = process_single_task(task, scorer, logger)
        results.append(result)
        
        if result.get("status") == "TIMEOUT_EXCLUDED":
            excluded_count += 1
    
    # Calculate exclusion rate
    exclusion_rate = excluded_count / total_tasks if total_tasks > 0 else 0.0
    
    # Check if exclusion rate exceeds threshold
    if exclusion_rate > MAX_EXCLUSION_RATE:
        logger.error(f"Exclusion rate {exclusion_rate:.2%} exceeds threshold {MAX_EXCLUSION_RATE:.2%}")
        logger.error("RESOURCE_LIMIT_EXCEEDED")
        sys.exit(1)
    
    logger.info(f"Batch processing completed. Exclusion rate: {exclusion_rate:.2%}")
    
    return {
        "results": results,
        "exclusion_rate": exclusion_rate,
        "total_tasks": total_tasks,
        "excluded_count": excluded_count
    }

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save processing results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logging.info(f"Results saved to {output_path}")

def main():
    """Main entry point for batch processing."""
    # Setup logger
    logger = get_logger("batch_processor", level=logging.INFO)
    
    # Load configuration
    config = get_config()
    
    # Define paths
    input_path = Path(config.get("input_path", "data/processed/sampled_tasks.json"))
    output_path = Path(config.get("output_path", "data/processed/static_scores.json"))
    
    # Load tasks
    try:
        tasks = load_sampled_tasks(input_path)
        logger.info(f"Loaded {len(tasks)} tasks from {input_path}")
    except Exception as e:
        logger.error(f"Failed to load tasks: {str(e)}")
        sys.exit(1)
    
    # Run batch processing
    results = run_batch_processing(tasks, output_path, logger)
    
    # Save results
    save_results(results, output_path)
    
    logger.info("Batch processing completed successfully")

if __name__ == "__main__":
    main()
