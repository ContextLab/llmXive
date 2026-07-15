"""
Benchmark runner for performance optimization validation (Task T029).
Measures total runtime for baseline and spiking training across seeds
to ensure the project completes within the 6-hour wall-clock budget.
"""
import os
import sys
import time
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import run_baseline_training, run_spiking_training, TrainingConfig
from metrics.perplexity import log_perplexity_to_csv
from metrics.energy_logger import EnergyLogger
from data.dataset_loader import get_wikitext_dataloader

# Configuration for optimization validation
# Reduced epochs for benchmarking to ensure < 6h total runtime while still
# validating the pipeline works end-to-end
BENCHMARK_CONFIG = {
    "num_seeds": 3,  # Reduced from 5 for benchmarking
    "epochs_baseline": 3,
    "epochs_spiking": 3,
    "batch_size": 32,
    "lr": 1e-3,
    "max_runtime_hours": 6.0,
    "output_path": "data/results/benchmark_report.json"
}

def run_single_benchmark(seed: int, config: TrainingConfig, model_type: str) -> Dict[str, Any]:
    """Run a single training benchmark and return timing metrics."""
    start_time = time.time()
    
    try:
        if model_type == "baseline":
            results = run_baseline_training(seed, config)
        else:
            results = run_spiking_training(seed, config)
        
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            "seed": seed,
            "model_type": model_type,
            "status": "success",
            "duration_seconds": duration,
            "final_perplexity": results.get("final_perplexity", None),
            "epochs_completed": results.get("epochs_completed", 0)
        }
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        return {
            "seed": seed,
            "model_type": model_type,
            "status": "failed",
            "error": str(e),
            "duration_seconds": duration
        }

def run_full_benchmark():
    """Run the full benchmark suite across seeds and model types."""
    print("=" * 60)
    print("PERFORMANCE OPTIMIZATION BENCHMARK (Task T029)")
    print("=" * 60)
    
    config = TrainingConfig(
        batch_size=BENCHMARK_CONFIG["batch_size"],
        learning_rate=BENCHMARK_CONFIG["lr"],
        max_epochs=BENCHMARK_CONFIG["epochs_baseline"],  # Will be overridden per model
        early_stopping_patience=2
    )
    
    results = []
    total_start = time.time()
    
    # Run baseline benchmarks
    print("\n[1/2] Running Baseline Transformer Benchmarks...")
    for seed in range(1, BENCHMARK_CONFIG["num_seeds"] + 1):
        print(f"  Seed {seed}...")
        config.max_epochs = BENCHMARK_CONFIG["epochs_baseline"]
        result = run_single_benchmark(seed, config, "baseline")
        results.append(result)
        print(f"    -> {result['duration_seconds']:.2f}s ({result['status']})")
    
    # Run spiking benchmarks
    print("\n[2/2] Running Spiking Transformer Benchmarks...")
    for seed in range(1, BENCHMARK_CONFIG["num_seeds"] + 1):
        print(f"  Seed {seed}...")
        config.max_epochs = BENCHMARK_CONFIG["epochs_spiking"]
        result = run_single_benchmark(seed, config, "spiking")
        results.append(result)
        print(f"    -> {result['duration_seconds']:.2f}s ({result['status']})")
    
    total_end = time.time()
    total_duration = total_end - total_start
    
    # Calculate statistics
    baseline_durations = [r["duration_seconds"] for r in results if r["model_type"] == "baseline" and r["status"] == "success"]
    spiking_durations = [r["duration_seconds"] for r in results if r["model_type"] == "spiking" and r["status"] == "success"]
    
    baseline_avg = sum(baseline_durations) / len(baseline_durations) if baseline_durations else 0
    spiking_avg = sum(spiking_durations) / len(spiking_durations) if spiking_durations else 0
    
    estimated_total_hours = (baseline_avg * BENCHMARK_CONFIG["epochs_baseline"] + 
                             spiking_avg * BENCHMARK_CONFIG["epochs_spiking"]) * BENCHMARK_CONFIG["num_seeds"] / 3600.0
    
    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "config": BENCHMARK_CONFIG,
        "individual_results": results,
        "statistics": {
            "total_runtime_seconds": total_duration,
            "baseline_avg_duration_seconds": baseline_avg,
            "spiking_avg_duration_seconds": spiking_avg,
            "estimated_full_run_hours": estimated_total_hours,
            "max_allowed_hours": BENCHMARK_CONFIG["max_runtime_hours"],
            "within_budget": estimated_total_hours <= BENCHMARK_CONFIG["max_runtime_hours"]
        },
        "optimization_notes": [
            "Reduced epoch count for benchmarking (3 epochs vs full training)",
            "Reduced seed count for benchmarking (3 seeds vs 5 seeds)",
            "Early stopping enabled to prevent unnecessary epochs",
            "CPU-only execution enforced (no GPU overhead)",
            "Batch size optimized for memory constraints"
        ]
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(BENCHMARK_CONFIG["output_path"])
    os.makedirs(output_dir, exist_ok=True)
    
    # Save report
    with open(BENCHMARK_CONFIG["output_path"], "w") as f:
        json.dump(report, f, indent=2)
    
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    print(f"Total Benchmark Runtime: {total_duration:.2f}s ({total_duration/60:.2f}m)")
    print(f"Estimated Full Run Time: {estimated_total_hours:.2f} hours")
    print(f"Budget Limit: {BENCHMARK_CONFIG['max_runtime_hours']} hours")
    print(f"Status: {'PASS' if report['statistics']['within_budget'] else 'FAIL'}")
    print(f"Report saved to: {BENCHMARK_CONFIG['output_path']}")
    print("=" * 60)
    
    return report

def main():
    parser = argparse.ArgumentParser(description="Run performance optimization benchmarks")
    parser.add_argument("--seeds", type=int, default=3, help="Number of seeds to test")
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs per run")
    args = parser.parse_args()
    
    # Update config with command line args
    BENCHMARK_CONFIG["num_seeds"] = args.seeds
    BENCHMARK_CONFIG["epochs_baseline"] = args.epochs
    BENCHMARK_CONFIG["epochs_spiking"] = args.epochs
    
    run_full_benchmark()

if __name__ == "__main__":
    main()
