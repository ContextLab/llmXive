from typing import Any, Dict, Union
import re
from pathlib import Path
import math
import hashlib
import sys

def normalize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes the state according to the protocol:
    (a) Compare floating-point values with a tolerance of 1e-6
    (b) Strip timestamps and random IDs
    (c) Canonicalize object references (memory addresses, UUIDs) to a hash of their content
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
            
            # T046: Canonicalize object references (memory addresses, UUIDs) to a hash of their content
            # Pattern 1: Memory addresses (e.g., 0x7f8b...)
            # Pattern 2: UUIDs (e.g., 550e8400-e29b-41d4-a716-446655440000)
            # Pattern 3: Ephemeral IDs (e.g., obj_123, var_456) - already handled by generic ID stripping below, 
            # but we need to ensure content-based hashing for complex references
            
            # First, identify and replace memory addresses
            # Format: 0x followed by hex digits
            def replace_memory_address(match):
                # In a real scenario, we would look up the content associated with this address.
                # Since we only have the string representation here, we hash the match itself 
                # to ensure consistency if the same address appears multiple times in the same context,
                # but ideally, the caller should provide the content.
                # For this implementation, we hash the address string to create a stable canonical ID.
                # Note: In a full state reconstruction, we would map '0x123' -> content_of_obj_123
                # and then hash the content. Here we hash the address string as a placeholder for content.
                addr = match.group(0)
                return f"canonical_{hashlib.sha256(addr.encode()).hexdigest()[:8]}"

            value = re.sub(r'0x[0-9a-fA-F]+', replace_memory_address, value)
            
            # Identify and replace UUIDs
            # Format: standard UUID with hyphens
            def replace_uuid(match):
                uuid = match.group(0)
                return f"canonical_{hashlib.sha256(uuid.encode()).hexdigest()[:8]}"
            
            value = re.sub(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', replace_uuid, value)

            # Canonicalize object references (e.g., obj_123 -> canonical_hash)
            # This handles patterns like "obj_1", "var_456" where the number is an ephemeral ID
            def replace_obj_ref(match):
                ref = match.group(0)
                return f"canonical_{hashlib.sha256(ref.encode()).hexdigest()[:8]}"
            
            value = re.sub(r'\b\w+_\d+\b', replace_obj_ref, value)
            
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