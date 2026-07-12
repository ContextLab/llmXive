"""
Sensitivity analysis module for User Story 3.

Tests the impact of checkpointing interval (N) on task pass rates.
Specifically evaluates N=1, N=3, and N=5 as required by FR-006.

This module re-runs the experiment logic for each N value by invoking
the intervention runner with the specific checkpoint interval configuration.
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from utils.logging_config import get_logger
from utils.config import load_config, CheckpointConfig, PipelineConfig
from intervention.runner import CPUOnlyRunner, ExecutionResult
from intervention.wrapper import ContextCheckpointWrapper

# Ensure project root is in path
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

logger = get_logger(__name__)

@dataclass
class SensitivityResult:
    """Result container for a single sensitivity analysis run."""
    n_interval: int
    total_tasks: int
    passed_tasks: int
    failed_tasks: int
    pass_rate: float
    execution_time_seconds: float
    memory_peak_mb: float
    output_file: str

def load_baseline_results() -> Dict[str, Any]:
    """
    Load baseline results from T023 to compare against.
    """
    baseline_path = Path("data/processed/baseline_results.json")
    if not baseline_path.exists():
        raise FileNotFoundError(
            f"Baseline results not found at {baseline_path}. "
            "Run T023 first to generate baseline data."
        )
    with open(baseline_path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_experiment_for_n(n_value: int, config: PipelineConfig) -> Dict[str, Any]:
    """
    Run the intervention experiment for a specific checkpoint interval N.
    
    This simulates the T023 logic but with a specific N value injected
    into the checkpoint configuration.
    """
    logger.info(f"Starting experiment run for N={n_value}")
    
    # Load the dataset defined in T015/T023
    data_path = Path("data/raw/golden_subset.json")
    if not data_path.exists():
        # Fallback to generated data if T015 hasn't run yet, though T023 should have
        raise FileNotFoundError(f"Task dataset not found at {data_path}")
    
    with open(data_path, "r", encoding="utf-8") as f:
        tasks = json.load(f)
    
    if not tasks:
        raise ValueError("Task dataset is empty.")
    
    # Configure the wrapper for this specific N
    # We assume the config loader can be updated or we override the interval
    checkpoint_config = CheckpointConfig(
        interval=n_value,
        model_path=config.model_config.model_path,
        compression_threshold=500
    )
    
    # Create runner and wrapper
    runner = CPUOnlyRunner(config.model_config.model_path)
    wrapper = ContextCheckpointWrapper(
        runner=runner,
        config=checkpoint_config
    )
    
    results = []
    start_time = time.time()
    total_memory = 0.0
    
    for task in tasks:
        try:
            # Execute task with intervention
            result: ExecutionResult = wrapper.run_task(task)
            results.append({
                "task_id": task.get("trace_id", "unknown"),
                "passed": result.passed,
                "steps": result.steps_executed,
                "checkpoint_count": result.checkpoints_applied,
                "memory_mb": result.memory_mb
            })
            total_memory = max(total_memory, result.memory_mb)
        except Exception as e:
            logger.error(f"Task {task.get('trace_id')} failed with exception: {e}")
            results.append({
                "task_id": task.get("trace_id", "unknown"),
                "passed": False,
                "steps": 0,
                "checkpoint_count": 0,
                "memory_mb": 0.0,
                "error": str(e)
            })
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    passed_count = sum(1 for r in results if r["passed"])
    total_count = len(results)
    pass_rate = passed_count / total_count if total_count > 0 else 0.0
    
    return {
        "n_interval": n_value,
        "total_tasks": total_count,
        "passed_tasks": passed_count,
        "failed_tasks": total_count - passed_count,
        "pass_rate": pass_rate,
        "execution_time_seconds": execution_time,
        "memory_peak_mb": total_memory,
        "task_details": results
    }

def run_sensitivity_analysis(config_path: str = "code/utils/config_schema.yaml") -> List[SensitivityResult]:
    """
    Execute sensitivity analysis for N=1, N=3, and N=5.
    
    Returns a list of SensitivityResult objects.
    """
    logger.info("Starting sensitivity analysis for intervals [1, 3, 5]")
    
    # Load base configuration
    config = load_config(config_path)
    
    # Ensure output directory exists
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    n_values = [1, 3, 5]
    
    for n in n_values:
        logger.info(f"Processing interval N={n}")
        
        # Run experiment
        raw_result = run_experiment_for_n(n, config)
        
        # Save individual result file
        output_file = output_dir / f"sensitivity_n_{n}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(raw_result, f, indent=2)
        
        # Create structured result
        sens_result = SensitivityResult(
            n_interval=raw_result["n_interval"],
            total_tasks=raw_result["total_tasks"],
            passed_tasks=raw_result["passed_tasks"],
            failed_tasks=raw_result["failed_tasks"],
            pass_rate=raw_result["pass_rate"],
            execution_time_seconds=raw_result["execution_time_seconds"],
            memory_peak_mb=raw_result["memory_peak_mb"],
            output_file=str(output_file)
        )
        results.append(sens_result)
        
        logger.info(
            f"N={n}: Pass Rate = {sens_result.pass_rate:.4f} "
            f"({sens_result.passed_tasks}/{sens_result.total_tasks})"
        )
    
    # Generate summary report
    summary_path = output_dir / "sensitivity_analysis_summary.json"
    summary_data = {
        "intervals_tested": n_values,
        "results": [
            {
                "n": r.n_interval,
                "pass_rate": r.pass_rate,
                "passed": r.passed_tasks,
                "total": r.total_tasks,
                "execution_time": r.execution_time_seconds,
                "memory_mb": r.memory_peak_mb
            }
            for r in results
        ],
        "variation": {
            "min_pass_rate": min(r.pass_rate for r in results),
            "max_pass_rate": max(r.pass_rate for r in results),
            "range": max(r.pass_rate for r in results) - min(r.pass_rate for r in results)
        }
    }
    
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    
    logger.info(f"Sensitivity analysis complete. Summary saved to {summary_path}")
    return results

def main():
    """Entry point for sensitivity analysis."""
    try:
        results = run_sensitivity_analysis()
        
        print("\n" + "="*50)
        print("SENSITIVITY ANALYSIS RESULTS")
        print("="*50)
        print(f"{'Interval (N)':<15} {'Pass Rate':<15} {'Passed':<10} {'Total':<10}")
        print("-" * 50)
        for r in results:
            print(f"{r.n_interval:<15} {r.pass_rate:<15.4f} {r.passed_tasks:<10} {r.total_tasks:<10}")
        print("="*50)
        
        return 0
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
