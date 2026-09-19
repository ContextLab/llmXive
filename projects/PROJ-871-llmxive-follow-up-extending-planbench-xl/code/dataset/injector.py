import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.config import get_path, get_hyperparameter


def load_raw_planbench_xl() -> List[Dict[str, Any]]:
    """
    Load the raw PlanBench-XL dataset from the derived data directory.
    Expects the raw data to be available as a JSONL or JSON file in data/raw/
    or data/derived/ based on the loader's previous execution.
    For this task, we assume T008 has populated data/raw/ with a file named
    'planbench_xl_raw.jsonl' or similar.
    """
    # Determine the source file path
    # T008 saves raw parquet to data/raw/, but we need to convert or load JSONL
    # Assuming T008 produced a JSONL for compatibility or we read the parquet
    # Here we assume the loader in T008 produced a JSONL for ease, or we handle parquet
    # If T008 produced parquet, we need to load it.
    # Let's assume T008 produced data/raw/planbench_xl_raw.jsonl for this implementation
    # If it's parquet, we'd need pandas. The requirements.txt includes pandas.
    
    raw_path = get_path("data_raw") / "planbench_xl_raw.jsonl"
    
    if not raw_path.exists():
        # Fallback: check for parquet if loader saved it as such
        parquet_path = get_path("data_raw") / "planbench_xl_raw.parquet"
        if parquet_path.exists():
            import pandas as pd
            df = pd.read_parquet(parquet_path)
            return df.to_dict(orient='records')
        else:
            raise FileNotFoundError(
                f"Raw PlanBench-XL data not found at {raw_path} or {parquet_path}. "
                "Ensure T008 (loader) has been executed successfully."
            )

    data = []
    with open(raw_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def inject_failures(
    data: List[Dict[str, Any]], 
    seed: int = 42, 
    injection_ratio: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Select a subset of tasks with 'success' ground truth and inject deterministic
    error patterns into their tool outputs.
    
    Args:
        data: List of task dictionaries from the raw dataset.
        seed: Random seed for reproducibility.
        injection_ratio: Fraction of success tasks to inject errors into.
        
    Returns:
        List of modified task dictionaries with injected errors.
    """
    random.seed(seed)
    
    # Filter tasks with ground_truth == "success"
    success_tasks = [
        task for task in data 
        if task.get("ground_truth", "").lower() == "success"
    ]
    
    if not success_tasks:
        raise ValueError(
            "No tasks with ground_truth='success' found in the dataset. "
            "Cannot inject failures."
        )
    
    # Select a subset to inject
    num_to_inject = max(1, int(len(success_tasks) * injection_ratio))
    selected_indices = random.sample(range(len(success_tasks)), num_to_inject)
    selected_tasks = [success_tasks[i] for i in selected_indices]
    
    injected_data = []
    
    # Add non-selected success tasks unchanged
    for task in success_tasks:
        if task not in selected_tasks:
            injected_data.append(task)
    
    # Add non-success tasks unchanged
    for task in data:
        if task.get("ground_truth", "").lower() != "success":
            injected_data.append(task)
    
    # Process selected tasks to inject errors
    # Note: We must be careful to maintain the original structure
    # and ONLY modify tool outputs, not ground_truth.
    for task in selected_tasks:
        # Deep copy to avoid modifying original data
        modified_task = json.loads(json.dumps(task))
        
        # Inject error into tool outputs
        # Assuming 'tool_outputs' or similar field exists in the task structure
        # If the structure varies, we need to handle it robustly
        if "tool_outputs" in modified_task:
            if isinstance(modified_task["tool_outputs"], list):
                # Append error to the first tool output or all
                for i, output in enumerate(modified_task["tool_outputs"]):
                    if isinstance(output, str):
                        modified_task["tool_outputs"][i] = f"{output}\nERROR: silent_tool_failure"
                    elif isinstance(output, dict):
                        # If output is a dict, add to a 'content' or 'result' field
                        if "content" in output:
                            output["content"] = f"{output['content']}\nERROR: silent_tool_failure"
                        elif "result" in output:
                            output["result"] = f"{output['result']}\nERROR: silent_tool_failure"
                        else:
                            # Fallback: add a new field
                            output["injected_error"] = "ERROR: silent_tool_failure"
                # Mark the task as having an injected error
                modified_task["injected_error"] = True
            else:
                # Single string output
                modified_task["tool_outputs"] = f"{modified_task['tool_outputs']}\nERROR: silent_tool_failure"
                modified_task["injected_error"] = True
        else:
            # If no tool_outputs field, we might need to inject at a different level
            # or skip. For now, we'll add a flag and a synthetic error field.
            modified_task["injected_error"] = True
            modified_task["synthetic_error"] = "ERROR: silent_tool_failure"
        
        injected_data.append(modified_task)
    
    return injected_data


def save_injected_data(data: List[Dict[str, Any]], output_path: Optional[str] = None) -> Path:
    """
    Save the injected data to a JSONL file.
    
    Args:
        data: List of task dictionaries.
        output_path: Optional path to save the file. Defaults to data/derived/implicit_failure_subset.jsonl
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = get_path("data_derived") / "implicit_failure_subset.jsonl"
    else:
        output_path = Path(output_path)
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')
    
    return output_path


def main():
    """
    Main entry point for the synthetic failure injection task.
    """
    print("Loading raw PlanBench-XL data...")
    raw_data = load_raw_planbench_xl()
    print(f"Loaded {len(raw_data)} tasks.")
    
    # Get hyperparameters from config if available, else use defaults
    seed = get_hyperparameter("injection_seed", 42)
    ratio = get_hyperparameter("injection_ratio", 0.3)
    
    print(f"Injecting failures with seed={seed}, ratio={ratio}...")
    injected_data = inject_failures(raw_data, seed=seed, injection_ratio=ratio)
    
    print(f"Injected failures into {len([t for t in injected_data if t.get('injected_error')])} tasks.")
    
    output_file = save_injected_data(injected_data)
    print(f"Saved injected data to {output_file}")
    
    return output_file


if __name__ == "__main__":
    main()