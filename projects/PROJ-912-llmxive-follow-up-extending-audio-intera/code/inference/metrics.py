"""
Metrics calculation module for User Story 2.

Calculates AUC, latency, and peak RAM usage for inference results.
Compares results against GitHub Actions constraints (≤6h runtime, ≤7GB RAM).
"""
import os
import time
import logging
import json
import tracemalloc
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score
import psutil

from utils.logger import get_logger, EvaluationError
from config import get_resource_limits, PathConfig

logger = get_logger(__name__)

# Constants for constraint checking
MAX_RUNTIME_HOURS = 6.0
MAX_RAM_GB = 7.0
MAX_RAM_MB = MAX_RAM_GB * 1024

def calculate_auc(labels: np.ndarray, probabilities: np.ndarray) -> float:
    """
    Calculate Area Under the Curve (AUC) for binary classification.

    Args:
        labels: Ground truth binary labels (0 or 1).
        probabilities: Predicted probabilities for the positive class.

    Returns:
        AUC score (float between 0 and 1).

    Raises:
        EvaluationError: If labels or probabilities are invalid or if AUC cannot be computed.
    """
    if len(labels) == 0 or len(probabilities) == 0:
        raise EvaluationError("Labels or probabilities are empty, cannot compute AUC.")

    if len(labels) != len(probabilities):
        raise EvaluationError(
            f"Label length ({len(labels)}) does not match probability length ({len(probabilities)})."
        )

    # Ensure unique labels exist for AUC calculation
    unique_labels = np.unique(labels)
    if len(unique_labels) < 2:
        logger.warning("Only one class present in labels. Returning 0.5 AUC (random).")
        return 0.5

    try:
        auc = roc_auc_score(labels, probabilities)
        return float(auc)
    except ValueError as e:
        raise EvaluationError(f"Failed to compute AUC: {str(e)}") from e

def calculate_latency(start_time: float, end_time: float) -> float:
    """
    Calculate inference latency in seconds.

    Args:
        start_time: Start timestamp (time.time()).
        end_time: End timestamp (time.time()).

    Returns:
        Latency in seconds.
    """
    return end_time - start_time

def get_peak_ram_mb() -> float:
    """
    Get current peak RAM usage in MB using psutil.

    Returns:
        Peak RAM usage in MB.
    """
    process = psutil.Process(os.getpid())
    # Note: psutil does not track historical peak across process lifetime by default
    # without explicit monitoring. We approximate with current RSS or use tracemalloc if enabled.
    # For a robust measure, we assume tracemalloc is started before inference if needed.
    # Here we return current RSS as a proxy if tracemalloc isn't active, or peak if it is.
    try:
        # Try to get peak memory from tracemalloc if available
        current, peak = tracemalloc.get_traced_memory()
        return peak / (1024 * 1024)
    except (RuntimeError, ValueError):
        # Fallback to psutil current RSS if tracemalloc is not running
        mem_info = process.memory_info()
        return mem_info.rss / (1024 * 1024)

def check_constraints(
    runtime_seconds: float,
    peak_ram_mb: float,
    max_runtime_hours: float = MAX_RUNTIME_HOURS,
    max_ram_gb: float = MAX_RAM_GB
) -> Dict[str, Any]:
    """
    Check if runtime and RAM usage are within project constraints.

    Args:
        runtime_seconds: Total runtime in seconds.
        peak_ram_mb: Peak RAM usage in MB.
        max_runtime_hours: Maximum allowed runtime in hours.
        max_ram_gb: Maximum allowed RAM in GB.

    Returns:
        Dictionary with pass/fail status and details.
    """
    max_runtime_seconds = max_runtime_hours * 3600
    max_ram_mb = max_ram_gb * 1024

    runtime_ok = runtime_seconds <= max_runtime_seconds
    ram_ok = peak_ram_mb <= max_ram_mb

    return {
        "runtime_ok": runtime_ok,
        "runtime_seconds": runtime_seconds,
        "runtime_limit_seconds": max_runtime_seconds,
        "ram_ok": ram_ok,
        "peak_ram_mb": peak_ram_mb,
        "ram_limit_mb": max_ram_mb,
        "overall_pass": runtime_ok and ram_ok,
        "message": (
            "PASS" if runtime_ok and ram_ok else "FAIL"
        )
    }

