"""
Calculate adherence rate for the dual-track agent and compare against threshold.
Implements T035 requirements.

Logic:
1. Load execution traces from data/processed/execution_traces.csv.
2. Filter for dual-track architecture.
3. Filter out rows where violation_reason is "implicit_unverified" (as per task spec).
4. Calculate adherence rate: (total remaining tasks - tasks with violations) / total remaining tasks.
5. Compare against SC-004 threshold of >85%.
6. Write results to data/processed/adherence_verification.json.
"""
import os
import sys
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import get_paths

def load_execution_traces(file_path: Path) -> List[Dict[str, Any]]:
    """Load execution traces from CSV file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Execution traces file not found: {file_path}")
    
    traces = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            traces.append(row)
    return traces

def calculate_adherence_rate(traces: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate adherence rate for dual-track agent.
    
    Adherence is defined as: (total dual-track tasks - tasks with violations) / total dual-track tasks.
    Per T035 spec: Filter out rows where violation_reason is "implicit_unverified" before calculating.
    """
    # 1. Filter for dual-track architecture
    dual_track_traces = [t for t in traces if t.get('architecture') == 'dual_track']
    
    if not dual_track_traces:
        return {
            'total_tasks': 0,
            'tasks_with_violations': 0,
            'adherence_rate': 0.0,
            'threshold': 0.85,
            'pass': False,
            'note': 'No dual-track traces found'
        }
    
    # 2. Filter out rows where violation_reason is "implicit_unverified"
    # These are cases where the rule-based resolver failed to match a constraint.
    # They are excluded from the adherence calculation as per T035 logic.
    filtered_traces = [
        t for t in dual_track_traces 
        if t.get('violation_reason') != 'implicit_unverified'
    ]
    
    if not filtered_traces:
        # If all traces were filtered out (e.g., all were implicit_unverified)
        return {
            'total_tasks': 0,
            'tasks_with_violations': 0,
            'adherence_rate': 0.0,
            'threshold': 0.85,
            'pass': False,
            'note': 'All dual-track traces were filtered out as implicit_unverified'
        }

    total_tasks = len(filtered_traces)
    
    # 3. Count tasks with violations
    # violation_boolean is a string in CSV, need to check for 'True' or '1'
    tasks_with_violations = sum(
        1 for t in filtered_traces 
        if t.get('violation_boolean', 'False').lower() in ['true', '1']
    )
    
    # 4. Calculate adherence rate
    adherence_rate = (total_tasks - tasks_with_violations) / total_tasks if total_tasks > 0 else 0.0
    
    # 5. Compare against SC-004 threshold (> 85%)
    threshold = 0.85
    pass_threshold = adherence_rate > threshold
    
    return {
        'total_tasks': total_tasks,
        'tasks_with_violations': tasks_with_violations,
        'adherence_rate': float(adherence_rate),
        'threshold': float(threshold),
        'pass': pass_threshold
    }

def main():
    """Main entry point for adherence verification."""
    paths = get_paths()
    
    # Define input and output paths
    # The task spec says to read from data/processed/execution_traces.csv
    traces_path = paths.data_processed / "execution_traces.csv"
    output_path = paths.data_processed / "adherence_verification.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading execution traces from: {traces_path}")
    if not traces_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {traces_path}. "
            "Please ensure T027 (execution traces generation) has been run successfully."
        )
    
    traces = load_execution_traces(traces_path)
    
    print(f"Calculating adherence rate for {len(traces)} traces...")
    result = calculate_adherence_rate(traces)
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    print(f"Adherence verification results written to: {output_path}")
    print(f"  Total Dual-Track Tasks (excl. implicit_unverified): {result['total_tasks']}")
    print(f"  Tasks with Violations: {result['tasks_with_violations']}")
    print(f"  Adherence Rate: {result['adherence_rate']:.2%}")
    print(f"  Threshold (SC-004): {result['threshold']:.2%}")
    print(f"  Pass: {result['pass']}")

if __name__ == "__main__":
    main()