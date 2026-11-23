"""
Batch processing loop for computing static branching scores.

This module orchestrates the processing of a fixed subset of tasks (exactly 100),
applying timeout logic and resource monitoring, and saving results to disk.
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from sibling modules using the exact API surface provided
from static_score.compute import StaticScorer, process_task_with_timeout
from utils.config import get_config
from utils.logger import get_logger, setup_progress_bar, log_metric, log_error_summary
from utils.resource_monitor import ResourceMonitor, run_with_monitoring

# Configure logger for this module
logger = get_logger(__name__)

# Constants
TARGET_TASK_COUNT = 100
OUTPUT_FILE = "data/processed/static_scores.json"
TIMEOUT_SECONDS = 30 * 60  # 30 minutes per task
MAX_EXCLUSION_RATE = 0.3  # 30% exclusion rate threshold


def load_sampled_tasks(
    data_dir: Path, 
    target_count: int = TARGET_TASK_COUNT
) -> List[Dict[str, Any]]:
    """
    Load a sampled subset of tasks from the downloaded dataset.
    
    Args:
        data_dir: Path to the data directory containing downloaded datasets
        target_count: Number of tasks to sample (default: 100)
        
    Returns:
        List of task dictionaries with 'task_id', 'question', and 'trace' fields
    """
    # Check for GSM8K data first, then MATH
    gsm8k_path = data_dir / "gsm8k" / "train" / "data-00000-of-00001.arrow"
    math_path = data_dir / "math" / "train" / "data-00000-of-00001.arrow"
    
    tasks = []
    
    if gsm8k_path.exists():
        logger.info(f"Loading GSM8K tasks from {gsm8k_path}")
        # Import datasets here to avoid circular imports at module level
        from datasets import load_from_disk
        try:
            # Try loading from disk if available
            gsm8k_ds = load_from_disk(str(data_dir / "gsm8k"))
            if "train" in gsm8k_ds:
                tasks.extend(gsm8k_ds["train"].to_pandas().to_dict(orient="records"))
            else:
                # Fallback: load directly
                gsm8k_ds = load_from_disk(str(data_dir / "gsm8k"))
                tasks.extend(gsm8k_ds.to_pandas().to_dict(orient="records"))
        except Exception as e:
            logger.warning(f"Could not load GSM8K from disk: {e}")
            # Try loading from HF cache or download
            from datasets import load_dataset
            gsm8k_ds = load_dataset("openai/gsm8k", "main", split="train")
            tasks.extend(gsm8k_ds.to_pandas().to_dict(orient="records"))
    elif math_path.exists():
        logger.info(f"Loading MATH tasks from {math_path}")
        from datasets import load_from_disk
        try:
            math_ds = load_from_disk(str(data_dir / "math"))
            tasks.extend(math_ds.to_pandas().to_dict(orient="records"))
        except Exception as e:
            logger.warning(f"Could not load MATH from disk: {e}")
            from datasets import load_dataset
            math_ds = load_dataset("hendrycks/math", "train", split="train")
            tasks.extend(math_ds.to_pandas().to_dict(orient="records"))
    else:
        # Try loading directly from HF if no local data
        logger.info("No local data found, loading from HuggingFace...")
        from datasets import load_dataset
        try:
            gsm8k_ds = load_dataset("openai/gsm8k", "main", split="train")
            tasks.extend(gsm8k_ds.to_pandas().to_dict(orient="records"))
        except Exception as e:
            logger.error(f"Failed to load GSM8K: {e}")
            raise RuntimeError("Could not load any dataset. Please run download.py first.")
    
    # Ensure we have exactly target_count tasks
    if len(tasks) < target_count:
        logger.warning(f"Only {len(tasks)} tasks available, requested {target_count}")
        # If we have fewer, use all available
        return tasks[:len(tasks)]
    
    # Sample exactly target_count tasks (first N for reproducibility)
    sampled_tasks = tasks[:target_count]
    
    # Normalize task structure
    normalized_tasks = []
    for i, task in enumerate(sampled_tasks):
        normalized_task = {
            "task_id": f"task_{i:04d}",
            "question": task.get("question", task.get("problem", "")),
            "trace": task.get("answer", task.get("solution", "")),
            "original_id": task.get("id", f"orig_{i}")
        }
        normalized_tasks.append(normalized_task)
    
    logger.info(f"Loaded and normalized {len(normalized_tasks)} tasks")
    return normalized_tasks


def process_single_task(
    task: Dict[str, Any], 
    scorer: StaticScorer,
    timeout_seconds: int = TIMEOUT_SECONDS
) -> Optional[Dict[str, Any]]:
    """
    Process a single task with timeout protection.
    
    Args:
        task: Task dictionary with 'task_id', 'question', 'trace'
        scorer: StaticScorer instance
        timeout_seconds: Maximum time allowed for processing this task
        
    Returns:
        Result dictionary or None if task timed out
    """
    task_id = task["task_id"]
    logger.info(f"Processing task {task_id}")
    
    try:
        # Use the timeout wrapper from compute.py
        result = process_task_with_timeout(
            task=task,
            scorer=scorer,
            timeout_seconds=timeout_seconds
        )
        
        if result is None:
            logger.warning(f"Task {task_id} timed out or was excluded")
            log_metric("TIMEOUT_EXCLUDED", 1)
            return None
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing task {task_id}: {e}")
        log_error_summary(task_id, str(e))
        return None


def run_batch_processing(
    tasks: List[Dict[str, Any]],
    scorer: StaticScorer,
    timeout_seconds: int = TIMEOUT_SECONDS
) -> List[Dict[str, Any]]:
    """
    Run batch processing on a list of tasks with monitoring.
    
    Args:
        tasks: List of task dictionaries
        scorer: StaticScorer instance
        timeout_seconds: Timeout per task
        
    Returns:
        List of result dictionaries
    """
    results = []
    excluded_count = 0
    total_count = len(tasks)
    
    # Setup progress bar
    pbar = setup_progress_bar(total=total_count, desc="Processing tasks")
    
    for task in pbar:
        task_id = task["task_id"]
        pbar.set_postfix({"task": task_id})
        
        result = process_single_task(task, scorer, timeout_seconds)
        
        if result is None:
            excluded_count += 1
            pbar.set_postfix({"excluded": excluded_count})
        else:
            results.append(result)
            pbar.set_postfix({"processed": len(results), "excluded": excluded_count})
    
    # Check exclusion rate
    exclusion_rate = excluded_count / total_count if total_count > 0 else 0
    
    if exclusion_rate > MAX_EXCLUSION_RATE:
        logger.error(f"Exclusion rate {exclusion_rate:.2%} exceeds threshold {MAX_EXCLUSION_RATE:.2%}")
        log_metric("RESOURCE_LIMIT_EXCEEDED", 1)
        sys.exit(1)
    
    log_metric("tasks_processed", len(results))
    log_metric("tasks_excluded", excluded_count)
    log_metric("exclusion_rate", exclusion_rate)
    
    logger.info(f"Batch processing complete: {len(results)} tasks processed, {excluded_count} excluded")
    return results


def save_results(
    results: List[Dict[str, Any]], 
    output_path: Path
) -> None:
    """
    Save results to JSON file.
    
    Args:
        results: List of result dictionaries
        output_path: Path to output file
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(results)} results to {output_path}")
    log_metric("output_file", str(output_path))


