import re
import json
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any

# Hardcoded template mapping for natural language constraints (FR-007)
# Maps natural language keywords to deterministic constraint templates
CONSTRAINT_TEMPLATES = {
    "must not": {"action": "delete", "constraint": "forbidden"},
    "must delete": {"action": "delete", "constraint": "required"},
    "must create": {"action": "create", "constraint": "required"},
    "must not create": {"action": "create", "constraint": "forbidden"},
    "must modify": {"action": "modify", "constraint": "required"},
    "must not modify": {"action": "modify", "constraint": "forbidden"},
    "must read": {"action": "read", "constraint": "required"},
    "must not read": {"action": "read", "constraint": "forbidden"},
    "forbidden": {"action": "any", "constraint": "forbidden"},
    "required": {"action": "any", "constraint": "required"},
}

def validate_static_constraints(task_description: str) -> Dict[str, Any]:
    """
    Validates static constraints in the task description using regex patterns
    and deterministic template matching.
    Implements Spec FR-007.
    """
    constraints = {
        "ids": [],
        "files": [],
        "paths": [],
        "variables": [],
        "semantic_constraints": []
    }
    
    # Pattern for IDs (word + digits) - strictly per FR-007
    # Using \w+_?\d+ to capture both "task_123" and "task123" styles if they exist
    id_pattern = r'\b(\w+_\d+)\b'
    id_matches = re.findall(id_pattern, task_description)
    constraints["ids"] = list(set(id_matches))
    
    # Fallback pattern if underscore is missing but digits are present
    id_pattern_fallback = r'\b(\w+\d+)\b'
    id_matches_fallback = re.findall(id_pattern_fallback, task_description)
    # Filter out the ones already caught by the primary pattern to avoid duplicates
    for match in id_matches_fallback:
        if match not in constraints["ids"] and not any(match.startswith(p) for p in constraints["ids"]):
            # Only add if it looks like an ID (has digits) and isn't a common word
            if any(c.isdigit() for c in match):
                constraints["ids"].append(match)
    
    constraints["ids"] = list(set(constraints["ids"]))
    
    # Pattern for file/path constraints
    file_pattern = r'\b(file|path|var):\s*(\S+)\b'
    file_matches = re.findall(file_pattern, task_description, re.IGNORECASE)
    for match in file_matches:
        if match[0].lower() == 'file':
            constraints["files"].append(match[1])
        elif match[0].lower() == 'path':
            constraints["paths"].append(match[1])
        elif match[0].lower() == 'var':
            constraints["variables"].append(match[1])
    
    # Deterministic template matching for natural language constraints
    lower_desc = task_description.lower()
    for phrase, template in CONSTRAINT_TEMPLATES.items():
        if phrase in lower_desc:
            # Extract the target object if possible (e.g., "must not delete X")
            # Simple heuristic: look for the word following the phrase
            pattern = re.escape(phrase) + r'\s+(\w+)'
            target_matches = re.findall(pattern, lower_desc)
            for target in target_matches:
                constraint_entry = template.copy()
                constraint_entry["target"] = target
                constraint_entry["source_phrase"] = phrase
                constraints["semantic_constraints"].append(constraint_entry)
    
    return constraints

def process_traces(traces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Processes a list of traces and validates static constraints for each.
    """
    processed = []
    for trace in traces:
        task_description = trace.get('task_description', '')
        constraints = validate_static_constraints(task_description)
        
        processed_trace = trace.copy()
        processed_trace['static_constraints'] = constraints
        processed.append(processed_trace)
    
    return processed

def main():
    parser = argparse.ArgumentParser(description="Validate static constraints in task descriptions (FR-007)")
    parser.add_argument("--input", type=str, default="data/raw/golden_subset.json", help="Input traces JSON")
    parser.add_argument("--output", type=str, default="data/processed/static_constraints.json", help="Output constraints JSON")
    
    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    with open(input_path, 'r') as f:
        traces = json.load(f)
    
    if not isinstance(traces, list):
        # If the file is a single object, wrap it or try to handle it
        # Assuming the expected format is a list of traces
        print(f"Warning: Input file does not contain a list. Attempting to process as single item.")
        traces = [traces]
    
    processed_traces = process_traces(traces)
    
    # Extract just the constraints for the report
    constraints_report = [t.get('static_constraints') for t in processed_traces]
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(constraints_report, f, indent=2)
    
    print(f"Static constraints validated and saved to {output_path}")
    print(f"Processed {len(traces)} traces.")

if __name__ == "__main__":
    main()