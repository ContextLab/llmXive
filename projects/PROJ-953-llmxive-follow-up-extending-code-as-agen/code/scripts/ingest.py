import os
import csv
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from datasets import load_dataset

# Ensure output directories exist
OUTPUT_DIR = Path("data/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_swe_bench() -> List[Dict[str, Any]]:
    """
    Load SWE-bench dataset from HuggingFace.
    Returns a list of dictionaries containing task data.
    """
    try:
        # Load the lite version for faster processing in CI/limited environments
        # If full dataset is needed, change 'lite' to 'default'
        ds = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
        return list(ds)
    except Exception as e:
        raise RuntimeError(f"Failed to load SWE-bench from HuggingFace: {e}")

def load_agent_bench() -> List[Dict[str, Any]]:
    """
    Load AgentBench dataset from HuggingFace.
    Returns a list of dictionaries containing task data.
    """
    try:
        # AgentBench is a multi-task benchmark. We focus on the 'human' subset
        # or a specific subset relevant to code generation if available.
        # Using the main repository dataset.
        ds = load_dataset("THUDM/AgentBench", "human", split="test")
        return list(ds)
    except Exception as e:
        raise RuntimeError(f"Failed to load AgentBench from HuggingFace: {e}")

def parse_swe_bench(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parse SWE-bench raw data into the unified schema.
    SWE-bench Schema:
    - instance_id: unique identifier
    - repo: repository path
    - base_commit: commit hash
    - problem_statement: natural language description
    - test_patch: the test code to verify the fix
    - patch: the solution patch (if available in ground truth, otherwise empty)
    - model_name_or_path: usually empty in raw dataset
    """
    parsed = []
    for item in raw_data:
        record = {
            "task_id": item.get("instance_id", ""),
            "dataset": "swe-bench",
            "repo": item.get("repo", ""),
            "base_commit": item.get("base_commit", ""),
            "problem_statement": item.get("problem_statement", ""),
            "code_diff": item.get("test_patch", ""), # Using test_patch as the diff context
            "original_code": "", # SWE-bench raw doesn't always provide full original code in one field
            "metadata": json.dumps({
                "base_commit": item.get("base_commit"),
                "repo": item.get("repo")
            })
        }
        parsed.append(record)
    return parsed

def parse_agent_bench(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parse AgentBench raw data into the unified schema.
    AgentBench Schema (Human subset):
    - id: unique identifier
    - question: natural language description
    - code: the solution code (if available)
    - test_code: the test code
    - context: additional context
    """
    parsed = []
    for item in raw_data:
        # AgentBench structure varies by sub-task. Assuming 'human' subset structure.
        # We treat 'code' as the diff/solution and 'test_code' as the verification.
        # If 'code' is missing, we might need to construct a diff or leave it empty.
        solution_code = item.get("code", "")
        test_code = item.get("test_code", "")
        
        # Construct a simple diff representation if we have both
        # In a real scenario, we might need to diff against a base. 
        # Here we store the solution code as the 'code_diff' for ingestion purposes.
        # If the task requires the diff between base and solution, we would need the base.
        # For this ingestion step, we store the provided code.
        
        record = {
            "task_id": item.get("id", ""),
            "dataset": "agent-bench",
            "repo": "", # AgentBench human subset often doesn't have a git repo path
            "base_commit": "",
            "problem_statement": item.get("question", ""),
            "code_diff": solution_code,
            "original_code": "", # Not explicitly provided in the same way
            "metadata": json.dumps({
                "context": item.get("context", ""),
                "source": "agent-bench-human"
            })
        }
        parsed.append(record)
    return parsed

def merge_datasets(swe_data: List[Dict[str, Any]], agent_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge parsed datasets into a single unified list.
    """
    merged = []
    merged.extend(swe_data)
    merged.extend(agent_data)
    
    # Optional: Deduplicate by task_id if any overlap exists (unlikely between these two)
    seen_ids = set()
    unique_merged = []
    for item in merged:
        if item["task_id"] not in seen_ids:
            seen_ids.add(item["task_id"])
            unique_merged.append(item)
    
    return unique_merged

def write_to_csv(data: List[Dict[str, Any]], output_path: Path):
    """
    Write the unified dataset to a CSV file.
    """
    if not data:
        raise ValueError("No data to write. Ingestion might have failed.")
    
    fieldnames = list(data[0].keys())
    
    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def main():
    """
    Main entry point for the ingestion script.
    Downloads SWE-bench and AgentBench, parses them, merges, and writes to CSV.
    """
    print("Starting dataset ingestion...")
    
    # 1. Load SWE-bench
    print("Loading SWE-bench...")
    raw_swe = load_swe_bench()
    print(f"Loaded {len(raw_swe)} SWE-bench items.")
    
    # 2. Parse SWE-bench
    print("Parsing SWE-bench...")
    parsed_swe = parse_swe_bench(raw_swe)
    
    # 3. Load AgentBench
    print("Loading AgentBench...")
    raw_agent = load_agent_bench()
    print(f"Loaded {len(raw_agent)} AgentBench items.")
    
    # 4. Parse AgentBench
    print("Parsing AgentBench...")
    parsed_agent = parse_agent_bench(raw_agent)
    
    # 5. Merge
    print("Merging datasets...")
    merged = merge_datasets(parsed_swe, parsed_agent)
    print(f"Merged dataset contains {len(merged)} tasks.")
    
    # 6. Write to CSV
    output_path = OUTPUT_DIR / "ingested_tasks.csv"
    print(f"Writing unified dataset to {output_path}...")
    write_to_csv(merged, output_path)
    
    print("Ingestion complete.")

if __name__ == "__main__":
    main()