"""
Terminal-Bench-Evo Dataset Availability Verifier and Generator.

This module verifies the availability of the 'Terminal-Bench-Evo' dataset.
It attempts to download from verified canonical sources (Hugging Face).
If the download fails or the dataset is unavailable, it generates a synthetic
subset with explicit state patches and version updates as a fallback.
"""
import json
import random
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Attempt to import datasets; if missing, we will handle the ImportError
# to trigger the synthetic fallback immediately.
try:
    from datasets import load_dataset
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def read_sample_size_from_research_md() -> int:
    """
    Reads the sample_size from research.md.
    Returns default (50) if file is missing or key not found.
    """
    research_path = PROJECT_ROOT / "specs" / "001-evoconflict-filtering" / "research.md"
    default_size = 50

    if not research_path.exists():
        return default_size

    try:
        content = research_path.read_text()
        for line in content.splitlines():
            if line.strip().startswith("sample_size:"):
                # Handle potential markdown formatting or comments
                val = line.split(":", 1)[1].strip().split("#")[0].strip()
                return int(val)
    except (ValueError, IndexError):
        pass

    return default_size


def generate_synthetic_benchmark_tasks(n_tasks: int, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generates a synthetic subset of Terminal-Bench-Evo tasks.
    
    Logic:
    - Creates explicit state patches (e.g., file modifications, variable changes).
    - Creates version updates (e.g., "v1.0" -> "v1.1").
    - Ensures diversity in task descriptions.
    
    Args:
        n_tasks: Number of tasks to generate.
        seed: Random seed for reproducibility.
    
    Returns:
        List of task dictionaries.
    """
    random.seed(seed)
    
    tasks = []
    base_commands = [
        "echo 'Initializing state'",
        "cat config.json",
        "ls -la",
        "git status",
        "grep -r 'TODO'",
        "python script.py --verbose"
    ]
    
    states = [
        "User is logged in as admin.",
        "Database connection established.",
        "File system read-only.",
        "Network latency high.",
        "Memory usage at 80%."
    ]
    
    for i in range(n_tasks):
        task_id = f"evo-task-{i:04d}"
        command = random.choice(base_commands)
        current_state = random.choice(states)
        next_state = random.choice(states)
        
        # Ensure next_state is different for a meaningful transition
        while next_state == current_state:
            next_state = random.choice(states)
        
        task = {
            "task_id": task_id,
            "description": f"Perform operation: {command} in state: {current_state}",
            "command": command,
            "current_state": current_state,
            "expected_state_update": next_state,
            "version": f"v1.{i}",
            "is_synthetic": True,
            "metadata": {
                "generated_at": "2023-10-27",
                "source": "synthetic_generator"
            }
        }
        tasks.append(task)
    
    return tasks


def load_real_dataset_sample(n_tasks: int) -> Optional[List[Dict[str, Any]]]:
    """
    Attempts to load a sample from the real 'Terminal-Bench-Evo' dataset.
    
    Tries the canonical Hugging Face dataset identifier.
    Returns None if the dataset is unavailable or the load fails.
    """
    if not HF_AVAILABLE:
        return None
    
    dataset_id = "Terminal-Bench-Evo/terminal-bench-evo"
    
    try:
        # Attempt to load the dataset (streaming for efficiency)
        ds = load_dataset(dataset_id, split="train", streaming=True)
        
        tasks = []
        count = 0
        for item in ds:
            if count >= n_tasks:
                break
            
            # Normalize structure to expected format
            task = {
                "task_id": item.get("task_id", f"real-{count}"),
                "description": item.get("description", "No description"),
                "command": item.get("command", ""),
                "current_state": item.get("state", ""),
                "expected_state_update": item.get("expected_state", ""),
                "version": item.get("version", "v1.0"),
                "is_synthetic": False,
                "metadata": {
                    "source": "huggingface",
                    "dataset_id": dataset_id
                }
            }
            tasks.append(task)
            count += 1
        
        if len(tasks) < n_tasks:
            # If the dataset is smaller than requested, return what we got
            # but this might trigger a fallback in the caller if strict count is needed.
            # For this task, we return the partial list if we got at least one.
            if len(tasks) > 0:
                return tasks
            return None
        
        return tasks
    
    except Exception:
        # Any error (not found, network, permission) -> fallback
        return None


def main():
    """
    Main entry point for T006.
    
    1. Reads sample size from research.md.
    2. Attempts to download real dataset.
    3. If real download fails, generates synthetic tasks.
    4. Writes output to data/raw/terminal_bench_evo.jsonl.
    """
    # Determine output path
    output_dir = PROJECT_ROOT / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "terminal_bench_evo.jsonl"
    
    # 1. Read sample size
    n_tasks = read_sample_size_from_research_md()
    print(f"Target task count: {n_tasks}")
    
    tasks = []
    source_used = "unknown"
    
    # 2. Attempt real download
    print(f"Attempting to load real dataset from canonical source...")
    real_tasks = load_real_dataset_sample(n_tasks)
    
    if real_tasks and len(real_tasks) >= n_tasks:
        tasks = real_tasks
        source_used = "real_huggingface"
        print(f"Successfully loaded {len(tasks)} tasks from real dataset.")
    else:
        # 3. Fallback: Generate synthetic
        print("Real dataset unavailable or insufficient. Generating synthetic fallback.")
        tasks = generate_synthetic_benchmark_tasks(n_tasks)
        source_used = "synthetic_fallback"
        print(f"Generated {len(tasks)} synthetic tasks.")
    
    # 4. Write output
    print(f"Writing dataset to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        for task in tasks:
            f.write(json.dumps(task) + "\n")
    
    print(f"Done. Output written to {output_path} ({source_used})")
    return output_path


if __name__ == "__main__":
    main()
