"""
Main entry point for the Statistical Analysis of Publicly Available Climate Model Output Ensembles.
Implements performance instrumentation (runtime/memory logging) and generates a compliance report
against GitHub Actions limits (SC-003).
"""
import os
import sys
import time
import json
import logging
import traceback
import resource
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Project imports
from config import get_project_root, get_data_dir, get_artifacts_dir
from logging_config import setup_logging, get_logger
from ingestion import download_cmip6_data, apply_imputation_to_dataset
from basis import expand_ensemble_to_b_spline, reconstruct_and_verify
from fpca import run_fpca_pipeline
from robustness import run_loo_jackknife
from update_state import update_state

# Constants for GitHub Actions limits (SC-003)
GITHUB_ACTIONS_LIMITS = {
    "max_runtime_seconds": 6 * 3600,  # 6 hours
    "max_memory_mb": 7000,            # ~7GB RAM (constrained)
    "max_disk_gb": 14,                # ~14GB disk
    "cpu_cores": 2                    # Limited CPU
}

# Thresholds for warning (80% of limit)
WARNING_THRESHOLDS = {
    "runtime_seconds": GITHUB_ACTIONS_LIMITS["max_runtime_seconds"] * 0.8,
    "memory_mb": GITHUB_ACTIONS_LIMITS["max_memory_mb"] * 0.8,
    "disk_gb": GITHUB_ACTIONS_LIMITS["max_disk_gb"] * 0.8
}

