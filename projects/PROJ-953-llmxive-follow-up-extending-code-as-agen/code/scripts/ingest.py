import os
import csv
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

from datasets import load_dataset


def load_swe_bench() -> List[Dict[str, Any]]:
    """
    Load SWE-bench dataset from HuggingFace.
    Returns a list of dictionaries containing the raw dataset entries.
    """
    try:
        # Using the lite version to ensure it fits within compute constraints
        # while still providing real data.
        dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="train")
        return list(dataset)
    except Exception as e:
        raise RuntimeError(f"Failed to load SWE-bench from HuggingFace: {e}")


def load_agent_bench() -> List[Dict[str, Any]]:
    """
    Load AgentBench dataset from HuggingFace.
    Returns a list of dictionaries containing the raw dataset entries.
    """
    try:
        # Loading the LLM-as-a-judge subset which contains executable tasks
        dataset = load_dataset("THUDM/AgentBench", "llm", split="train")
        return list(dataset)
    except Exception as e:
        raise RuntimeError(f"Failed to load AgentBench from HuggingFace: {e}")


def parse_swe_bench(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parse SWE-bench entries into the unified schema.
    
    SWE-bench Schema:
    - instance_id: str
    - repo: str
    - problem_statement: str
    - base_commit: str
    - patch: str (the solution diff)
    - test_patch: str (the test suite diff)
    - instance_relevant: bool (optional filter)
    
    Output Unified Schema:
    - task_id: str (derived from instance_id)
    - source: "swe_bench"
    - original_code: str (context, often empty in SWE-bench but we store the repo info)
    - code_diff: str (the patch)
    - task_description: str (problem_statement)
    - metadata: dict (json string of remaining fields)
    """
    parsed = []
    for entry in raw_data:
        # SWE-bench specific logic
        task_id = entry.get("instance_id", "unknown")
        patch = entry.get("patch", "")
        problem_statement = entry.get("problem_statement", "")
        
        # SWE-bench usually provides the patch as the solution, 
        # but for "original_code" we might need to fetch from repo if available.
        # For this ingestion step, we store the repo context in metadata.
        original_code = "" # SWE-bench lite doesn't always provide full file content in the row
        
        parsed_entry = {
            "task_id": f"swe_{task_id}",
            "source": "swe_bench",
            "original_code": original_code,
            "code_diff": patch,
            "task_description": problem_statement,
            "metadata": json.dumps({
                "repo": entry.get("repo"),
                "base_commit": entry.get("base_commit"),
                "test_patch": entry.get("test_patch", ""),
                "version": entry.get("version")
            })
        }
        parsed.append(parsed_entry)
    
    return parsed


def parse_agent_bench(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parse AgentBench entries into the unified schema.
    
    AgentBench Schema (LLM subset):
    - id: str
    - task: str (description)
    - input: str (initial state/code)
    - output: str (expected solution/code)
    - type: str (e.g., "code_generation")
    
    Output Unified Schema:
    - task_id: str
    - source: "agent_bench"
    - original_code: str (input)
    - code_diff: str (output - treated as the target diff/solution)
    - task_description: str
    - metadata: dict
    """
    parsed = []
    for entry in raw_data:
        task_id = entry.get("id", "unknown")
        input_code = entry.get("input", "")
        output_code = entry.get("output", "")
        task_desc = entry.get("task", "")
        
        # For AgentBench, the "diff" is conceptually the transformation from input to output.
        # Since we are ingesting for ground truth generation later, we treat the output
        # as the target code change.
        
        parsed_entry = {
            "task_id": f"agent_{task_id}",
            "source": "agent_bench",
            "original_code": input_code,
            "code_diff": output_code,
            "task_description": task_desc,
            "metadata": json.dumps({
                "type": entry.get("type"),
                "subtask": entry.get("subtask")
            })
        }
        parsed.append(parsed_entry)
    
    return parsed


def merge_datasets(swe_parsed: List[Dict[str, Any]], agent_parsed: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge parsed datasets into a single list.
    """
    return swe_parsed + agent_parsed


def write_to_csv(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write the unified dataset to a CSV file.
    """
    if not data:
        raise ValueError("No data to write to CSV.")
    
    # Define standard columns
    fieldnames = ["task_id", "source", "original_code", "code_diff", "task_description", "metadata"]
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def main():
    """
    Main entry point for the ingestion script.
    Downloads SWE-bench and AgentBench, parses them, merges, and saves to CSV.
    """
    # Configuration
    output_dir = Path("data/raw")
    output_file = output_dir / "ingested_tasks.csv"
    
    print("Starting dataset ingestion...")
    
    # 1. Load SWE-bench
    print("Loading SWE-bench...")
    swe_raw = load_swe_bench()
    print(f"Loaded {len(swe_raw)} SWE-bench entries.")
    
    # 2. Load AgentBench
    print("Loading AgentBench...")
    agent_raw = load_agent_bench()
    print(f"Loaded {len(agent_raw)} AgentBench entries.")
    
    # 3. Parse
    print("Parsing SWE-bench...")
    swe_parsed = parse_swe_bench(swe_raw)
    
    print("Parsing AgentBench...")
    agent_parsed = parse_agent_bench(agent_raw)
    
    # 4. Merge
    print("Merging datasets...")
    unified_data = merge_datasets(swe_parsed, agent_parsed)
    print(f"Total unified entries: {len(unified_data)}")
    
    # 5. Write
    print(f"Writing to {output_file}...")
    write_to_csv(unified_data, output_file)
    
    print(f"Ingestion complete. Output saved to {output_file}")


if __name__ == "__main__":
    main()