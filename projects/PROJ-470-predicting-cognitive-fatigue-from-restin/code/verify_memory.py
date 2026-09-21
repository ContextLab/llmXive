"""
Verify total pipeline memory usage ≤ 7 GB (SC-003, DC-001).
Runs the full pipeline stages (Download -> Preprocess -> Features -> Analysis -> Report)
while monitoring peak RSS memory usage.
"""
from __future__ import annotations

import os
import sys
import json
import time
import subprocess
import resource
from pathlib import Path
from typing import Any, Dict

# Add code directory to path for imports
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from utils.logging import get_logger, log_operation
from utils.monitor import ResourceMonitor

def load_config() -> Dict[str, Any]:
    """Load configuration from code/config.yaml."""
    import yaml
    config_path = code_dir / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def run_pipeline() -> float:
    """
    Execute the full pipeline stages and return peak memory usage in GB.
    Stages: Download, Preprocess, Features, Analysis, Report
    """
    logger = get_logger("verify_memory")
    log_operation("run_pipeline", status="starting")

    stages = [
        ("Download", "python code/download.py --validate"),
        ("Preprocess", "python code/preprocess.py"),
        ("Features", "python code/features.py"),
        ("Analysis", "python code/analysis.py"),
        ("Report", "python code/report.py")
    ]

    monitor = ResourceMonitor()
    monitor.start()

    for stage_name, command in stages:
        logger.info(f"Running stage: {stage_name}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Stage {stage_name} completed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Stage {stage_name} failed: {e.stderr}")
            raise RuntimeError(f"Pipeline stage {stage_name} failed")

    monitor.stop()
    peak_memory_bytes = monitor.get_peak_memory()
    peak_memory_gb = peak_memory_bytes / (1024 ** 3)

    log_operation("run_pipeline", status="completed", peak_memory_gb=peak_memory_gb)
    return peak_memory_gb

def check_memory_usage(peak_memory_gb: float, threshold_gb: float = 7.0) -> bool:
    """Check if peak memory usage is within threshold."""
    return peak_memory_gb <= threshold_gb

def write_resource_usage(peak_memory_gb: float, passed: bool, output_path: str) -> None:
    """Write resource usage metrics to JSON file."""
    usage_data = {
        "peak_rss_gb": round(peak_memory_gb, 4),
        "total_runtime_hours": 0.0,  # Can be calculated if needed
        "memory_threshold_gb": 7.0,
        "passed": passed
    }

    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(usage_data, f, indent=2)

def main() -> None:
    """Main entry point for memory verification."""
    logger = get_logger("verify_memory")
    logger.info("Starting memory verification pipeline")

    try:
        config = load_config()
        threshold = config.get("memory_threshold_gb", 7.0)

        peak_memory_gb = run_pipeline()
        passed = check_memory_usage(peak_memory_gb, threshold)

        output_path = "data/analysis/resource_usage.json"
        write_resource_usage(peak_memory_gb, passed, output_path)

        if passed:
            logger.info(f"Memory check PASSED: {peak_memory_gb:.4f} GB <= {threshold} GB")
            sys.exit(0)
        else:
            logger.error(f"Memory check FAILED: {peak_memory_gb:.4f} GB > {threshold} GB")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Memory verification failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()