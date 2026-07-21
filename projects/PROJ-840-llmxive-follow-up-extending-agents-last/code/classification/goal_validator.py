import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

def validate_static_constraints(task_description: str) -> Dict[str, Any]:
    """
    Validates static constraints in the task description using regex patterns.
    Implements Spec FR-007.
    """
    constraints = {
        "ids": [],
        "files": [],
        "paths": [],
        "variables": []
    }
    
    # Pattern for IDs (word + digits)
    id_pattern = r'\b(\w+\d+)\b'
    id_matches = re.findall(id_pattern, task_description)
    constraints["ids"] = list(set(id_matches))
    
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
    parser = argparse.ArgumentParser(description="Validate static constraints in task descriptions")
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
    
    processed_traces = process_traces(traces)
    
    # Extract just the constraints for the report
    constraints_report = [t.get('static_constraints') for t in processed_traces]
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(constraints_report, f, indent=2)
    
    print(f"Static constraints validated and saved to {output_path}")

if __name__ == "__main__":
    main()
