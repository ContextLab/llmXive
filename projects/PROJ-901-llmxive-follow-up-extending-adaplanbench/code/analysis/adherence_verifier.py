"""
Calculate adherence rate for the dual-track agent and compare against threshold.
Implements T031b requirements.
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
    Adherence is defined as: (total dual-track tasks - tasks with violations) / total dual-track tasks
    """
    dual_track_traces = [t for t in traces if t['architecture'] == 'dual_track']
    
    if not dual_track_traces:
        return {
            'total_tasks': 0,
            'tasks_with_violations': 0,
            'adherence_rate': 0.0,
            'pass': False
        }
    
    total_tasks = len(dual_track_traces)
    tasks_with_violations = sum(
        1 for t in dual_track_traces 
        if t.get('violation_boolean', 'False').lower() in ['true', '1']
    )
    
    adherence_rate = (total_tasks - tasks_with_violations) / total_tasks if total_tasks > 0 else 0.0
    
    # Threshold from SC-004: > 85%
    threshold = 0.85
    pass_threshold = adherence_rate > threshold
    
    return {
        'total_tasks': total_tasks,
        'tasks_with_violations': tasks_with_violations,
        'adherence_rate': adherence_rate,
        'threshold': threshold,
        'pass': pass_threshold
    }

def main():
    """Main entry point for adherence verification."""
    paths = get_paths()
    
    # Define input and output paths
    traces_path = paths.data_processed / "execution_traces.csv"
    output_path = paths.data_processed / "adherence_verification.json"
    
    print(f"Loading execution traces from: {traces_path}")
    traces = load_execution_traces(traces_path)
    
    print(f"Calculating adherence rate for {len(traces)} traces...")
    result = calculate_adherence_rate(traces)
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    print(f"Adherence verification results written to: {output_path}")
    print(f"  Total Dual-Track Tasks: {result['total_tasks']}")
    print(f"  Tasks with Violations: {result['tasks_with_violations']}")
    print(f"  Adherence Rate: {result['adherence_rate']:.2%}")
    print(f"  Threshold: {result['threshold']:.2%}")
    print(f"  Pass: {result['pass']}")

if __name__ == "__main__":
    main()
