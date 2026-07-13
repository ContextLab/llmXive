"""
Failure Signature Indexer.
Parses injected data and builds a signature index.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from utils.config import get_path

def load_injected_data(input_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Loads the injected failure subset.
    """
    if input_path is None:
        input_path = str(get_path("implicit_failure_subset"))
    
    tasks = []
    with open(input_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                tasks.append(json.loads(line))
    return tasks

def extract_failure_signatures(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extracts failure patterns and maps them to tool identifiers.
    
    Args:
        tasks: List of tasks with injected errors.
        
    Returns:
        Dictionary mapping tool_id to pattern and recovery strategy.
    """
    signatures = {}
    for task in tasks:
        if task.get("injected_error"):
            tool_outputs = task.get("tool_outputs", [])
            for output in tool_outputs:
                if "ERROR" in output:
                    # Extract pattern
                    pattern = output.strip()
                    signatures[pattern] = {
                        "tool_id": "unknown_tool", # Placeholder
                        "recovery_strategy": "replan"
                    }
    return signatures

def build_failure_index(signatures: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds the final failure index structure.
    """
    return signatures

def save_index(index: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Saves the failure index to a JSON file.
    """
    if output_path is None:
        output_path = str(get_path("failure_signatures"))
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(index, f, indent=2)
    
    return output_path

def main():
    """
    Main entry point for building the index.
    """
    tasks = load_injected_data()
    signatures = extract_failure_signatures(tasks)
    index = build_failure_index(signatures)
    path = save_index(index)
    print(f"Failure index saved to {path}")

if __name__ == "__main__":
    main()
