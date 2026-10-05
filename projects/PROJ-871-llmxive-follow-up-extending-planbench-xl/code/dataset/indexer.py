import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from utils.config import get_path, ensure_dirs_exist

def load_injected_data(input_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load the injected failure subset."""
    if input_path is None:
        input_path = get_path('data/derived/implicit_failure_subset.jsonl')
    
    if not input_path.exists():
        raise FileNotFoundError(f"Injected data not found at {input_path}")
    
    data = []
    with open(input_path, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def extract_failure_signatures(data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Extract failure patterns and map to tool identifiers."""
    signatures = {}
    
    for item in data:
        if item.get('injected_error_pattern'):
            error_type = item.get('injected_error_type', 'unknown_error')
            tool_id = f"tool_{hash(error_type) % 1000}"  # Deterministic tool ID
            
            if tool_id not in signatures:
                signatures[tool_id] = {
                    'tool_id': tool_id,
                    'pattern_string': error_type,
                    'recovery_strategy': 'replan'
                }
    
    return list(signatures.values())

def build_failure_index(signatures: List[Dict[str, str]]) -> Dict[str, str]:
    """Build a lookup index from tool_id to pattern."""
    return {sig['tool_id']: sig['pattern_string'] for sig in signatures}

def save_index(index_data: List[Dict[str, str]], output_path: Optional[Path] = None) -> Path:
    """Save the failure signature index."""
    if output_path is None:
        output_path = get_path('data/derived/failure_signatures.json')
    
    ensure_dirs_exist(output_path.parent)
    
    with open(output_path, 'w') as f:
        json.dump(index_data, f, indent=2)
    
    return output_path

def main():
    """Main entry point for failure indexer."""
    injected_data = load_injected_data()
    signatures = extract_failure_signatures(injected_data)
    output_file = save_index(signatures)
    print(f"Failure signatures index saved to: {output_file}")

if __name__ == "__main__":
    main()
