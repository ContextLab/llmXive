import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.config import get_path


def load_injected_data() -> List[Dict[str, Any]]:
    """
    Load the implicit failure subset from the derived data directory.
    
    Returns:
        List of dictionaries representing the injected failure tasks.
        
    Raises:
        FileNotFoundError: If the implicit_failure_subset.jsonl file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON lines.
    """
    file_path = get_path("data", "derived", "implicit_failure_subset.jsonl")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Required input file not found: {file_path}. "
            "Please run T009a (injector.py) to generate this file first."
        )
    
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON on line {line_num} in {file_path}", 
                    e.doc, 
                    e.pos
                )
    
    if not data:
        raise ValueError(f"No valid data found in {file_path}")
        
    return data


def extract_failure_signatures(injected_data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Extract failure signatures from the injected data.
    
    This function parses the injected error patterns, maps them to tool identifiers,
    and assigns a default recovery strategy.
    
    Args:
        injected_data: List of task dictionaries containing injected error information.
        
    Returns:
        List of signature dictionaries with keys: tool_id, pattern, recovery_strategy.
    """
    signatures = {}
    
    for task in injected_data:
        if not task.get("injected_error", False):
            continue
        
        # Extract the error pattern from the tool output or specific field
        # Based on T009a description, the error is appended as 'ERROR: silent_tool_failure'
        # We look for this pattern in the tool outputs
        
        tool_outputs = task.get("tool_outputs", [])
        task_id = task.get("task_id", "unknown")
        
        for output in tool_outputs:
            tool_id = output.get("tool_id", "unknown_tool")
            content = output.get("content", "")
            
            # Check for the injected error pattern
            if "ERROR: silent_tool_failure" in content:
                # Create a signature key based on the tool and the error pattern
                # We use the specific error string as the pattern
                pattern = "ERROR: silent_tool_failure"
                
                if tool_id not in signatures:
                    signatures[tool_id] = {
                        "tool_id": tool_id,
                        "pattern": pattern,
                        "recovery_strategy": "replan"
                    }
    
    # Convert to list format
    return list(signatures.values())


def build_failure_index(signatures: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    """
    Build a failure index dictionary from the extracted signatures.
    
    Args:
        signatures: List of signature dictionaries.
        
    Returns:
        Dictionary mapping tool_id to signature details for fast lookup.
    """
    index = {}
    for sig in signatures:
        tool_id = sig.get("tool_id")
        if tool_id:
            index[tool_id] = {
                "pattern": sig.get("pattern", ""),
                "recovery_strategy": sig.get("recovery_strategy", "replan")
            }
    return index


def save_index(index_data: Dict[str, Dict[str, str]], output_path: Optional[str] = None) -> str:
    """
    Save the failure index to a JSON file.
    
    Args:
        index_data: The failure index dictionary to save.
        output_path: Optional path to save the file. If None, uses the default path.
        
    Returns:
        The path where the file was saved.
        
    Raises:
        IOError: If the file cannot be written.
    """
    if output_path is None:
        output_path = get_path("data", "derived", "failure_signatures.json")
    
    # Ensure the directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        raise IOError(f"Failed to write failure index to {output_path}: {e}")
    
    return output_path


def main() -> None:
    """
    Main entry point for the indexer script.
    
    This function orchestrates the loading of injected data, extraction of
    failure signatures, building of the index, and saving to disk.
    """
    print("Starting failure signature index construction...")
    
    try:
        # Step 1: Load injected data
        print("Loading injected failure data...")
        injected_data = load_injected_data()
        print(f"Loaded {len(injected_data)} tasks with injected errors.")
        
        # Step 2: Extract signatures
        print("Extracting failure signatures...")
        signatures = extract_failure_signatures(injected_data)
        print(f"Extracted {len(signatures)} unique failure signatures.")
        
        if not signatures:
            print("Warning: No failure signatures found in the injected data.")
            # Still create an empty index to satisfy the requirement
            index_data = {}
        else:
            # Step 3: Build index
            print("Building failure index...")
            index_data = build_failure_index(signatures)
        
        # Step 4: Save index
        print("Saving failure index...")
        output_path = save_index(index_data)
        print(f"Successfully saved failure signatures to: {output_path}")
        
        # Summary
        print("\n--- Index Summary ---")
        print(f"Total signatures indexed: {len(index_data)}")
        for tool_id, details in index_data.items():
            print(f"  - {tool_id}: {details['pattern']} (Strategy: {details['recovery_strategy']})")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure T009a (injector.py) has been run successfully to generate the input file.")
        raise
    except Exception as e:
        print(f"Unexpected error during indexing: {e}")
        raise


if __name__ == "__main__":
    main()