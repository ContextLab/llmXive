"""
Benchmark script to measure and validate the 6-hour CPU runtime constraint.

This script runs the full pipeline and measures:
- Total wall-clock time
- CPU time usage
- Memory peak
- Per-stage breakdown

Output: A detailed JSON report in data/benchmark_results.json
"""
import os
import sys
import time
import json
import resource
import logging
from datetime import datetime
from typing import Dict, Any

from data.utils import setup_logging
from performance_optimizer import PerformanceConfig, run_optimized_training

logger = logging.getLogger(__name__)


def measure_memory_usage():
    """Measure current memory usage in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / 1024  # Convert KB to MB


def run_benchmark():
    """
    Execute the benchmark and generate a detailed report.
    """
    # Setup
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logger = setup_logging(level=log_level)
    
    logger.info("Starting Performance Benchmark")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    # Configuration
    config = PerformanceConfig(
        max_runtime_seconds=21600,  # 6 hours
        enable_feature_cache=True,
        cache_dir="data/cache",
        num_workers=4,
        batch_size=32,
        early_termination_threshold=0.90
    )
    
    # Initial measurements
    start_time = time.time()
    initial_memory = measure_memory_usage()
    
    # Run the optimized pipeline
    try:
        report = run_optimized_training(config)
        
        # Final measurements
        end_time = time.time()
        final_memory = measure_memory_usage()
        
        # Build benchmark report
        benchmark_report = {
            "benchmark_id": f"bench_{int(start_time)}",
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "max_runtime_seconds": config.max_runtime_seconds,
                "num_workers": config.num_workers,
                "batch_size": config.batch_size,
                "feature_cache_enabled": config.enable_feature_cache
            },
            "results": {
                "total_runtime_seconds": report['total_runtime_seconds'],
                "total_runtime_hours": report['total_runtime_hours'],
                "budget_met": report['budget_met'],
                "memory_peak_mb": report['memory_peak_mb'],
                "memory_start_mb": initial_memory,
                "memory_end_mb": final_memory,
                "cache_hit_rate": report['cache_stats']['hit_rate'] if report['cache_stats'] else None,
                "training_epochs": report['training_result']['epochs_completed']
            },
            "status": "PASS" if report['budget_met'] else "FAIL",
            "notes": []
        }
        
        # Add notes
        if not report['budget_met']:
            benchmark_report['notes'].append(
                f"Pipeline exceeded budget by {report['total_runtime_seconds'] - config.max_runtime_seconds:.1f} seconds"
            )
        
        if report['cache_stats'] and report['cache_stats']['hit_rate'] > 0.5:
            benchmark_report['notes'].append(
                f"Feature cache achieved {report['cache_stats']['hit_rate']*100:.1f}% hit rate"
            )
        
        # Save report
        os.makedirs("data", exist_ok=True)
        report_path = "data/benchmark_results.json"
        with open(report_path, 'w') as f:
            json.dump(benchmark_report, f, indent=2)
        
        logger.info(f"Benchmark report saved to {report_path}")
        logger.info(f"Status: {benchmark_report['status']}")
        logger.info(f"Runtime: {report['total_runtime_hours']:.2f} hours")
        logger.info(f"Memory peak: {report['memory_peak_mb']:.1f} MB")
        
        return 0 if report['budget_met'] else 1
        
    except Exception as e:
        logger.exception(f"Benchmark failed: {e}")
        return 1


def main():
    """Main entry point."""
    return run_benchmark()


if __name__ == "__main__":
    sys.exit(main())
