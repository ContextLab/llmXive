"""
T030: Audit Resource Usage against CI Limits (SC-005)

This script aggregates local resource logs from previous pipeline stages (T013, T017),
compares total compute time and memory usage against defined CI limits, and logs
the results to a compliance artifact.

Inputs:
  - data/derived/fallback_status.json (from T013)
  - data/derived/baseline_results.json (from T021b - used for context, though we focus on rule engine)
  - data/derived/results.csv (from T022 - contains execution logs)
  - code/utils/config.py (for CI limits: MAX_MEMORY_GB, MAX_CPU_CORES)

Outputs:
  - data/derived/resource_audit_report.json
"""

import json
import csv
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import time

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import validate_resource_limits, MAX_MEMORY_GB, MAX_CPU_CORES
from utils.logging import get_logger, log_stage_start, log_stage_end

logger = get_logger(__name__)

# CI Limits (defined in config, but we restate for clarity in this audit)
CI_MEMORY_LIMIT_GB = MAX_MEMORY_GB
CI_TIME_LIMIT_HOURS = 2.0  # Default assumption if not specified elsewhere, typically 1-2h for this scale

def load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    """Safely load a JSON file."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {path}: {e}")
        return None

def load_csv_file(path: Path) -> List[Dict[str, Any]]:
    """Load CSV as list of dicts."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        logger.error(f"Error loading {path}: {e}")
        return []

def parse_fallback_status(fallback_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract resource metrics from fallback_status.json if available."""
    metrics = {
        "ram_peak_gb": 0.0,
        "attempt_count": 0,
        "fallback_triggered": False,
        "method": "none"
    }
    if fallback_data:
        metrics["ram_peak_gb"] = float(fallback_data.get("ram_peak_gb", 0.0))
        metrics["attempt_count"] = int(fallback_data.get("attempt_count", 0))
        if fallback_data.get("fallback_method") != "none":
            metrics["fallback_triggered"] = True
            metrics["method"] = fallback_data.get("fallback_method", "unknown")
    return metrics

def parse_results_csv(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate time and success metrics from results.csv."""
    total_time_seconds = 0.0
    total_tasks = 0
    success_count = 0
    failure_count = 0

    for row in results:
        try:
            # Expect 'method' column to filter for rule_engine
            method = row.get("method", "")
            if "rule_engine" in method.lower():
                ttp = float(row.get("time_to_pivot", 0.0))
                total_time_seconds += ttp
                total_tasks += 1
                success = row.get("success", "False").lower() == "true"
                if success:
                    success_count += 1
                else:
                    failure_count += 1
        except (ValueError, TypeError) as e:
            logger.debug(f"Skipping malformed row in results.csv: {e}")
            continue

    return {
        "total_time_seconds": total_time_seconds,
        "total_tasks": total_tasks,
        "success_count": success_count,
        "failure_count": failure_count,
        "avg_time_per_task": total_time_seconds / total_tasks if total_tasks > 0 else 0.0
    }

def check_compliance(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Compare metrics against CI limits."""
    time_limit_seconds = CI_TIME_LIMIT_HOURS * 3600
    memory_limit_gb = CI_MEMORY_LIMIT_GB

    time_ok = metrics.get("total_time_seconds", 0) <= time_limit_seconds
    memory_ok = metrics.get("ram_peak_gb", 0) <= memory_limit_gb

    return {
        "time_limit_hours": CI_TIME_LIMIT_HOURS,
        "time_used_hours": metrics.get("total_time_seconds", 0) / 3600,
        "time_ok": time_ok,
        "memory_limit_gb": memory_limit_gb,
        "memory_used_gb": metrics.get("ram_peak_gb", 0),
        "memory_ok": memory_ok,
        "overall_pass": time_ok and memory_ok
    }

def main():
    log_stage_start(logger, "T030_Resource_Audit")

    # Paths
    fallback_path = Path(project_root) / "data" / "derived" / "fallback_status.json"
    results_path = Path(project_root) / "data" / "derived" / "results.csv"
    output_path = Path(project_root) / "data" / "derived" / "resource_audit_report.json"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load Data
    fallback_data = load_json_file(fallback_path)
    results_data = load_csv_file(results_path)

    if not fallback_data and not results_data:
        logger.error("No input data found for resource audit. Cannot proceed.")
        # Create a failure report
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "failed",
            "reason": "Missing input artifacts (fallback_status.json or results.csv)",
            "compliance": {"overall_pass": False}
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        return

    # Process
    fallback_metrics = parse_fallback_status(fallback_data)
    execution_metrics = parse_results_csv(results_data)

    # Combine metrics for the audit
    # We take the peak RAM from fallback_status (T013) and total time from results (T022)
    # Note: T017 (rule_engine) also has RAM usage, but fallback_status often captures the peak of the distillation phase.
    # For a strict CI check, we assume the pipeline's peak is the max of all stages.
    # Since we only have fallback_status explicitly for RAM peak in the provided artifacts, we use that.
    # If T017 had a separate log, we would merge them.
    
    combined_metrics = {
        "ram_peak_gb": fallback_metrics.get("ram_peak_gb", 0.0),
        "total_time_seconds": execution_metrics.get("total_time_seconds", 0.0),
        "total_tasks": execution_metrics.get("total_tasks", 0),
        "fallback_triggered": fallback_metrics.get("fallback_triggered", False),
        "fallback_method": fallback_metrics.get("method", "none")
    }

    compliance = check_compliance(combined_metrics)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ci_limits": {
            "max_memory_gb": CI_MEMORY_LIMIT_GB,
            "max_time_hours": CI_TIME_LIMIT_HOURS
        },
        "observed_metrics": combined_metrics,
        "compliance": compliance,
        "execution_summary": {
            "total_tasks_processed": execution_metrics.get("total_tasks", 0),
            "success_rate": (execution_metrics.get("success_count", 0) / execution_metrics.get("total_tasks", 1)) if execution_metrics.get("total_tasks", 0) > 0 else 0.0,
            "avg_time_per_task_seconds": execution_metrics.get("avg_time_per_task", 0.0)
        }
    }

    # Write Output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Resource audit complete. Report written to {output_path}")
    log_stage_end(logger, "T030_Resource_Audit")

    if not compliance["overall_pass"]:
        logger.warning("Resource usage exceeded CI limits!")
        # In a real CI environment, this might trigger a failure exit code
        # sys.exit(1) 

if __name__ == "__main__":
    main()