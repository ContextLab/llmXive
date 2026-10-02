import os
import csv
import json
import hashlib
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Importing tree-sitter for parsing validation if needed, though primary ingestion is from HF
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' library is required. Install it via 'pip install datasets'."
    )

# Constants for paths
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

def load_swe_bench(subset: str = "verified") -> Any:
    """
    Loads the SWE-bench dataset from HuggingFace.
    
    Args:
        subset: The specific subset to load (e.g., 'verified', 'all').
    
    Returns:
        The loaded dataset object.
    
    Raises:
        Exception: If the dataset cannot be fetched.
    """
    try:
        # Using streaming to handle large datasets efficiently if needed, 
        # but loading to memory for processing is standard for this pipeline stage
        # unless explicitly streaming for stats.
        ds = load_dataset("princeton-nlp/SWE-bench", split="train")
        # Filter if a specific subset is requested (implementation detail depends on HF schema)
        # For now, assuming standard load. If 'verified' is a specific filter key:
        if subset == "verified":
            # SWE-bench verified is often a specific split or filter
            # Assuming standard split 'train' contains the data, filtering by 'verified' column if exists
            # or using a specific config. Adjust based on actual HF card.
            # Standard SWE-bench on HF usually has 'train' split.
            pass 
        return ds
    except Exception as e:
        raise RuntimeError(f"Failed to load SWE-bench dataset: {e}")

def load_agent_bench() -> Any:
    """
    Loads the AgentBench dataset from HuggingFace.
    
    Returns:
        The loaded dataset object.
    
    Raises:
        Exception: If the dataset cannot be fetched.
    """
    try:
        ds = load_dataset("THUDM/AgentBench", "osbench", split="train")
        return ds
    except Exception as e:
        raise RuntimeError(f"Failed to load AgentBench dataset: {e}")

def parse_swe_bench(dataset: Any) -> List[Dict[str, Any]]:
    """
    Parses the SWE-bench dataset into the standard internal format.
    
    Args:
        dataset: The loaded HuggingFace dataset.
    
    Returns:
        List of dictionaries containing task_id, code_diff, original_code, etc.
    """
    parsed_tasks = []
    
    # Iterate through the dataset
    for item in dataset:
        task_id = item.get("instance_id")
        if not task_id:
            continue
        
        # Extract relevant fields based on SWE-bench schema
        # Assuming 'patch' is the diff and 'repo'/'base_commit' are context
        code_diff = item.get("patch", "")
        original_code = item.get("repo", "") # Placeholder if 'repo' is path, usually we need the code context
        
        # If 'base_commit' or 'repo' code is needed, it might be fetched separately
        # For this ingestion task, we focus on the diff and ID.
        
        # Ensure we have the necessary fields
        if not code_diff:
            # Handle cases where diff might be missing or empty
            code_diff = ""
        
        parsed_tasks.append({
            "task_id": str(task_id),
            "code_diff": str(code_diff),
            "original_code": str(original_code),
            "source": "swe_bench",
            "status": "parsed" # Default status, will be updated later
        })
    
    return parsed_tasks

def parse_agent_bench(dataset: Any) -> List[Dict[str, Any]]:
    """
    Parses the AgentBench dataset into the standard internal format.
    
    Args:
        dataset: The loaded HuggingFace dataset.
    
    Returns:
        List of dictionaries containing task_id, code_diff, original_code, etc.
    """
    parsed_tasks = []
    
    for item in dataset:
        # AgentBench schema might differ. Assuming 'id' or similar.
        task_id = item.get("id") or item.get("instance_id")
        if not task_id:
            continue
        
        code_diff = item.get("diff", item.get("patch", ""))
        original_code = item.get("original_code", "")
        
        if not code_diff:
            code_diff = ""
        
        parsed_tasks.append({
            "task_id": str(task_id),
            "code_diff": str(code_diff),
            "original_code": str(original_code),
            "source": "agent_bench",
            "status": "parsed"
        })
    
    return parsed_tasks

