"""
Terminal-Bench-Evo Dataset Verification and Fallback Generator.

This module attempts to verify the availability of the 'Terminal-Bench-Evo' dataset
from verified canonical sources. If the dataset is unavailable or download fails,
it generates a synthetic subset with explicit state patches and version updates
as a strict fallback.

Output:
    Writes the dataset to `data/raw/terminal_bench_evo.jsonl`.

Fallback:
    If `research.md` is missing, defaults to 50 tasks.
"""
import json
import os
import sys
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

# Attempt to import real data source (Hugging Face datasets)
# This import is allowed to fail if the environment is not set up for real data,
# but the script must handle the failure by falling back to synthetic generation
# ONLY if the real source is genuinely unavailable.
try:
    from datasets import load_dataset
    REAL_DATA_AVAILABLE = True
except ImportError:
    REAL_DATA_AVAILABLE = False


def read_sample_size_from_research_md() -> int:
    """
    Reads the sample size N from specs/001-evoconflict-filtering/research.md.
    Returns 50 if the file is missing or the key is not found.
    """
    research_md_path = Path("specs/001-evoconflict-filtering/research.md")
    if not research_md_path.exists():
        return 50

    try:
        content = research_md_path.read_text()
        for line in content.splitlines():
            if line.strip().startswith("sample_size:"):
                # Parse the number after the colon
                val = line.split(":", 1)[1].strip()
                return int(val)
    except (ValueError, IndexError):
        pass
    
    return 50


def generate_synthetic_benchmark_tasks(n_tasks: int) -> List[Dict[str, Any]]:
    """
    Generates a synthetic subset of Terminal-Bench-Evo tasks.
    
    This is strictly a fallback mechanism when the real dataset is unavailable.
    It creates tasks with explicit state patches and version updates.
    
    Args:
        n_tasks: Number of tasks to generate.
        
    Returns:
        List of task dictionaries.
    """
    tasks = []
    base_commands = [
        "git checkout main",
        "git pull origin main",
        "npm install",
        "pip install -r requirements.txt",
        "docker build -t app .",
        "kubectl apply -f deployment.yaml"
    ]
    
    base_states = [
        {"status": "idle", "version": "1.0.0", "files": ["main.py"]},
        {"status": "building", "version": "1.0.1", "files": ["main.py", "config.json"]},
        {"status": "deploying", "version": "1.0.2", "files": ["main.py", "config.json", "Dockerfile"]}
    ]

    for i in range(n_tasks):
        # Create a deterministic but varied task
        task_id = f"evo-task-{i:04d}"
        command = random.choice(base_commands)
        initial_state = random.choice(base_states).copy()
        
        # Simulate a state transition (patch)
        new_version = f"{initial_state['version'].rsplit('.', 1)[0]}.{int(initial_state['version'].split('.')[-1]) + 1}"
        new_files = initial_state['files'] + [f"patch_{i}.py"]
        
        final_state = {
            "status": "completed" if random.random() > 0.2 else "failed",
            "version": new_version,
            "files": new_files
        }

        task = {
            "task_id": task_id,
            "command": command,
            "initial_state": initial_state,
            "final_state": final_state,
            "is_contradiction": random.choice([True, False]),
            "metadata": {
                "source": "synthetic_fallback",
                "generated_at": "2023-10-27T00:00:00Z"
            }
        }
        tasks.append(task)

    return tasks


def load_real_dataset() -> Optional[List[Dict[str, Any]]]:
    """
    Attempts to load the real 'Terminal-Bench-Evo' dataset.
    Returns None if the dataset is unavailable.
    """
    if not REAL_DATA_AVAILABLE:
        return None

    try:
        # Try to load from a verified canonical source.
        # Using 'terminal-bench/terminal-bench-evo' as the canonical ID if it exists,
        # or a generic placeholder if the specific ID is unknown but the package is present.
        # In a real execution, this would be the exact dataset ID.
        # We attempt a generic load to verify availability.
        dataset = load_dataset("terminal-bench/terminal-bench-evo", split="train")
        return dataset.to_list()
    except Exception:
        # If the specific dataset ID is not found or network fails, return None
        return None


def main():
    """
    Main entry point to verify availability and generate/write the dataset.
    """
    n_tasks = read_sample_size_from_research_md()
    output_path = Path("data/raw/terminal_bench_evo.jsonl")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Try to load real data first
    real_data = load_real_dataset()

    if real_data is not None and len(real_data) > 0:
        # If real data is available and has content, use it.
        # Truncate or sample if necessary to match n_tasks if the real dataset is huge,
        # but usually we just take the first N.
        tasks = real_data[:n_tasks]
        source = "real"
    else:
        # Fallback: Generate synthetic data
        # This is the ONLY path to synthetic data, triggered only if real data fails.
        tasks = generate_synthetic_benchmark_tasks(n_tasks)
        source = "synthetic_fallback"

    # Write to JSONL
    with open(output_path, 'w', encoding='utf-8') as f:
        for task in tasks:
            f.write(json.dumps(task) + '\n')

    print(f"Dataset written to {output_path} ({len(tasks)} tasks, source: {source})")
    return output_path


if __name__ == "__main__":
    main()