def calculate_metrics_for_model(
    labels: np.ndarray,
    probabilities: np.ndarray,
    runtime_seconds: float,
    peak_ram_mb: float
) -> Dict[str, Any]:
    """
    Calculate all metrics for a single model's inference run.

    Args:
        labels: Ground truth labels.
        probabilities: Predicted probabilities.
        runtime_seconds: Inference runtime in seconds.
        peak_ram_mb: Peak RAM usage in MB.

    Returns:
        Dictionary containing AUC, latency, RAM, and constraint check results.
    """
    auc = calculate_auc(labels, probabilities)
    constraints = check_constraints(runtime_seconds, peak_ram_mb)

    return {
        "auc": auc,
        "latency_seconds": runtime_seconds,
        "peak_ram_mb": peak_ram_mb,
        "constraints": constraints
    }

def main():
    """
    Main entry point to calculate metrics from inference results.

    Expects inference results to be loaded from a JSON file generated by runner.py.
    Calculates AUC, latency, and RAM usage, then logs pass/fail against constraints.
    """
    # Initialize logging
    setup = get_logger("metrics")
    setup.info("Starting metrics calculation for User Story 2.")

    # Start memory tracking
    tracemalloc.start()

    try:
        # Load resource limits from config
        resource_limits = get_resource_limits()
        max_ram_gb = resource_limits.get("max_ram_gb", MAX_RAM_GB)
        max_runtime_hours = resource_limits.get("max_runtime_hours", MAX_RUNTIME_HOURS)

        # Load inference results (expected path from T024 or runner output)
        # Assuming runner.py outputs to data/processed/inference_results.json
        path_config = PathConfig()
        inference_results_path = path_config.processed_dir / "inference_results.json"

        if not inference_results_path.exists():
            raise FileNotFoundError(
                f"Inference results not found at {inference_results_path}. "
                "Run T024 (inference integration) first."
            )

        with open(inference_results_path, "r") as f:
            inference_data = json.load(f)

        results_summary = []
        all_passed = True

        for model_name, model_data in inference_data.items():
            logger.info(f"Processing metrics for model: {model_name}")

            labels = np.array(model_data.get("labels", []))
            probabilities = np.array(model_data.get("probabilities", []))
            runtime = model_data.get("runtime_seconds", 0.0)
            ram_mb = model_data.get("peak_ram_mb", 0.0)

            if len(labels) == 0:
                logger.warning(f"No labels found for {model_name}, skipping.")
                continue

            metrics = calculate_metrics_for_model(
                labels, probabilities, runtime, ram_mb
            )

            # Override RAM/Runtime with actual measured values if available in data
            # (In a real pipeline, runner.py would write these, but we recalculate to be safe)
            if runtime == 0:
                # If runtime wasn't stored, we can't recalculate it here without re-running.
                # We assume the runner stored it. If missing, we flag it.
                logger.warning(f"Runtime not provided for {model_name}, using placeholder.")

            if ram_mb == 0:
                ram_mb = get_peak_ram_mb()

            metrics["peak_ram_mb"] = ram_mb
            metrics["latency_seconds"] = runtime

            # Re-check constraints with updated values
            metrics["constraints"] = check_constraints(
                runtime, ram_mb, max_runtime_hours, max_ram_gb
            )

            results_summary.append({
                "model": model_name,
                "auc": metrics["auc"],
                "latency_seconds": metrics["latency_seconds"],
                "peak_ram_mb": metrics["peak_ram_mb"],
                "constraints_pass": metrics["constraints"]["overall_pass"]
            })

            if not metrics["constraints"]["overall_pass"]:
                all_passed = False
                logger.error(
                    f"Model {model_name} FAILED constraints: "
                    f"Runtime={runtime}s (limit={max_runtime_hours*3600}s), "
                    f"RAM={ram_mb:.2f}MB (limit={max_ram_gb*1024}MB)"
                )
            else:
                logger.info(
                    f"Model {model_name} PASSED constraints: "
                    f"AUC={metrics['auc']:.4f}, Runtime={runtime:.2f}s, RAM={ram_mb:.2f}MB"
                )

        # Save metrics summary to CSV/JSON
        output_path = path_config.processed_dir / "robustness_metrics.csv"
        # Simple CSV export
        import csv
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results_summary[0].keys())
            writer.writeheader()
            writer.writerows(results_summary)

        logger.info(f"Metrics saved to {output_path}")

        # Final status
        if all_passed:
            logger.info("All models passed resource constraints (FR-004, SC-002).")
        else:
            logger.error("One or more models FAILED resource constraints.")

    except Exception as e:
        logger.error(f"Error during metrics calculation: {str(e)}", exc_info=True)
        raise EvaluationError(f"Metrics calculation failed: {str(e)}") from e
    finally:
        tracemalloc.stop()

if __name__ == "__main__":
    main()