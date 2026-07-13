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
    Loads the raw PlanBench-XL dataset.
    In a real implementation, this would download/load from HuggingFace.
    For this cleanup task, we assume the data exists or is loaded via the loader module.
    """
    raw_path = get_path("data_raw") / "planbench_xl.parquet"
    if raw_path.exists():
        # Placeholder for actual loading logic
        return []
    return []

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
    
    # Filter for success tasks (assuming ground_truth indicates success)
    # In real data, this logic would be more robust
    success_tasks = [t for t in tasks if t.get("ground_truth", "").lower() in ["success", "completed"]]
    
    # Select subset to inject
    num_to_inject = int(len(success_tasks) * target_proportion)
    selected_indices = random.sample(range(len(success_tasks)), min(num_to_inject, len(success_tasks)))
    
    for i, task in enumerate(tasks):
        new_task = task.copy()
        new_task["injected_error"] = False
        
        if i in selected_indices:
            # Inject error pattern
            new_task["injected_error"] = True
            # Append error to tool outputs or response simulation
            if "tool_outputs" in new_task:
                new_task["tool_outputs"].append("ERROR: silent_tool_failure")
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
        output_path = str(get_path("implicit_failure_subset"))
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        for task in tasks:
            f.write(json.dumps(task) + "\n")
    
    return output_path

def main():
    """
    Main entry point for data injection.
    """
    # Placeholder for loading data
    tasks = [] 
    injected = inject_failures(tasks)
    path = save_injected_data(injected)
    print(f"Injected data saved to {path}")

if __name__ == "__main__":
    main()
