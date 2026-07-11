import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

@dataclass
class ForgettingResult:
    condition: str
    initial_accuracy: float
    final_accuracy: float
    accuracy_drop: float
    forgetting_rate: float
    run_id: str

@dataclass
class RetentionMetrics:
    condition: str
    rule_id: str
    initial_accuracy: float
    final_accuracy: float
    retention_rate: float
    run_id: str

def calculate_accuracy_drop(initial_acc: float, final_acc: float) -> float:
    """Calculate the absolute drop in accuracy."""
    return max(0.0, initial_acc - final_acc)

def calculate_retention_rate(initial_acc: float, final_acc: float) -> float:
    """
    Calculate retention rate as the proportion of initial performance retained.
    Formula: final / initial (clamped to [0, 1] if initial > 0).
    Returns 0.0 if initial is 0 to avoid division by zero.
    """
    if initial_acc <= 0:
        return 0.0
    rate = final_acc / initial_acc
    return max(0.0, min(1.0, rate))

def load_agent_results(results_dir: Path, condition: str) -> List[Dict[str, Any]]:
    """
    Load results for a specific condition from the results directory.
    Expects files named like: run_{run_id}_{condition}.json
    """
    results = []
    if not results_dir.exists():
        return results
    
    for file_path in results_dir.glob(f"*_ {condition}.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Ensure run_id is captured
                run_id = data.get('run_id', file_path.stem)
                data['run_id'] = run_id
                results.append(data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load {file_path}: {e}")
    return results

def compute_forgetting_metrics(
    results_dir: Path, 
    conditions: List[str]
) -> List[ForgettingResult]:
    """
    Compute forgetting metrics (accuracy drop) for each run across conditions.
    """
    forgetting_data = []
    for condition in conditions:
        runs = load_agent_results(results_dir, condition)
        for run in runs:
            initial_acc = run.get('initial_accuracy', 0.0)
            final_acc = run.get('final_accuracy', 0.0)
            drop = calculate_accuracy_drop(initial_acc, final_acc)
            forgetting_rate = drop / initial_acc if initial_acc > 0 else 0.0
            
            forgetting_data.append(ForgettingResult(
                condition=condition,
                initial_accuracy=initial_acc,
                final_accuracy=final_acc,
                accuracy_drop=drop,
                forgetting_rate=forgetting_rate,
                run_id=run.get('run_id', 'unknown')
            ))
    return forgetting_data

def compute_retention_metrics(
    results_dir: Path,
    conditions: List[str]
) -> List[RetentionMetrics]:
    """
    Compute retention rates for distinct logical rules per run.
    SC-003: Compare Co-evolving vs Mixed-task conditions.
    
    Expects 'rule_performance' in the run data, a dict mapping rule_id to {initial, final} accuracy.
    """
    retention_data = []
    target_conditions = [c for c in conditions if c in ['coevolving', 'mixed']]
    
    if not target_conditions:
        return retention_data

    for condition in target_conditions:
        runs = load_agent_results(results_dir, condition)
        for run in runs:
            rule_perf = run.get('rule_performance', {})
            if not rule_perf:
                # Fallback if structure is flat: look for specific keys
                # Try to infer from keys if 'rule_performance' is missing but rule data exists
                rule_keys = [k for k in run.keys() if k.startswith('rule_')]
                for rule_key in rule_keys:
                    rule_id = rule_key
                    rule_data = run[rule_key]
                    init = rule_data.get('initial', 0.0)
                    final = rule_data.get('final', 0.0)
                    rate = calculate_retention_rate(init, final)
                    retention_data.append(RetentionMetrics(
                        condition=condition,
                        rule_id=rule_id,
                        initial_accuracy=init,
                        final_accuracy=final,
                        retention_rate=rate,
                        run_id=run.get('run_id', 'unknown')
                    ))
                continue

            for rule_id, perf in rule_perf.items():
                init = perf.get('initial', 0.0)
                final = perf.get('final', 0.0)
                rate = calculate_retention_rate(init, final)
                
                retention_data.append(RetentionMetrics(
                    condition=condition,
                    rule_id=rule_id,
                    initial_accuracy=init,
                    final_accuracy=final,
                    retention_rate=rate,
                    run_id=run.get('run_id', 'unknown')
                ))
    
    return retention_data

def save_retention_metrics(
    retention_data: List[RetentionMetrics],
    output_path: Path
) -> None:
    """Save retention metrics to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump([asdict(r) for r in retention_data], f, indent=2)

def main():
    """
    Main entry point to compute and store retention rates for SC-003.
    Reads from data/results/, computes metrics, writes to data/results/retention_metrics.json.
    """
    base_dir = Path(__file__).resolve().parent.parent.parent
    results_dir = base_dir / "data" / "results"
    output_file = base_dir / "data" / "results" / "retention_metrics.json"

    print(f"Loading results from: {results_dir}")
    
    conditions = ['coevolving', 'mixed', 'sequential']
    retention_metrics = compute_retention_metrics(results_dir, conditions)
    
    if not retention_metrics:
        print("Warning: No retention metrics computed. Check if result files contain 'rule_performance'.")
        # Write empty list to indicate completion even if no data found
        save_retention_metrics([], output_file)
        return

    save_retention_metrics(retention_metrics, output_file)
    print(f"Saved retention metrics to: {output_file}")
    print(f"Computed {len(retention_metrics)} rule retention entries.")

    # Summary for Co-evolving vs Mixed
    coevolving_rates = [m.retention_rate for m in retention_metrics if m.condition == 'coevolving']
    mixed_rates = [m.retention_rate for m in retention_metrics if m.condition == 'mixed']
    
    if coevolving_rates and mixed_rates:
        avg_coev = sum(coevolving_rates) / len(coevolving_rates)
        avg_mix = sum(mixed_rates) / len(mixed_rates)
        print(f"Average Retention (Co-evolving): {avg_coev:.4f} (n={len(coevolving_rates)})")
        print(f"Average Retention (Mixed-task): {avg_mix:.4f} (n={len(mixed_rates)})")

if __name__ == "__main__":
    main()