"""
Performance monitoring and optimization tools for the simulation pipeline.

This module provides utilities to:
1. Log execution times for simulation scenarios
2. Validate against the 6-hour (21,600s) limit for 2-core CPU
3. Generate performance reports
4. Estimate total runtime based on partial samples
"""
import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Constants
TARGET_RUNTIME_SECONDS = 6 * 3600  # 6 hours
MAX_CORES = 2
LOG_FILE = "data/processed/performance_log.json"

def load_performance_log(log_path: Optional[str] = None) -> Dict[str, Any]:
    """Load existing performance log or return empty structure."""
    if log_path is None:
        log_path = LOG_FILE
        
    if not os.path.exists(log_path):
        return {
            "start_time": None,
            "end_time": None,
            "scenarios": [],
            "total_runtime": 0,
            "optimization_notes": []
        }
        
    with open(log_path, 'r') as f:
        return json.load(f)

def save_performance_log(data: Dict[str, Any], log_path: Optional[str] = None) -> None:
    """Save performance log to disk."""
    if log_path is None:
        log_path = LOG_FILE
        
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w') as f:
        json.dump(data, f, indent=2)

def log_scenario_execution(
    scenario_id: str, 
    runtime_seconds: float, 
    status: str = "completed",
    error_msg: Optional[str] = None,
    log_path: Optional[str] = None
) -> None:
    """Log a single scenario execution result."""
    log_data = load_performance_log(log_path)
    
    entry = {
        "scenario_id": scenario_id,
        "runtime_seconds": runtime_seconds,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "error_msg": error_msg
    }
    
    log_data["scenarios"].append(entry)
    
    if log_data["start_time"] is None:
        log_data["start_time"] = entry["timestamp"]
        
    if status == "completed":
        log_data["total_runtime"] += runtime_seconds
        
    log_data["end_time"] = datetime.now().isoformat()
    
    save_performance_log(log_data, log_path)
    
    logger.info(f"Logged scenario {scenario_id}: {status} ({runtime_seconds:.2f}s)")

def validate_performance_target(
    total_runtime: float, 
    num_scenarios: int, 
    target_seconds: int = TARGET_RUNTIME_SECONDS
) -> Dict[str, Any]:
    """
    Validate if the simulation meets the performance target.
    
    Returns a dictionary with:
    - passed: bool
    - total_runtime: float
    - remaining_budget: float
    - avg_time_per_scenario: float
    - estimated_total: float (if partial)
    - recommendation: str
    """
    avg_time = total_runtime / num_scenarios if num_scenarios > 0 else 0
    remaining_budget = target_seconds - total_runtime
    
    result = {
        "passed": total_runtime <= target_seconds,
        "total_runtime": total_runtime,
        "target_seconds": target_seconds,
        "remaining_budget": remaining_budget,
        "avg_time_per_scenario": avg_time,
        "num_scenarios": num_scenarios
    }
    
    if total_runtime <= target_seconds:
        result["recommendation"] = "Performance target met."
    else:
        excess = total_runtime - target_seconds
        result["recommendation"] = (
            f"Target exceeded by {excess:.0f}s ({(excess/target_seconds)*100:.1f}%). "
            "Consider reducing replicate counts for large sample sizes or "
            "implementing early stopping for clear null cases."
        )
        
    return result

def generate_performance_report(log_path: Optional[str] = None) -> Dict[str, Any]:
    """Generate a comprehensive performance report."""
    log_data = load_performance_log(log_path)
    
    if not log_data["scenarios"]:
        return {
            "status": "no_data",
            "message": "No scenario execution data found."
        }
    
    total_runtime = log_data["total_runtime"]
    num_scenarios = len(log_data["scenarios"])
    
    # Calculate statistics
    runtimes = [s["runtime_seconds"] for s in log_data["scenarios"] if s["status"] == "completed"]
    avg_time = np.mean(runtimes) if runtimes else 0
    max_time = np.max(runtimes) if runtimes else 0
    min_time = np.min(runtimes) if runtimes else 0
    
    # Count failures
    failures = [s for s in log_data["scenarios"] if s["status"] != "completed"]
    
    validation = validate_performance_target(total_runtime, num_scenarios)
    
    report = {
        "status": "success" if validation["passed"] else "exceeded",
        "summary": {
            "total_runtime_seconds": total_runtime,
            "total_runtime_formatted": f"{total_runtime/3600:.2f} hours",
            "target_seconds": TARGET_RUNTIME_SECONDS,
            "target_formatted": f"{TARGET_RUNTIME_SECONDS/3600:.2f} hours",
            "passed": validation["passed"],
            "num_scenarios": num_scenarios,
            "failed_scenarios": len(failures)
        },
        "statistics": {
            "average_time_per_scenario": avg_time,
            "max_time_per_scenario": max_time,
            "min_time_per_scenario": min_time,
            "std_dev": np.std(runtimes) if runtimes else 0
        },
        "recommendation": validation["recommendation"],
        "start_time": log_data["start_time"],
        "end_time": log_data["end_time"]
    }
    
    # Save report
    report_path = "data/processed/performance_report.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Performance report saved to {report_path}")
    return report

def estimate_total_runtime(sample_runtimes: List[float], total_scenarios: int) -> Dict[str, Any]:
    """
    Estimate total runtime based on a sample of completed scenarios.
    
    Args:
        sample_runtimes: List of runtime seconds for completed scenarios
        total_scenarios: Total number of scenarios in the full grid
        
    Returns:
        Dictionary with estimated total runtime and confidence intervals
    """
    if not sample_runtimes:
        return {"status": "insufficient_data"}
        
    avg_time = np.mean(sample_runtimes)
    std_err = np.std(sample_runtimes) / np.sqrt(len(sample_runtimes))
    
    estimated_total = avg_time * total_scenarios
    margin_of_error = 1.96 * std_err * total_scenarios  # 95% CI
    
    return {
        "status": "estimated",
        "estimated_total_seconds": estimated_total,
        "estimated_total_hours": estimated_total / 3600,
        "confidence_interval_95": (
            (estimated_total - margin_of_error, estimated_total + margin_of_error)
        ),
        "target_met": estimated_total + margin_of_error <= TARGET_RUNTIME_SECONDS,
        "sample_size": len(sample_runtimes)
    }
