"""
Contamination filter module.

Compares task release dates to model training cut-offs using strict inequality.
Task Release Date < Model Training Cutoff
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    logger = logging.getLogger("contamination_filter")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

def load_model_cutoffs() -> Dict[str, str]:
    """
    Load model training cutoff dates.
    In a real implementation, this would come from a config file or database.
    """
    # Example cutoffs - in production, these should be configurable
    return {
        "gpt-4": "2023-09-01",
        "gpt-4-turbo": "2024-01-01",
        "claude-3": "2024-02-01",
        "llama-3": "2024-03-01",
        "codex": "2021-06-01"
    }

def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string to datetime object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return None

def filter_contaminated_tasks(
    execution_log: Dict[str, Any],
    model_cutoffs: Dict[str, str]
) -> Dict[str, Any]:
    """
    Filter tasks that are contaminated based on release date vs model cutoff.
    
    Condition: Task Release Date < Model Training Cutoff
    If task release date is BEFORE model cutoff, it is considered contaminated.
    """
    logger = setup_logging()
    logger.info("Starting contamination filter...")
    
    tasks = execution_log.get("tasks", [])
    filtered_tasks = []
    excluded_tasks = []
    
    for task in tasks:
        task_id = task.get("task_id", "unknown")
        model = task.get("model", "unknown")
        release_date_str = task.get("release_date", "")
        
        task_release_date = parse_date(release_date_str)
        model_cutoff_str = model_cutoffs.get(model, "2099-12-31")
        model_cutoff_date = parse_date(model_cutoff_str)
        
        if task_release_date is None or model_cutoff_date is None:
            # If dates are missing, log warning and include task
            logger.warning(f"Missing date info for task {task_id}: release={release_date_str}, model={model}")
            filtered_tasks.append(task)
            continue
        
        # Check for contamination: Task Release Date < Model Training Cutoff
        if task_release_date < model_cutoff_date:
            excluded_tasks.append({
                "task_id": task_id,
                "model": model,
                "release_date": release_date_str,
                "model_cutoff": model_cutoff_str,
                "reason": f"Task release date ({release_date_str}) is before model cutoff ({model_cutoff_str})"
            })
            logger.info(f"Excluded task {task_id} for model {model} due to contamination")
        else:
            filtered_tasks.append(task)
    
    return {
        "total_tasks": len(tasks),
        "included_tasks": len(filtered_tasks),
        "excluded_tasks": len(excluded_tasks),
        "exclusion_rate": len(excluded_tasks) / len(tasks) if tasks else 0.0,
        "excluded_task_details": excluded_tasks,
        "filtered_tasks": filtered_tasks
    }

def run_contamination_pipeline(
    execution_log: Dict[str, Any],
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the contamination filter pipeline.
    
    Args:
        execution_log: The execution log data.
        output_dir: Directory to save results.
        
    Returns:
        Dictionary containing contamination filter results.
    """
    logger = setup_logging()
    logger.info("Running contamination filter pipeline...")
    
    model_cutoffs = load_model_cutoffs()
    results = filter_contaminated_tasks(execution_log, model_cutoffs)
    
    # Add metadata
    results["metadata"] = {
        "analysis_type": "contamination_filter",
        "model_cutoffs_used": model_cutoffs,
        "comparison_logic": "Task Release Date < Model Training Cutoff"
    }
    
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "contamination_filter.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Contamination filter results saved to {output_path}")
    
    return results

def main():
    """Entry point for contamination filter."""
    from config import get_results_path
    import json
    
    execution_log_path = get_results_path() / "artifacts" / "execution_log.json"
    if not execution_log_path.exists():
        print(f"Error: Execution log not found at {execution_log_path}")
        sys.exit(1)
        
    with open(execution_log_path, 'r') as f:
        execution_log = json.load(f)
        
    results = run_contamination_pipeline(execution_log)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
