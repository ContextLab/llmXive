import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional
from utils.config import get_path, get_hyperparameter, set_deterministic_seed, ensure_dirs_exist

def load_raw_planbench_xl(input_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load the raw PlanBench-XL dataset."""
    if input_path is None:
        input_path = get_path('data/raw/planbench_xl.jsonl')
    
    if not input_path.exists():
        raise FileNotFoundError(f"Raw dataset not found at {input_path}")
    
    data = []
    with open(input_path, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def inject_failures(data: List[Dict[str, Any]], num_failures: int = 50, seed: int = 42) -> List[Dict[str, Any]]:
    """Inject synthetic failure patterns into success tasks."""
    set_deterministic_seed(seed)
    
    # Filter for success tasks
    success_tasks = [task for task in data if task.get('ground_truth') == 'success']
    
    if len(success_tasks) < num_failures:
        raise ValueError(f"Not enough success tasks to inject {num_failures} failures")
    
    # Select first N tasks deterministically
    selected_tasks = success_tasks[:num_failures]
    
    injected_data = []
    error_patterns = [
        "ERROR: silent_tool_failure",
        "ERROR: tool_timeout",
        "ERROR: invalid_tool_response",
        "ERROR: missing_tool_output"
    ]
    
    for task in selected_tasks:
        injected_task = task.copy()
        # Inject error pattern
        error_pattern = random.choice(error_patterns)
        injected_task['tool_output'] = f"{task.get('tool_output', '')}\n{error_pattern}"
        injected_task['injected_error_pattern'] = True
        injected_task['injected_error_type'] = error_pattern
        injected_data.append(injected_task)
    
    return injected_data

def save_injected_data(data: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """Save the injected failure subset."""
    if output_path is None:
        output_path = get_path('data/derived/implicit_failure_subset.jsonl')
    
    ensure_dirs_exist(output_path.parent)
    
    with open(output_path, 'w') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')
    
    return output_path

def main():
    """Main entry point for data injector."""
    raw_data = load_raw_planbench_xl()
    injected_data = inject_failures(raw_data, num_failures=50, seed=42)
    output_file = save_injected_data(injected_data)
    print(f"Injected failure subset saved to: {output_file}")

if __name__ == "__main__":
    main()
