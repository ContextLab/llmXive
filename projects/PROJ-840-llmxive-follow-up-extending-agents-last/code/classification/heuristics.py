from typing import Any, Dict, Union
import re
from pathlib import Path
import math

def normalize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes the state according to the protocol:
    (a) Compare floating-point values with a tolerance of 1e-6
    (b) Strip timestamps and random IDs
    (c) Canonicalize object references
    """
    normalized = {}
    
    for key, value in state.items():
        if isinstance(value, dict):
            normalized[key] = normalize_state(value)
        elif isinstance(value, list):
            normalized[key] = [normalize_state(item) if isinstance(item, dict) else item for item in value]
        elif isinstance(value, float):
            # Round to 6 decimal places for tolerance comparison
            normalized[key] = round(value, 6)
        elif isinstance(value, str):
            # Strip timestamps (e.g., 2023-01-01T12:00:00)
            value = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', '', value)
            # Strip random IDs (e.g., abc123def456)
            value = re.sub(r'\b[a-f0-9]{12,}\b', '', value)
            # Canonicalize object references (e.g., obj_1 -> obj)
            value = re.sub(r'_\d+\b', '', value)
            normalized[key] = value.strip()
        else:
            normalized[key] = value
    
    return normalized

def deep_normalize_states(states: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalizes a list of states.
    """
    return [normalize_state(state) for state in states]

def main():
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Normalize states for comparison")
    parser.add_argument("--input", type=str, help="Input JSON file with states")
    parser.add_argument("--output", type=str, help="Output JSON file with normalized states")
    
    args = parser.parse_args()
    
    if not args.input or not args.output:
        print("Usage: python heuristics.py --input <input.json> --output <output.json>")
        sys.exit(1)
    
    with open(args.input, 'r') as f:
        states = json.load(f)
    
    normalized_states = deep_normalize_states(states)
    
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(normalized_states, f, indent=2)
    
    print(f"Normalized states saved to {args.output}")

if __name__ == "__main__":
    main()
