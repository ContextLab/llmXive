import hashlib
import logging
import os
import sys
import itertools
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_variables(dataset: Any) -> Tuple[bool, Optional[List[str]]]:
    """Validate that required variables exist in the dataset."""
    required_vars = ["observations", "actions", "rewards"]
    missing_vars = []
    
    if hasattr(dataset, 'features'):
        features = list(dataset.features.keys())
    else:
        # Fallback for streaming or other dataset types
        sample = next(iter(dataset))
        features = list(sample.keys())
    
    for var in required_vars:
        if var not in features:
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required variables: {missing_vars}")
        return False, missing_vars
    
    logger.info(f"All required variables present: {required_vars}")
    return True, None

def filter_error_prone_tasks(dataset: Any) -> List[Dict[str, Any]]:
    """
    Filter the dataset to identify error-prone tasks.
    
    Logic:
    1. Identify tasks where the agent failed in the baseline (success == 0 or False).
    2. If the dataset doesn't have an explicit 'success' column, infer failure
       based on reward patterns (e.g., final reward < threshold or negative rewards).
    
    Returns:
        List of task dictionaries that are error-prone.
    """
    error_prone_tasks = []
    success_col = None
    
    # Determine success column name
    if hasattr(dataset, 'features'):
        features = list(dataset.features.keys())
        if 'success' in features:
            success_col = 'success'
        elif 'final_reward' in features:
            # Infer success from final_reward if available
            pass
    else:
        sample = next(iter(dataset))
        if 'success' in sample:
            success_col = 'success'
    
    # Iterate through dataset
    for idx, item in enumerate(dataset):
        is_error_prone = False
        
        if success_col:
            # Check explicit success field
            if item.get(success_col) == 0 or item.get(success_col) is False:
                is_error_prone = True
        else:
            # Infer from reward patterns
            rewards = item.get('rewards', [])
            if rewards:
                final_reward = rewards[-1] if isinstance(rewards, list) else rewards
                if final_reward < 0:  # Negative reward indicates failure
                    is_error_prone = True
        
        if is_error_prone:
            # Ensure task_id exists, otherwise use index
            task_id = item.get('task_id', f"task_{idx}")
            error_prone_tasks.append({
                'task_id': task_id,
                'index': idx,
                'data': item
            })
    
    logger.info(f"Identified {len(error_prone_tasks)} error-prone tasks out of {len(dataset)} total tasks")
    return error_prone_tasks

def select_tasks_for_baseline(
    error_prone_tasks: List[Dict[str, Any]],
    max_tasks: Optional[int] = None,
    sample_strategy: str = "first_n"
) -> List[Dict[str, Any]]:
    """
    Select a subset of error-prone tasks for baseline execution.
    
    Args:
        error_prone_tasks: List of error-prone task dictionaries from filter_error_prone_tasks.
        max_tasks: Maximum number of tasks to select. If None, select all.
        sample_strategy: Strategy for sampling if max_tasks is hit.
                       Options: "first_n", "random" (requires random seed).
    
    Returns:
        List of selected task dictionaries.
    """
    if not error_prone_tasks:
        logger.warning("No error-prone tasks found to select.")
        return []
    
    if max_tasks is None or max_tasks >= len(error_prone_tasks):
        logger.info(f"Selecting all {len(error_prone_tasks)} error-prone tasks.")
        return error_prone_tasks
    
    # Apply sampling strategy
    if sample_strategy == "first_n":
        selected = list(itertools.islice(error_prone_tasks, max_tasks))
        logger.info(f"Selected first {max_tasks} error-prone tasks using 'first_n' strategy.")
    elif sample_strategy == "random":
        import random
        # Set a fixed seed for reproducibility
        random.seed(42)
        selected = random.sample(error_prone_tasks, max_tasks)
        logger.info(f"Selected {max_tasks} random error-prone tasks using 'random' strategy (seed=42).")
    else:
        raise ValueError(f"Unknown sample_strategy: {sample_strategy}. Use 'first_n' or 'random'.")
    
    return selected

def main():
    """
    Main entry point for downloading and filtering the AgentBench dataset.
    
    This function:
    1. Loads the 'lmz/agentbench' dataset.
    2. Validates required variables.
    3. Filters for error-prone tasks.
    4. Selects a subset for baseline execution (T012a logic).
    5. Saves the selected tasks to a JSON file in data/processed/.
    """
    logger.info("Starting dataset download and task selection process...")
    
    # 1. Load dataset
    dataset_name = "lmz/agentbench"
    logger.info(f"Loading dataset: {dataset_name}")
    
    try:
        # Load the dataset (using streaming to handle large sizes if needed)
        # Note: If the full dataset is too large for memory, we might need to adjust this.
        # For now, we assume it fits or use streaming=True if necessary.
        dataset = load_dataset(dataset_name, split="train")
        logger.info(f"Dataset loaded successfully. Total rows: {len(dataset)}")
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        raise

    # 2. Validate variables
    is_valid, missing = validate_variables(dataset)
    if not is_valid:
        raise ValueError(f"Dataset validation failed. Missing variables: {missing}")

    # 3. Filter error-prone tasks
    error_prone_tasks = filter_error_prone_tasks(dataset)
    
    if not error_prone_tasks:
        logger.warning("No error-prone tasks identified. Cannot proceed with selection.")
        # Depending on requirements, we might want to exit or handle this differently.
        # For now, we'll proceed with an empty list, but log a warning.
        selected_tasks = []
    else:
        # 4. Select tasks for baseline (T012a logic)
        # Define max_tasks based on constraints (e.g., hourly/size limits)
        # For this implementation, we'll use a reasonable default or allow override.
        # Let's assume a limit of 50 tasks for baseline if not specified.
        max_tasks = 50 
        
        selected_tasks = select_tasks_for_baseline(
            error_prone_tasks, 
            max_tasks=max_tasks, 
            sample_strategy="first_n"
        )
    
    # 5. Save selected tasks
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "selected_baseline_tasks.json"
    
    # Prepare data for saving (remove large 'data' field if needed, or keep full)
    # For now, we'll keep the full data but in a serializable format.
    # If 'data' contains non-serializable objects, we might need to convert.
    # Assuming dataset items are already dicts of serializable types.
    serializable_selected = []
    for task in selected_tasks:
        task_copy = task.copy()
        # Ensure 'data' is serializable (it should be from load_dataset)
        serializable_selected.append(task_copy)
    
    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_selected, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Selected {len(selected_tasks)} tasks saved to {output_file}")
    logger.info("Task selection process completed successfully.")

if __name__ == "__main__":
    main()