def main() -> None:
    """
    Main entry point for batch processing.
    
    This function:
    1. Loads exactly 100 tasks from the dataset
    2. Initializes the StaticScorer
    3. Processes tasks with timeout protection
    4. Monitors resources and enforces limits
    5. Saves results to data/processed/static_scores.json
    """
    # Get configuration
    config = get_config()
    
    # Initialize resource monitor
    resource_monitor = ResourceMonitor(
        max_memory_gb=7.0,
        max_time_hours=5.0
    )
    
    # Start resource monitoring
    logger.info("Starting batch processing with resource monitoring")
    
    def processing_wrapper():
        # Load tasks
        data_dir = Path(config.data_dir)
        tasks = load_sampled_tasks(data_dir, TARGET_TASK_COUNT)
        
        if len(tasks) == 0:
            logger.error("No tasks loaded. Exiting.")
            sys.exit(1)
        
        logger.info(f"Processing {len(tasks)} tasks")
        
        # Initialize scorer
        scorer = StaticScorer(
            model_name=config.model_path,
            device="cpu",
            epsilon=config.epsilon_smoothing
        )
        
        # Run batch processing with timeout
        results = run_batch_processing(
            tasks=tasks,
            scorer=scorer,
            timeout_seconds=TIMEOUT_SECONDS
        )
        
        # Save results
        output_path = Path(config.data_dir) / OUTPUT_FILE
        save_results(results, output_path)
        
        return results
    
    # Run with resource monitoring
    try:
        results = run_with_monitoring(
            func=processing_wrapper,
            monitor=resource_monitor
        )
        
        logger.info("Batch processing completed successfully")
        
    except MemoryError:
        logger.error("Memory limit exceeded")
        log_metric("RESOURCE_LIMIT_EXCEEDED", 1)
        sys.exit(1)
    except TimeoutError:
        logger.error("Time limit exceeded")
        log_metric("RESOURCE_LIMIT_EXCEEDED", 1)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during batch processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
