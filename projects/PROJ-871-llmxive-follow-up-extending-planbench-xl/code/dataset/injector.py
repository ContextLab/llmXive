import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.config import get_path, get_hyperparameter


def load_raw_planbench_xl() -> List[Dict[str, Any]]:
    """
    Loads the raw PlanBench-XL dataset from the derived location.
    Since T008 saves the raw parquet to data/raw/, we assume the
    loader has converted it to a JSONL or parquet file we can iterate.
    For this implementation, we expect the raw data to be available
    as a JSONL file in data/raw/planbench_xl.jsonl (converted from parquet by T008).
    If T008 saves parquet, we would need to read it. Assuming JSONL for simplicity
    as per common pipeline patterns, or we read the parquet if that's the output.
    
    Given the constraint to use real data and T008 output, we assume T008
    produces a JSONL file at data/raw/planbench_xl.jsonl for easy streaming.
    """
    raw_path = get_path("data_raw") / "planbench_xl.jsonl"
    
    if not raw_path.exists():
        # Fallback to parquet if JSONL doesn't exist, assuming T008 saves parquet
        parquet_path = get_path("data_raw") / "planbench_xl.parquet"
        if parquet_path.exists():
            try:
                import pandas as pd
                df = pd.read_parquet(parquet_path)
                return df.to_dict(orient="records")
            except ImportError:
                raise RuntimeError("pandas required to read parquet data. Install it.")
        else:
            raise FileNotFoundError(
                f"Raw data not found at {raw_path} or {parquet_path}. "
                "Ensure T008 has successfully downloaded and processed the dataset."
            )

    records = []
    with open(raw_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def inject_failures(
    data: List[Dict[str, Any]], 
    n: int = 50, 
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Selects the first N tasks where ground_truth == success and injects
    specific error patterns into their tool outputs to create the "implicit failure" subset.
    
    Args:
        data: List of task records from PlanBench-XL.
        n: Number of tasks to inject (default 50).
        seed: Random seed for deterministic selection.
        
    Returns:
        List of modified task records with injected errors.
    """
    random.seed(seed)
    
    # Filter for successful tasks
    success_tasks = [
        task for task in data 
        if task.get("ground_truth") == "success"
    ]
    
    if len(success_tasks) < n:
        raise ValueError(
            f"Requested {n} success tasks for injection, but only found {len(success_tasks)}. "
            "Cannot proceed with injection."
        )
    
    # Select first N tasks deterministically (since list is ordered from file)
    # The requirement says "first N tasks ... using a fixed random seed and deterministic iteration order"
    # If the file order is deterministic, taking the first N is sufficient.
    # To be strictly compliant with "using a fixed random seed", we could shuffle with seed,
    # but "first N" implies order preservation. Let's stick to the first N as they appear.
    selected_tasks = success_tasks[:n]
    
    injected_data = []
    error_pattern = "ERROR: silent_tool_failure"
    
    for task in selected_tasks:
        # Create a copy to avoid mutating the original
        modified_task = task.copy()
        
        # Inject error into tool outputs
        # Assuming 'tool_outputs' or 'actions' field exists
        if "tool_outputs" in modified_task:
            if isinstance(modified_task["tool_outputs"], list):
                # Inject into the first output or all
                for i in range(len(modified_task["tool_outputs"])):
                    modified_task["tool_outputs"][i] = error_pattern
            elif isinstance(modified_task["tool_outputs"], str):
                modified_task["tool_outputs"] = error_pattern
        elif "actions" in modified_task:
            # Fallback if actions field is used
            if isinstance(modified_task["actions"], list):
                for i in range(len(modified_task["actions"])):
                    if isinstance(modified_task["actions"][i], dict):
                        modified_task["actions"][i]["output"] = error_pattern
                    else:
                        modified_task["actions"][i] = error_pattern
        
        # Add the injected_error_pattern flag
        modified_task["injected_error_pattern"] = True
        modified_task["original_ground_truth"] = task.get("ground_truth")
        modified_task["ground_truth"] = "failure" # Simulate failure state for evaluation
        
        injected_data.append(modified_task)
        
    return injected_data


def save_injected_data(data: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """
    Saves the injected data to a JSONL file.
    
    Args:
        data: List of modified task records.
        output_path: Path to save the file. Defaults to data/derived/implicit_failure_subset.jsonl.
        
    Returns:
        The path where the file was saved.
    """
    if output_path is None:
        output_path = get_path("data_derived") / "implicit_failure_subset.jsonl"
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for record in data:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            
    return output_path


def main():
    """
    Main entry point for the synthetic failure injection script.
    """
    print("Starting synthetic failure injection (T009a)...")
    
    # Load raw data
    print("Loading raw PlanBench-XL data...")
    raw_data = load_raw_planbench_xl()
    print(f"Loaded {len(raw_data)} records.")
    
    # Get hyperparameters
    n_tasks = get_hyperparameter("injection_n", default=50)
    seed = get_hyperparameter("injection_seed", default=42)
    
    # Inject failures
    print(f"Injecting failures into {n_tasks} success tasks (seed={seed})...")
    injected_data = inject_failures(raw_data, n=n_tasks, seed=seed)
    print(f"Successfully injected {len(injected_data)} tasks.")
    
    # Save data
    output_path = save_injected_data(injected_data)
    print(f"Saved injected data to: {output_path}")
    
    print("T009a completed successfully.")


if __name__ == "__main__":
    main()