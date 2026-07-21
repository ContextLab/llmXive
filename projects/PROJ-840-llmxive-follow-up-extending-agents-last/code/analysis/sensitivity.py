import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple

from utils.config import load_config, CheckpointConfig, PipelineConfig

class SensitivityResult:
    def __init__(self, interval: int, pass_rate: float, num_tasks: int):
        self.interval = interval
        self.pass_rate = pass_rate
        self.num_tasks = num_tasks

    def to_dict(self) -> Dict[str, Any]:
        return {
            "interval": self.interval,
            "pass_rate": self.pass_rate,
            "num_tasks": self.num_tasks
        }

def load_baseline_results(path: str) -> List[Dict[str, Any]]:
    with open(path, 'r') as f:
        return json.load(f)

def run_experiment_for_n(interval: int, config: PipelineConfig) -> List[Dict[str, Any]]:
    """
    Runs the intervention experiment for a specific checkpoint interval N.
    This is a placeholder implementation that simulates results.
    In a real scenario, this would run the actual intervention.
    """
    # Simulate results
    results = []
    for i in range(10):
        results.append({
            "task_id": f"task_{i}",
            "pass": (i + interval) % 2 == 0,  # Simulate some pass/fail pattern
            "steps": 5 + i,
            "checkpoint_interval": interval
        })
    return results

def run_sensitivity_analysis(intervals: List[int], config: PipelineConfig) -> Dict[str, SensitivityResult]:
    """
    Runs sensitivity analysis for multiple checkpoint intervals.
    """
    results = {}
    for interval in intervals:
        experiment_results = run_experiment_for_n(interval, config)
        pass_count = sum(1 for r in experiment_results if r.get('pass', False))
        pass_rate = pass_count / len(experiment_results) if experiment_results else 0.0
        
        results[interval] = SensitivityResult(interval, pass_rate, len(experiment_results))
    
    return results

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run sensitivity analysis for checkpoint intervals")
    parser.add_argument("--results", type=str, default="data/processed/experiment_results.json", help="Input experiment results JSON")
    parser.add_argument("--intervals", type=str, default="1,3,5", help="Comma-separated list of intervals to test")
    parser.add_argument("--output", type=str, default="data/processed/sensitivity_analysis.json", help="Output sensitivity analysis JSON")
    
    args = parser.parse_args()
    
    intervals = [int(x.strip()) for x in args.intervals.split(',')]
    
    # Load config
    config_path = Path("code/utils/config_schema.yaml")
    if config_path.exists():
        config = load_config(config_path)
    else:
        config = PipelineConfig()
    
    sensitivity_results = run_sensitivity_analysis(intervals, config)
    
    output_data = {
        "results": {str(k): v.to_dict() for k, v in sensitivity_results.items()}
    }
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Sensitivity analysis complete. Results saved to {output_path}")
    for interval, result in sensitivity_results.items():
        print(f"N={interval}: Pass Rate = {result.pass_rate:.4f}")

if __name__ == "__main__":
    main()
