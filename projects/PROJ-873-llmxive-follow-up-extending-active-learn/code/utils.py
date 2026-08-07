import os
import signal
import sys
import time
import resource
import logging
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

class PartialRunError(Exception):
    """Raised when the pipeline must stop gracefully due to resource limits."""
    pass

class DataFlowViolationError(Exception):
    """Raised when a required data artifact is missing or schema-mismatched."""
    pass

class ResourceWatchdog:
    def __init__(self, max_runtime_seconds: float, max_memory_bytes: int):
        self.max_runtime_seconds = max_runtime_seconds
        self.max_memory_bytes = max_memory_bytes
        self.start_time = time.time()
        self.running = True

    def check(self) -> bool:
        """Returns True if limits are respected, False otherwise."""
        elapsed = time.time() - self.start_time
        if elapsed > self.max_runtime_seconds:
            logger.warning(f"Runtime limit exceeded: {elapsed:.2f}s > {self.max_runtime_seconds}s")
            return False

        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            mem_mb = usage.ru_maxrss / 1024  # Convert KB to MB on Linux/macOS
            mem_bytes = mem_mb * 1024 * 1024
            if mem_bytes > self.max_memory_bytes:
                logger.warning(f"Memory limit exceeded: {mem_bytes:.2f}B > {self.max_memory_bytes}B")
                return False
        except Exception as e:
            logger.warning(f"Could not check memory usage: {e}")

        return True

def enforce_resource_limits(watchdog: ResourceWatchdog):
    if not watchdog.check():
        raise PartialRunError("Resource limits exceeded, terminating gracefully.")

def init_watchdog(max_runtime_hours: float, max_memory_gb: float) -> ResourceWatchdog:
    max_runtime_seconds = max_runtime_hours * 3600
    max_memory_bytes = max_memory_gb * 1024 * 1024 * 1024
    return ResourceWatchdog(max_runtime_seconds, max_memory_bytes)

def check_limits_periodically(watchdog: ResourceWatchdog, interval_seconds: float = 60):
    while watchdog.running:
        time.sleep(interval_seconds)
        if not watchdog.check():
            raise PartialRunError("Resource limits exceeded, terminating gracefully.")

def stop_watchdog(watchdog: ResourceWatchdog):
    watchdog.running = False

def validate_artifact_chain(artifact_paths: List[str], schemas: Dict[str, Dict[str, Any]]):
    """
    Validates that all required artifacts exist and conform to their expected schemas.
    
    Args:
        artifact_paths: List of file paths to check.
        schemas: Dictionary mapping file paths to expected schema structures (dicts).
    
    Raises:
        DataFlowViolationError: If a file is missing or schema mismatched.
    """
    for path in artifact_paths:
        if not os.path.exists(path):
            raise DataFlowViolationError(f"Required artifact missing: {path}")
        
        if path in schemas:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                expected_schema = schemas[path]
                # Simple schema check: ensure all expected keys exist at the top level
                if isinstance(expected_schema, dict):
                    for key in expected_schema:
                        if key not in data:
                            raise DataFlowViolationError(
                                f"Artifact {path} missing required key: {key}"
                            )
                
                logger.info(f"Artifact validated: {path}")
            except json.JSONDecodeError as e:
                raise DataFlowViolationError(f"Artifact {path} is not valid JSON: {e}")
            except Exception as e:
                raise DataFlowViolationError(f"Error validating artifact {path}: {e}")

def get_config_schema_for_artifact(artifact_name: str) -> Dict[str, Any]:
    """
    Returns the expected schema for a given artifact name.
    This centralizes schema definitions for consistency.
    """
    schemas = {
        "data/processed/injected_datasets.json": {
            "datasets": dict,
            "injection_params": dict,
            "validation_status": str
        },
        "data/processed/clusters.json": {
            "clusters": list,
            "threshold": float,
            "algorithm": str
        },
        "data/processed/unique_subset.json": {
            "subset": list,
            "total_original": int,
            "total_unique": int
        },
        "data/processed/comparison_log.json": {
            "logs": list
        },
        "data/results/flagged_pairs_count.json": {
            "wasted_count": int,
            "total_pairs": int,
            "wasted_ratio": float
        },
        "data/results/consensus_sample.json": list,
        "data/results/consensus_ground_truth.json": list,
        "data/results/correction_factor.json": {
            "correction_factor": float,
            "proxy_accuracy": float,
            "sample_size": int,
            "confusion_matrix": dict
        },
        "data/results/us1_efficiency_ratio.json": {
            "wasted_ratio": float,
            "wasted_ratio_corrected": float,
            "wasted_count": int,
            "total_budget": int
        }
    }
    return schemas.get(artifact_name, {})