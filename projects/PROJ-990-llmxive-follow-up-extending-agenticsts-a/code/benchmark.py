import os
import sys
import time
import json
import logging
import tracemalloc
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Tuple

# Import existing pipeline components to benchmark
from parser import main as parser_main, parse_trajectories
from splitter import main as splitter_main, stratified_split
from ablation import main as ablation_main, run_ablation_study
from classifier import main as classifier_main, run_training
from simulator import main as simulator_main, run_dynamic_simulation
from stats import main as stats_main, compute_aggregates

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/benchmark_debug.log')
    ]
)
logger = logging.getLogger(__name__)

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    if tracemalloc.is_tracing():
        current, peak = tracemalloc.get_traced_memory()
        return current / 1024 / 1024
    return 0.0

def run_phase_benchmark(
    phase_name: str,
    phase_func: Callable,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """
    Run a single phase of the pipeline and benchmark its execution.
    
    Args:
        phase_name: Name of the phase for logging
        phase_func: Function to execute
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Dictionary with benchmark results for this phase
    """
    logger.info(f"Starting benchmark for phase: {phase_name}")
    
    start_time = time.time()
    start_memory = get_memory_usage_mb()
    
    success = False
    error_msg = None
    result = None
    
    try:
        # Execute the phase function
        result = phase_func(*args, **kwargs)
        success = True
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Phase {phase_name} failed with error: {e}")
        raise
    finally:
        end_time = time.time()
        end_memory = get_memory_usage_mb()
        
    duration = end_time - start_time
    memory_delta = end_memory - start_memory
    
    phase_result = {
        "phase_name": phase_name,
        "duration_seconds": round(duration, 3),
        "start_memory_mb": round(start_memory, 2),
        "end_memory_mb": round(end_memory, 2),
        "memory_delta_mb": round(memory_delta, 2),
        "success": success,
        "error": error_msg
    }
    
    logger.info(f"Phase {phase_name} completed in {duration:.3f}s (Memory: {memory_delta:.2f}MB)")
    return phase_result

def benchmark_parser_phase(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Benchmark the parser phase."""
    if config is None:
        config = {
            "raw_data_dir": "data/raw",
            "output_file": "data/processed/metrics_with_moves.csv"
        }
    return run_phase_benchmark("Parser", parser_main, config)

def benchmark_splitter_phase(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Benchmark the splitter phase."""
    if config is None:
        config = {
            "input_file": "data/processed/metrics_with_moves.csv",
            "output_dir": "data/processed"
        }
    return run_phase_benchmark("Splitter", splitter_main, config)

def benchmark_ablation_phase(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Benchmark the ablation phase."""
    if config is None:
        config = {
            "dataset_path": "data/processed/ablation_train_set.csv",
            "output_dir": "data/processed"
        }
    return run_phase_benchmark("Ablation", ablation_main, config)

def benchmark_classifier_phase(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Benchmark the classifier training phase."""
    if config is None:
        config = {
            "labels_path": "data/processed/ablation_labels_train.json",
            "model_output": "models/layer_utility_classifier.pkl"
        }
    return run_phase_benchmark("Classifier", classifier_main, config)

def benchmark_simulation_phase(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Benchmark the simulation phase."""
    if config is None:
        config = {
            "test_set_path": "data/processed/test_set.csv",
            "model_path": "models/layer_utility_classifier.pkl",
            "output_file": "data/processed/simulation_logs_dynamic.json"
        }
    return run_phase_benchmark("Simulation", simulator_main, config)

def benchmark_stats_phase(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Benchmark the statistics phase."""
    if config is None:
        config = {
            "dynamic_log": "data/processed/simulation_logs_dynamic.json",
            "static_log": "data/processed/simulation_logs_static.json",
            "output_file": "data/processed/statistical_results.json"
        }
    return run_phase_benchmark("Statistics", stats_main, config)

def run_full_benchmark(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Run the full pipeline benchmark, measuring each phase and total runtime.
    
    Args:
        config: Optional configuration dictionary for all phases
        
    Returns:
        Complete benchmark report dictionary
    """
    if config is None:
        config = {}
        
    logger.info("Starting full pipeline benchmark")
    
    # Start memory tracing
    tracemalloc.start()
    benchmark_start = datetime.now().isoformat()
    start_memory = get_memory_usage_mb()
    
    phases = []
    successful_phases = 0
    failed_phases = 0
    
    # Define the pipeline phases in order
    phase_functions = [
        ("Parser", benchmark_parser_phase, config.get("parser", {})),
        ("Splitter", benchmark_splitter_phase, config.get("splitter", {})),
        ("Ablation", benchmark_ablation_phase, config.get("ablation", {})),
        ("Classifier", benchmark_classifier_phase, config.get("classifier", {})),
        ("Simulation", benchmark_simulation_phase, config.get("simulation", {})),
        ("Statistics", benchmark_stats_phase, config.get("stats", {})),
    ]
    
    for phase_name, phase_func, phase_config in phase_functions:
        try:
            result = run_phase_benchmark(phase_name, phase_func, phase_config)
            phases.append(result)
            if result["success"]:
                successful_phases += 1
            else:
                failed_phases += 1
        except Exception as e:
            logger.error(f"Phase {phase_name} failed: {e}")
            phases.append({
                "phase_name": phase_name,
                "duration_seconds": 0,
                "start_memory_mb": 0,
                "end_memory_mb": 0,
                "memory_delta_mb": 0,
                "success": False,
                "error": str(e)
            })
            failed_phases += 1
            # Continue to next phase even if one fails
    
    # End memory tracing
    end_memory = get_memory_usage_mb()
    tracemalloc.stop()
    
    total_duration = time.time() - start_time if 'start_time' in locals() else 0
    total_memory_delta = end_memory - start_memory
    
    # Build the complete report
    report = {
        "benchmark_start": benchmark_start,
        "total_duration_seconds": round(total_duration, 3),
        "start_memory_mb": round(start_memory, 2),
        "end_memory_mb": round(end_memory, 2),
        "total_memory_delta_mb": round(total_memory_delta, 2),
        "phases": phases,
        "summary": {
            "total_phases": len(phases),
            "successful_phases": successful_phases,
            "failed_phases": failed_phases,
            "success_rate": round(successful_phases / len(phases), 2) if phases else 0.0,
            "total_duration_hours": round(total_duration / 3600, 4),
            "within_6_hour_limit": total_duration < 6 * 3600
        }
    }
    
    logger.info(f"Benchmark completed: {successful_phases}/{len(phases)} phases successful")
    logger.info(f"Total runtime: {total_duration:.3f}s ({total_duration/3600:.4f}h)")
    
    return report

def save_benchmark_report(report: Dict[str, Any], output_path: str = "data/processed/benchmark_log.json") -> None:
    """
    Save the benchmark report to a JSON file.
    
    Args:
        report: The benchmark report dictionary
        output_path: Path to save the JSON file
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Benchmark report saved to {output_path}")

def main(config: Dict[str, Any] = None) -> None:
    """
    Main entry point for the benchmark script.
    
    Args:
        config: Optional configuration dictionary
    """
    logger.info("Running benchmark script...")
    
    try:
        report = run_full_benchmark(config)
        save_benchmark_report(report)
        logger.info("Benchmark completed successfully")
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        # Still try to save a partial report
        error_report = {
            "benchmark_start": datetime.now().isoformat(),
            "total_duration_seconds": 0,
            "error": str(e),
            "phases": [],
            "summary": {
                "total_phases": 0,
                "successful_phases": 0,
                "failed_phases": 0,
                "success_rate": 0.0,
                "total_duration_hours": 0.0,
                "within_6_hour_limit": False
            }
        }
        save_benchmark_report(error_report)
        raise

if __name__ == "__main__":
    main()
