import json
import os
import sys
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

def load_golden_subset(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Golden subset file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def deep_compare_states(golden_trace: Dict[str, Any], reconstructed_trace: Dict[str, Any]) -> Tuple[bool, float]:
    """
    Compares golden and reconstructed states to calculate accuracy.
    """
    golden_state = golden_trace.get('step_state', {})
    reconstructed_state = reconstructed_trace.get('step_state', {})
    
    # Compare files
    golden_files = {f['path']: f for f in golden_state.get('files', [])}
    reconstructed_files = {f['path']: f for f in reconstructed_state.get('files', [])}
    
    file_matches = 0
    total_files = len(golden_files)
    
    for path, golden_file in golden_files.items():
        if path in reconstructed_files:
            rec_file = reconstructed_files[path]
            if (golden_file['content'] == rec_file['content'] and 
                golden_file['deleted'] == rec_file['deleted']):
                file_matches += 1
    
    file_accuracy = file_matches / total_files if total_files > 0 else 1.0
    
    # Compare variables
    golden_vars = {v['name']: v for v in golden_state.get('variables', [])}
    reconstructed_vars = {v['name']: v for v in reconstructed_state.get('variables', [])}
    
    var_matches = 0
    total_vars = len(golden_vars)
    
    for name, golden_var in golden_vars.items():
        if name in reconstructed_vars:
            rec_var = reconstructed_vars[name]
            if (golden_var['value'] == rec_var['value'] and 
                golden_var['type'] == rec_var['type']):
                var_matches += 1
    
    var_accuracy = var_matches / total_vars if total_vars > 0 else 1.0
    
    # Combined accuracy (weighted average)
    combined_accuracy = (file_accuracy * 0.6 + var_accuracy * 0.4)
    
    is_accurate = combined_accuracy >= 0.95
    
    return is_accurate, combined_accuracy

def calculate_reconstruction_accuracy(golden_traces: List[Dict[str, Any]], reconstructed_traces: List[Dict[str, Any]]) -> float:
    """
    Calculates the overall reconstruction accuracy across all traces.
    """
    if not golden_traces or not reconstructed_traces:
        return 0.0
    
    golden_map = {t['trace_id']: t for t in golden_traces}
    total_accuracy = 0.0
    count = 0
    
    for trace in reconstructed_traces:
        trace_id = trace.get('trace_id')
        if trace_id in golden_map:
            golden_trace = golden_map[trace_id]
            _, accuracy = deep_compare_states(golden_trace, trace)
            total_accuracy += accuracy
            count += 1
    
    return total_accuracy / count if count > 0 else 0.0

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate state reconstruction against golden subset")
    parser.add_argument("--golden", type=str, default="data/raw/golden_subset.json", help="Golden subset JSON")
    parser.add_argument("--input", type=str, default="data/processed/classified_traces.json", help="Input reconstructed traces JSON")
    parser.add_argument("--output", type=str, default="data/processed/reconstruction_accuracy.json", help="Output accuracy JSON")
    
    args = parser.parse_args()
    golden_path = Path(args.golden)
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not golden_path.exists():
        print(f"Error: Golden file not found: {golden_path}")
        sys.exit(1)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    golden_traces = load_golden_subset(golden_path)
    
    with open(input_path, 'r') as f:
        reconstructed_traces = json.load(f)
    
    accuracy = calculate_reconstruction_accuracy(golden_traces, reconstructed_traces)
    
    result = {
        "reconstruction_accuracy": accuracy,
        "threshold": 0.95,
        "passed": accuracy >= 0.95
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Reconstruction accuracy: {accuracy:.4f}")
    print(f"Threshold: 0.95")
    print(f"Passed: {result['passed']}")
    
    if not result['passed']:
        sys.exit(1)

if __name__ == "__main__":
    main()