def merge_datasets(swe_tasks: List[Dict], agent_tasks: List[Dict]) -> List[Dict[str, Any]]:
    """
    Merges parsed tasks from both sources into a single list.
    
    Args:
        swe_tasks: List of parsed SWE-bench tasks.
        agent_tasks: List of parsed AgentBench tasks.
    
    Returns:
        Combined list of tasks.
    """
    return swe_tasks + agent_tasks

def write_to_csv(tasks: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Writes the list of tasks to a CSV file.
    
    Args:
        tasks: List of task dictionaries.
        output_path: Path to the output CSV file.
    """
    if not tasks:
        raise ValueError("No tasks to write to CSV.")
    
    # Define fieldnames based on expected columns
    fieldnames = ["task_id", "code_diff", "original_code", "source", "status"]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for task in tasks:
            # Ensure all keys are present, fill with empty string if missing
            row = {k: task.get(k, "") for k in fieldnames}
            writer.writerow(row)

def write_to_json(tasks: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Writes the list of tasks to a JSON file.
    
    Args:
        tasks: List of task dictionaries.
        output_path: Path to the output JSON file.
    """
    with open(output_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(tasks, jsonfile, indent=2)

def main():
    """
    Main entry point for the ingestion script.
    Downloads datasets, parses them, and saves to data/raw and data/processed.
    """
    print("Starting data ingestion...")
    
    # Ensure directories exist
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Load SWE-bench
    print("Loading SWE-bench dataset...")
    try:
        swe_dataset = load_swe_bench()
    except Exception as e:
        print(f"Error loading SWE-bench: {e}")
        sys.exit(1)
    
    # 2. Load AgentBench
    print("Loading AgentBench dataset...")
    try:
        agent_dataset = load_agent_bench()
    except Exception as e:
        print(f"Error loading AgentBench: {e}")
        sys.exit(1)
    
    # 3. Parse datasets
    print("Parsing SWE-bench...")
    swe_tasks = parse_swe_bench(swe_dataset)
    print(f"Parsed {len(swe_tasks)} SWE-bench tasks.")
    
    print("Parsing AgentBench...")
    agent_tasks = parse_agent_bench(agent_dataset)
    print(f"Parsed {len(agent_tasks)} AgentBench tasks.")
    
    # 4. Merge datasets
    all_tasks = merge_datasets(swe_tasks, agent_tasks)
    print(f"Total tasks merged: {len(all_tasks)}")
    
    # 5. Save raw parquet (simulated as json/csv for now if parquet lib not strictly enforced, 
    #    but tasks.md asks for parquet. We will save as json for raw intermediate if parquet writer is heavy,
    #    or use pandas if available. Let's assume pandas is available as per requirements.txt.)
    try:
        import pandas as pd
        df_raw = pd.DataFrame(all_tasks)
        df_raw.to_parquet(RAW_DIR / "swe_bench_subset.parquet", index=False)
        # Note: AgentBench might be separate or merged. Tasks.md says "swe_bench_subset" and "agentbench_subset".
        # We will split them back for the specific files or save the combined one.
        # Let's save the specific subsets as requested.
        
        df_swe = pd.DataFrame(swe_tasks)
        df_swe.to_parquet(RAW_DIR / "swe_bench_subset.parquet", index=False)
        
        df_agent = pd.DataFrame(agent_tasks)
        df_agent.to_parquet(RAW_DIR / "agentbench_subset.parquet", index=False)
        
    except ImportError:
        # Fallback to JSON if pandas not available (though requirements.txt says it is)
        write_to_json(swe_tasks, RAW_DIR / "swe_bench_subset.json")
        write_to_json(agent_tasks, RAW_DIR / "agentbench_subset.json")
        print("Pandas not found, saved as JSON.")
    
    # 6. Write intermediate CSV (ground_truth.csv will be generated by baseline_runner later)
    # For now, write a preliminary CSV with status 'pending'
    print("Writing intermediate ground truth CSV...")
    write_to_csv(all_tasks, PROCESSED_DIR / "ground_truth.csv")
    
    print("Ingestion complete.")

if __name__ == "__main__":
    main()
