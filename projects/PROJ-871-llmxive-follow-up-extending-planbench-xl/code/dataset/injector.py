"""
Synthetic Failure Injection Module.
Creates an implicit failure subset from the PlanBench-XL dataset.
"""
import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.config import get_path, get_hyperparameter

def load_raw_planbench_xl() -> List[Dict[str, Any]]:
    """
    Loads the raw PlanBench-XL dataset from the local cache.
    Expects the file to be at data/raw/planbench_xl.jsonl (converted from parquet by T008).
    If the parquet file exists, it attempts to convert it or load it directly if pandas is available.
    """
    raw_path = get_path("data_raw")
    parquet_path = raw_path / "planbench_xl.parquet"
    jsonl_path = raw_path / "planbench_xl.jsonl"

    # Priority 1: Load from pre-converted JSONL if it exists
    if jsonl_path.exists():
        tasks = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    tasks.append(json.loads(line))
        return tasks

    # Priority 2: Try to load parquet if pandas is available (T008 dependency)
    if parquet_path.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(parquet_path)
            # Convert dataframe to list of dicts
            tasks = df.to_dict(orient='records')
            return tasks
        except ImportError:
            raise RuntimeError(
                "PlanBench-XL parquet file found but pandas is not installed. "
                "Please install pandas or ensure T008 has converted the data to JSONL."
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load parquet file: {e}")

    raise FileNotFoundError(
        f"Raw PlanBench-XL data not found. Expected at {jsonl_path} or {parquet_path}. "
        "Ensure T008 (loader) has completed successfully."
    )

def inject_failures(
    tasks: List[Dict[str, Any]],
    seed: int = 42,
    target_proportion: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Injects deterministic error patterns into a subset of tasks.
    
    Args:
        tasks: List of task dictionaries.
        seed: Random seed for reproducibility.
        target_proportion: Proportion of success tasks to inject.
        
    Returns:
        List of tasks with injected errors.
    """
    random.seed(seed)
    injected_tasks = []
    
    # Identify success tasks based on ground_truth field
    # We look for "success", "completed", or "true" in the ground_truth string
    success_tasks_indices = []
    for i, task in enumerate(tasks):
        gt = str(task.get("ground_truth", "")).lower()
        if gt in ["success", "completed", "true", "successful"]:
            success_tasks_indices.append(i)
    
    if not success_tasks_indices:
        raise ValueError(
            "No tasks with 'success' ground truth found in the dataset. "
            "Cannot inject failures into non-existent success tasks."
        )

    # Select subset to inject
    num_to_inject = int(len(success_tasks_indices) * target_proportion)
    # Ensure we inject at least 1 if there are success tasks
    num_to_inject = max(1, num_to_inject)
    
    selected_indices_set = set(random.sample(success_tasks_indices, min(num_to_inject, len(success_tasks_indices))))
    
    for i, task in enumerate(tasks):
        new_task = task.copy()
        new_task["injected_error"] = False
        
        if i in selected_indices_set:
            # Inject error pattern
            new_task["injected_error"] = True
            # Append error to tool outputs or create the list if missing
            if "tool_outputs" in new_task:
                if isinstance(new_task["tool_outputs"], list):
                    new_task["tool_outputs"].append("ERROR: silent_tool_failure")
                else:
                    # If it's a string, convert to list
                    new_task["tool_outputs"] = [new_task["tool_outputs"], "ERROR: silent_tool_failure"]
            else:
                new_task["tool_outputs"] = ["ERROR: silent_tool_failure"]
        
        injected_tasks.append(new_task)
    
    return injected_tasks

def save_injected_data(tasks: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
    """
    Saves the injected dataset to a JSONL file.
    
    Args:
        tasks: List of injected task dictionaries.
        output_path: Optional output path.
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        # Ensure the path points to data/derived as per spec
        derived_dir = get_path("data_derived")
        output_path = str(derived_dir / "implicit_failure_subset.jsonl")
    
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path_obj, 'w', encoding='utf-8') as f:
        for task in tasks:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")
    
    return str(output_path_obj)

def main():
    """
    Main entry point for data injection.
    Loads raw data, injects failures, and saves the result.
    """
    print("Loading raw PlanBench-XL data...")
    try:
        tasks = load_raw_planbench_xl()
    except (FileNotFoundError, RuntimeError) as e:
        print(f"ERROR: {e}")
        return
    
    print(f"Loaded {len(tasks)} tasks.")
    
    # Get hyperparameters if available, otherwise use defaults
    seed = get_hyperparameter("injection_seed", 42)
    proportion = get_hyperparameter("injection_proportion", 0.3)
    
    print(f"Injecting failures (seed={seed}, proportion={proportion})...")
    injected_tasks = inject_failures(tasks, seed=seed, target_proportion=proportion)
    
    success_count = sum(1 for t in injected_tasks if t.get("injected_error", False))
    print(f"Injected errors into {success_count} tasks.")
    
    output_path = save_injected_data(injected_tasks)
    print(f"Injected data saved to {output_path}")

if __name__ == "__main__":
    main()
