import json
import os
import sys
import csv
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

class DeltaCalculationError(Exception):
    """Raised when delta calculation fails."""
    pass

def load_benchmark_results(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise DeltaCalculationError(f"Benchmark results file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def calculate_deltas(benchmark_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate deltas between baseline and compressed agent performance.
    Input: List of dicts with 'trace_id', 'baseline_acc', 'compressed_acc'
    Output: List of dicts with 'trace_id', 'baseline_acc', 'compressed_acc', 'delta_acc', 'fidelity_loss'
    """
    deltas = []
    for entry in benchmark_results:
        trace_id = entry.get('trace_id')
        baseline_acc = entry.get('baseline_acc', 0.0)
        compressed_acc = entry.get('compressed_acc', 0.0)
        
        delta_acc = baseline_acc - compressed_acc
        # Fidelity loss is defined as 1 - Compressed Accuracy (loss of fidelity relative to perfect)
        # Or sometimes defined as (Baseline - Compressed). The task says:
        # "Fidelity Loss (1 - Compressed Accuracy)"
        fidelity_loss = 1.0 - compressed_acc
        
        deltas.append({
            'trace_id': trace_id,
            'baseline_acc': baseline_acc,
            'compressed_acc': compressed_acc,
            'delta_acc': delta_acc,
            'fidelity_loss': fidelity_loss
        })
    return deltas

def save_deltas(deltas: List[Dict[str, Any]], output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not deltas:
        # Write empty file with headers if no data
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['trace_id', 'baseline_acc', 'compressed_acc', 'delta_acc', 'fidelity_loss'])
            writer.writeheader()
        return

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['trace_id', 'baseline_acc', 'compressed_acc', 'delta_acc', 'fidelity_loss']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(deltas)

def run_delta_calculation(benchmark_path: Path, output_path: Path):
    results = load_benchmark_results(benchmark_path)
    deltas = calculate_deltas(results)
    save_deltas(deltas, output_path)
    return deltas

def main():
    """
    Main entry point for T035b.
    Computes Edit Accuracy Difference and Fidelity Loss for each trace.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    data_root = project_root / "data"
    
    benchmark_path = data_root / "processed" / "benchmark_results.json"
    output_path = data_root / "processed" / "accuracy_deltas.csv"

    if not benchmark_path.exists():
        raise DeltaCalculationError(f"Benchmark results not found at {benchmark_path}. "
                                    "Please run benchmark.py first.")

    print(f"Calculating deltas from {benchmark_path}...")
    deltas = run_delta_calculation(benchmark_path, output_path)
    print(f"Deltas saved to {output_path}")
    print(f"Calculated {len(deltas)} entries.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
