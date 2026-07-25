import os
import sys
import time
import json
import logging
import tracemalloc
from pathlib import Path
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('benchmark')

# Ensure paths are in sys.path for relative imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import load_config_from_file, ensure_directories
from parser import main as run_parser
from splitter import main as run_splitter
from ablation import main as run_ablation
from classifier import main as run_classifier
from simulator import main as run_simulation
from stats import main as run_stats

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    if not tracemalloc.is_tracing():
        return 0.0
    current, peak = tracemalloc.get_traced_memory()
    return current / (1024 * 1024)

def get_peak_memory_mb() -> float:
    """Get peak memory usage in MB."""
    if not tracemalloc.is_tracing():
        return 0.0
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)

def run_phase_benchmark(phase_name: str, phase_func: callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Run a specific phase and measure its execution time and memory usage.
    """
    logger.info(f"Starting benchmark for phase: {phase_name}")
    tracemalloc.start()
    start_time = time.perf_counter()

    try:
        phase_func(*args, **kwargs)
        end_time = time.perf_counter()
        current_mem = get_memory_usage_mb()
        peak_mem = get_peak_memory_mb()
        duration_ms = (end_time - start_time) * 1000

        result = {
            "phase": phase_name,
            "duration_ms": round(duration_ms, 2),
            "peak_memory_mb": round(peak_mem, 2),
            "final_memory_mb": round(current_mem, 2),
            "status": "success"
        }
        logger.info(f"Phase {phase_name} completed in {duration_ms:.2f}ms. Peak memory: {peak_mem:.2f}MB")
        return result
    except Exception as e:
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        logger.error(f"Phase {phase_name} failed: {str(e)}")
        return {
            "phase": phase_name,
            "duration_ms": round(duration_ms, 2),
            "status": "failed",
            "error": str(e)
        }
    finally:
        tracemalloc.stop()

def benchmark_parser_phase(config: Any) -> Dict[str, Any]:
    """Benchmark the parser phase."""
    # The parser main function expects to be run as a script, so we call it directly
    # We wrap it to catch errors if it expects sys.argv
    try:
        # Mock sys.argv if needed, but main() usually handles internal args
        # For benchmarking, we call the core logic if exposed, or wrap main
        # Assuming main() handles its own arg parsing or uses defaults
        run_parser()
        return {"phase": "parser", "status": "success"}
    except Exception as e:
        return {"phase": "parser", "status": "failed", "error": str(e)}

def benchmark_splitter_phase(config: Any) -> Dict[str, Any]:
    """Benchmark the splitter phase."""
    try:
        run_splitter()
        return {"phase": "splitter", "status": "success"}
    except Exception as e:
        return {"phase": "splitter", "status": "failed", "error": str(e)}

def benchmark_ablation_phase(config: Any) -> Dict[str, Any]:
    """Benchmark the ablation phase."""
    try:
        run_ablation()
        return {"phase": "ablation", "status": "success"}
    except Exception as e:
        return {"phase": "ablation", "status": "failed", "error": str(e)}

def benchmark_classifier_phase(config: Any) -> Dict[str, Any]:
    """Benchmark the classifier phase."""
    try:
        run_classifier()
        return {"phase": "classifier", "status": "success"}
    except Exception as e:
        return {"phase": "classifier", "status": "failed", "error": str(e)}

def benchmark_simulation_phase(config: Any) -> Dict[str, Any]:
    """Benchmark the simulation phase."""
    try:
        run_simulation()
        return {"phase": "simulation", "status": "success"}
    except Exception as e:
        return {"phase": "simulation", "status": "failed", "error": str(e)}

def benchmark_stats_phase(config: Any) -> Dict[str, Any]:
    """Benchmark the stats phase."""
    try:
        run_stats()
        return {"phase": "stats", "status": "success"}
    except Exception as e:
        return {"phase": "stats", "status": "failed", "error": str(e)}

def run_full_benchmark(config: Optional[Any] = None) -> Dict[str, Any]:
    """
    Run the full benchmark pipeline, timing each phase.
    """
    if config is None:
        config = load_config_from_file()
    
    ensure_directories(config)

    phases = [
        ("parser", benchmark_parser_phase),
        ("splitter", benchmark_splitter_phase),
        ("ablation", benchmark_ablation_phase),
        ("classifier", benchmark_classifier_phase),
        ("simulation", benchmark_simulation_phase),
        ("stats", benchmark_stats_phase)
    ]

    phase_timings = {}
    total_start = time.perf_counter()

    for name, func in phases:
        # Run the benchmark wrapper which measures time and memory
        result = run_phase_benchmark(name, func, config)
        phase_timings[name] = result['duration_ms'] if result['status'] == 'success' else 0

    total_end = time.perf_counter()
    total_runtime_ms = (total_end - total_start) * 1000

    report = {
        "total_runtime": round(total_runtime_ms, 2),
        "phase_timings": phase_timings,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "config_summary": {
            "token_budget": config.get('TOKEN_BUDGET', 4096),
            "min_context": config.get('MIN_CONTEXT', 256),
            "k_random_baseline": config.get('K_RANDOM_BASELINE', 2)
        }
    }

    return report

def save_benchmark_report(report: Dict[str, Any], output_path: str) -> None:
    """Save the benchmark report to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Benchmark report saved to {output_path}")

def main():
    """Main entry point for the benchmark script."""
    logger.info("Starting benchmark execution...")
    
    config = load_config_from_file()
    ensure_directories(config)

    report = run_full_benchmark(config)
    output_path = str(Path(config.get('DATA_PROCESSED', 'data/processed')) / 'benchmark_log.json')
    save_benchmark_report(report, output_path)

    print(f"Benchmark complete. Total runtime: {report['total_runtime']}ms")
    print(f"Results saved to: {output_path}")

    return 0

if __name__ == '__main__':
    sys.exit(main())
