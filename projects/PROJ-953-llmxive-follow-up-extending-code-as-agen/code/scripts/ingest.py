"""
Ingests SWE-bench and AgentBench datasets from HuggingFace,
parses them according to their distinct schemas, and merges
them into a unified dataset.
"""
import os
import csv
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

from datasets import load_dataset

# Output paths relative to project root
OUTPUT_DIR = Path("data/raw")
OUTPUT_CSV = OUTPUT_DIR / "unified_tasks.csv"


def load_swe_bench() -> List[Dict[str, Any]]:
    """
    Downloads and returns the SWE-bench dataset from HuggingFace.
    Uses the 'lite' split for efficiency if available, otherwise full.
    """
    try:
        # Using the lite version which is smaller and sufficient for initial runs
        # If the full dataset is required, change 'lite' to 'test' or 'dev'
        dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
        return list(dataset)
    except Exception as e:
        raise RuntimeError(f"Failed to load SWE-bench from HuggingFace: {e}")


def load_agent_bench() -> List[Dict[str, Any]]:
    """
    Downloads and returns the AgentBench dataset from HuggingFace.
    Specifically targets the 'osbench' or general coding tasks if available.
    Note: AgentBench structure varies; this targets the standard coding benchmark.
    """
    try:
        # Using the standard AgentBench dataset
        dataset = load_dataset("THUDM/AgentBench", split="osbench")
        return list(dataset)
    except Exception as e:
        # Fallback to other splits if osbench fails, or raise
        try:
            dataset = load_dataset("THUDM/AgentBench", split="dev")
            return list(dataset)
        except Exception as e2:
            raise RuntimeError(f"Failed to load AgentBench from HuggingFace: {e2}")


def parse_swe_bench(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parses raw SWE-bench data into the unified schema.
    
    SWE-bench Schema:
    - instance_id: str
    - repo: str
    - base_commit: str
    - patch: str (the solution diff)
    - test_patch: str (test suite diff)
    - problem_statement: str
    - instance_id is the unique key.
    """
    parsed = []
    for item in raw_data:
        # Construct a unique ID if not present (should be present)
        task_id = str(item.get("instance_id", ""))
        if not task_id:
            continue

        # Extract code diff (the proposed solution)
        code_diff = item.get("patch", "")
        
        # Extract original code context if available, otherwise empty
        # SWE-bench usually requires dynamic execution to verify, 
        # so we store the diff and the problem statement.
        # We don't have 'original_code' directly in the lite split, 
        # but we can derive context from the repo or store the diff as the primary artifact.
        # For this pipeline, 'original_code' is often reconstructed during execution.
        original_code = "" 

        parsed.append({
            "task_id": task_id,
            "source": "swe-bench",
            "repo": item.get("repo", ""),
            "base_commit": item.get("base_commit", ""),
            "problem_statement": item.get("problem_statement", ""),
            "code_diff": code_diff,
            "original_code": original_code,
            "test_patch": item.get("test_patch", ""),
            "metadata": json.dumps(item) # Store raw item for debugging
        })
    return parsed


def parse_agent_bench(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parses raw AgentBench data into the unified schema.
    
    AgentBench Schema (varies by split):
    - question_id / id
    - question / instruction
    - code / solution
    - environment / setup info
    """
    parsed = []
    for item in raw_data:
        # Identify task ID
        task_id = str(item.get("question_id", item.get("id", "")))
        if not task_id:
            continue

        # AgentBench often provides the solution directly as 'code' or 'answer'
        # We treat the solution as the 'code_diff' relative to an empty/original state,
        # or we parse the instruction to find the diff if provided.
        # For simplicity in this pipeline, we store the solution code as the diff.
        code_diff = item.get("code", item.get("answer", ""))
        original_code = item.get("original_code", "") # Often not provided in raw benchmark

        # Construct problem statement from instruction
        problem_statement = item.get("question", item.get("instruction", ""))

        parsed.append({
            "task_id": task_id,
            "source": "agent-bench",
            "repo": "", # AgentBench often doesn't have a git repo
            "base_commit": "",
            "problem_statement": problem_statement,
            "code_diff": code_diff,
            "original_code": original_code,
            "test_patch": "", # AgentBench evaluation is usually internal
            "metadata": json.dumps(item)
        })
    return parsed


def merge_datasets(swe_parsed: List[Dict[str, Any]], agent_parsed: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merges the two parsed datasets into a single list.
    Ensures no duplicate task_ids (though unlikely between sources).
    """
    all_tasks = swe_parsed + agent_parsed
    
    # Deduplicate by task_id just in case
    seen_ids = set()
    unique_tasks = []
    for task in all_tasks:
        if task["task_id"] not in seen_ids:
            seen_ids.add(task["task_id"])
            unique_tasks.append(task)
    
    return unique_tasks


def write_to_csv(tasks: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Writes the unified task list to a CSV file.
    Columns: task_id, source, repo, base_commit, problem_statement, code_diff, original_code, test_patch
    """
    if not tasks:
        raise ValueError("No tasks to write. The datasets were empty or parsing failed.")

    # Define columns
    fieldnames = [
        "task_id", "source", "repo", "base_commit", 
        "problem_statement", "code_diff", "original_code", "test_patch"
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for task in tasks:
            # Ensure all fields are strings to avoid CSV errors
            row = {k: str(v) if v is not None else "" for k, v in task.items() if k in fieldnames}
            writer.writerow(row)

    print(f"Successfully wrote {len(tasks)} tasks to {output_path}")


def main():
    """
    Main entry point for the ingestion script.
    """
    print("Starting dataset ingestion...")
    
    # 1. Load raw data from HuggingFace
    print("Loading SWE-bench...")
    swe_raw = load_swe_bench()
    print(f"Loaded {len(swe_raw)} SWE-bench items.")

    print("Loading AgentBench...")
    agent_raw = load_agent_bench()
    print(f"Loaded {len(agent_raw)} AgentBench items.")

    # 2. Parse distinct schemas
    print("Parsing SWE-bench...")
    swe_parsed = parse_swe_bench(swe_raw)

    print("Parsing AgentBench...")
    agent_parsed = parse_agent_bench(agent_raw)

    # 3. Merge datasets
    print("Merging datasets...")
    unified_tasks = merge_datasets(swe_parsed, agent_parsed)
    print(f"Total unified tasks: {len(unified_tasks)}")

    # 4. Write to CSV
    print("Writing to CSV...")
    write_to_csv(unified_tasks, OUTPUT_CSV)

    print("Ingestion complete.")


if __name__ == "__main__":
    main()