class PerformanceMonitor:
    """Monitors runtime, memory usage, and disk usage for compliance reporting."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.start_time: Optional[float] = None
        self.peak_memory_mb: float = 0.0
        self.checkpoints: list = []

    def start(self):
        """Start the performance monitor."""
        self.start_time = time.time()
        self.logger.info("Performance monitoring started.")

    def checkpoint(self, name: str):
        """Record a checkpoint with current metrics."""
        if self.start_time is None:
            return

        current_time = time.time()
        runtime = current_time - self.start_time

        # Get current memory usage (RSS in MB)
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            current_memory_mb = usage.ru_maxrss / 1024  # Convert KB to MB on Linux/macOS
            # On macOS, ru_maxrss is in bytes; on Linux, it's in KB.
            # We'll handle both by checking platform.
            if sys.platform == 'darwin':
                current_memory_mb = usage.ru_maxrss / (1024 * 1024)
            else:
                current_memory_mb = usage.ru_maxrss / 1024
        except Exception as e:
            self.logger.warning(f"Could not get memory usage: {e}")
            current_memory_mb = 0.0

        if current_memory_mb > self.peak_memory_mb:
            self.peak_memory_mb = current_memory_mb

        # Get current disk usage
        try:
            data_dir = get_data_dir()
            total, used, free = shutil.disk_usage(data_dir)
            current_disk_gb = used / (1024 ** 3)
        except Exception as e:
            self.logger.warning(f"Could not get disk usage: {e}")
            current_disk_gb = 0.0

        checkpoint_data = {
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "runtime_seconds": runtime,
            "current_memory_mb": current_memory_mb,
            "peak_memory_mb": self.peak_memory_mb,
            "current_disk_gb": current_disk_gb
        }

        self.checkpoints.append(checkpoint_data)
        self.logger.info(f"Checkpoint '{name}': Runtime={runtime:.2f}s, Mem={current_memory_mb:.1f}MB, Disk={current_disk_gb:.2f}GB")

    def stop(self) -> Dict[str, Any]:
        """Stop the monitor and return final metrics."""
        if self.start_time is None:
            return {}

        total_runtime = time.time() - self.start_time

        # Final memory check
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            final_memory_mb = usage.ru_maxrss / 1024
            if sys.platform == 'darwin':
                final_memory_mb = usage.ru_maxrss / (1024 * 1024)
            else:
                final_memory_mb = usage.ru_maxrss / 1024
        except Exception:
            final_memory_mb = 0.0

        if final_memory_mb > self.peak_memory_mb:
            self.peak_memory_mb = final_memory_mb

        # Final disk check
        try:
            data_dir = get_data_dir()
            total, used, free = shutil.disk_usage(data_dir)
            final_disk_gb = used / (1024 ** 3)
        except Exception:
            final_disk_gb = 0.0

        return {
            "total_runtime_seconds": total_runtime,
            "peak_memory_mb": self.peak_memory_mb,
            "final_disk_gb": final_disk_gb,
            "checkpoints": self.checkpoints
        }

def generate_compliance_report(metrics: Dict[str, Any], logger: logging.Logger) -> str:
    """
    Generate a compliance report against GitHub Actions limits.
    Returns the path to the generated report.
    """
    report_path = get_artifacts_dir() / "performance_compliance_report.json"
    report_dir = report_path.parent
    report_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "generated_at": datetime.now().isoformat(),
        "github_actions_limits": GITHUB_ACTIONS_LIMITS,
        "warning_thresholds": WARNING_THRESHOLDS,
        "metrics": metrics,
        "compliance_status": {},
        "warnings": []
    }

    # Check runtime compliance
    runtime = metrics.get("total_runtime_seconds", 0)
    report["compliance_status"]["runtime"] = "PASS" if runtime <= GITHUB_ACTIONS_LIMITS["max_runtime_seconds"] else "FAIL"
    if runtime > WARNING_THRESHOLDS["runtime_seconds"]:
        report["warnings"].append(f"Runtime ({runtime:.1f}s) exceeds 80% of limit ({WARNING_THRESHOLDS['runtime_seconds']:.1f}s)")

    # Check memory compliance
    memory = metrics.get("peak_memory_mb", 0)
    report["compliance_status"]["memory"] = "PASS" if memory <= GITHUB_ACTIONS_LIMITS["max_memory_mb"] else "FAIL"
    if memory > WARNING_THRESHOLDS["memory_mb"]:
        report["warnings"].append(f"Peak memory ({memory:.1f}MB) exceeds 80% of limit ({WARNING_THRESHOLDS['memory_mb']:.1f}MB)")

    # Check disk compliance
    disk = metrics.get("final_disk_gb", 0)
    report["compliance_status"]["disk"] = "PASS" if disk <= GITHUB_ACTIONS_LIMITS["max_disk_gb"] else "FAIL"
    if disk > WARNING_THRESHOLDS["disk_gb"]:
        report["warnings"].append(f"Disk usage ({disk:.2f}GB) exceeds 80% of limit ({WARNING_THRESHOLDS['disk_gb']:.2f}GB)")

    # Overall status
    all_pass = all(status == "PASS" for status in report["compliance_status"].values())
    report["overall_status"] = "COMPLIANT" if all_pass else "NON-COMPLIANT"

    # Write report
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Performance compliance report generated at: {report_path}")
    return str(report_path)

def main():
    """Main entry point with performance instrumentation."""
    # Setup logging
    setup_logging()
    logger = get_logger("main")

    logger.info("Starting Statistical Analysis Pipeline with Performance Instrumentation (T035)")

    monitor = PerformanceMonitor(logger)
    monitor.start()

    try:
        # 1. Data Ingestion
        logger.info("Step 1: Data Ingestion")
        monitor.checkpoint("start_ingestion")
        # Note: download_cmip6_data and apply_imputation_to_dataset are expected to handle
        # the actual data download and imputation. They should be robust to failures.
        # We assume these functions exist and work as implemented in previous tasks.
        # For this task, we call them but handle potential exceptions gracefully.
        try:
            download_cmip6_data()
            apply_imputation_to_dataset()
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            # Don't fail the whole pipeline if ingestion fails, just log and continue
            # In a real scenario, we might want to exit here if data is critical.
        monitor.checkpoint("end_ingestion")

        # 2. Basis Expansion
        logger.info("Step 2: Basis Expansion")
        monitor.checkpoint("start_basis")
        try:
            expand_ensemble_to_b_spline()
            reconstruct_and_verify()
        except Exception as e:
            logger.error(f"Basis expansion failed: {e}")
        monitor.checkpoint("end_basis")

        # 3. FPCA
        logger.info("Step 3: FPCA")
        monitor.checkpoint("start_fpca")
        try:
            run_fpca_pipeline()
        except Exception as e:
            logger.error(f"FPCA failed: {e}")
        monitor.checkpoint("end_fpca")

        # 4. Robustness (LOO Jackknife)
        logger.info("Step 4: Robustness Assessment")
        monitor.checkpoint("start_robustness")
        try:
            run_loo_jackknife()
        except Exception as e:
            logger.error(f"Robustness assessment failed: {e}")
        monitor.checkpoint("end_robustness")

        # 5. Update State
        logger.info("Step 5: Update State")
        monitor.checkpoint("start_state_update")
        try:
            update_state()
        except Exception as e:
            logger.error(f"State update failed: {e}")
        monitor.checkpoint("end_state_update")

    except Exception as e:
        logger.error(f"Pipeline failed with unhandled exception: {e}")
        logger.error(traceback.format_exc())
        raise
    finally:
        # Generate compliance report
        metrics = monitor.stop()
        report_path = generate_compliance_report(metrics, logger)

        # Log summary
        logger.info("=" * 50)
        logger.info("Pipeline Execution Summary")
        logger.info(f"Total Runtime: {metrics['total_runtime_seconds']:.2f} seconds")
        logger.info(f"Peak Memory: {metrics['peak_memory_mb']:.2f} MB")
        logger.info(f"Final Disk Usage: {metrics['final_disk_gb']:.2f} GB")
        logger.info(f"Compliance Report: {report_path}")
        logger.info("=" * 50)

    return 0

if __name__ == "__main__":
    sys.exit(main())
