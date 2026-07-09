"""
T031: Generate final analysis report with compliance status.

Aggregates metrics, p-values, flags, and limitations from previous stages.
Explicitly reads logs to verify SC-004 (runtime) and SC-005 (memory) compliance.
"""
import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional
import re

from config import is_synthetic, get_runtime_limit_hours, get_memory_limit_gb
from logging_config import get_logger

# Setup logging
logger = get_logger(__name__)

RESULTS_DIR = Path("data/results")
LOG_DIR = Path("logs")

def parse_log_for_memory(log_file_path: Path) -> Optional[float]:
    """
    Parse the log file to find the peak RAM usage in GB.
    Looks for patterns like 'RAM usage: X.XX GB' or 'Peak RAM: X.XX GB'.
    Returns None if not found or parsing fails.
    """
    if not log_file_path.exists():
        logger.warning(f"Log file not found: {log_file_path}")
        return None

    peak_ram = 0.0
    # Regex to capture float values associated with RAM keywords
    pattern = re.compile(r'(?:Peak RAM|RAM usage|Current RAM)[\s:]+([0-9.]+)\s*GB', re.IGNORECASE)

    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                match = pattern.search(line)
                if match:
                    try:
                        val = float(match.group(1))
                        if val > peak_ram:
                            peak_ram = val
                    except ValueError:
                        continue
    except Exception as e:
        logger.error(f"Error reading log file {log_file_path}: {e}")
        return None

    return peak_ram if peak_ram > 0 else None

def parse_log_for_runtime(log_file_path: Path) -> Optional[float]:
    """
    Parse the log file to find the total runtime in hours.
    Looks for patterns like 'Total runtime: X.XX hours' or 'Elapsed: X.XX hours'.
    Returns None if not found.
    """
    if not log_file_path.exists():
        logger.warning(f"Log file not found: {log_file_path}")
        return None

    total_hours = 0.0
    # Regex to capture float values associated with time keywords
    pattern = re.compile(r'(?:Total runtime|Elapsed time|Runtime)[\s:]+([0-9.]+)\s*hours?', re.IGNORECASE)

    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                match = pattern.search(line)
                if match:
                    try:
                        val = float(match.group(1))
                        if val > total_hours:
                            total_hours = val
                    except ValueError:
                        continue
    except Exception as e:
        logger.error(f"Error reading log file {log_file_path}: {e}")
        return None

    return total_hours if total_hours > 0 else None

def load_json_safely(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if it doesn't exist or is invalid."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None

def aggregate_metrics() -> Dict[str, Any]:
    """
    Aggregate metrics from various result files into a single dictionary.
    """
    metrics = {
        "model_results": None,
        "robustness_results": None,
        "sensitivity_results": None,
        "pca_results": None,
        "vif_report": None,
        "validation_results": None,
        "gaps": None
    }

    # Map expected file names to keys
    file_mappings = [
        ("model_results.json", "model_results"),
        ("robustness_results.json", "robustness_results"),
        ("sensitivity_analysis.csv", "sensitivity_results"), # CSV handled differently if needed, but stored as path or flag here
        ("pca_metrics.json", "pca_results"),
        ("descriptive_vif_report.json", "vif_report"),
        ("external_validation.json", "validation_results"),
        ("gaps.json", "gaps")
    ]

    for filename, key in file_mappings:
        if filename.endswith('.csv'):
            # For CSV, just check existence and store path or a boolean flag
            f_path = RESULTS_DIR / filename
            metrics[key] = {
                "exists": f_path.exists(),
                "path": str(f_path) if f_path.exists() else None
            }
        else:
            data = load_json_safely(RESULTS_DIR / filename)
            metrics[key] = data

    return metrics

def generate_report() -> Dict[str, Any]:
    """
    Generate the final analysis report including compliance status.
    """
    start_time = time.time()
    logger.info("Starting final analysis report generation (T031).")

    # 1. Determine flags
    is_synthetic_mode = is_synthetic()
    is_pilot = True # Assuming this is a pilot study based on context
    
    # Check for validation gap from gaps.json
    gaps_data = load_json_safely(RESULTS_DIR / "gaps.json")
    validation_gap = gaps_data.get("validation_gap", False) if gaps_data else False

    # 2. Aggregate metrics
    aggregated_metrics = aggregate_metrics()

    # 3. Compute Compliance Status
    # Find the most recent log file in the logs directory
    log_files = list(LOG_DIR.glob("*.log"))
    if not log_files:
        logger.warning("No log files found to parse for compliance.")
        peak_ram_gb = None
        total_runtime_hours = None
    else:
        # Sort by modification time, get latest
        latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
        peak_ram_gb = parse_log_for_memory(latest_log)
        total_runtime_hours = parse_log_for_runtime(latest_log)

    # Define limits
    runtime_limit = get_runtime_limit_hours()
    memory_limit = get_memory_limit_gb()

    # Compute booleans
    # If we couldn't parse logs, we can't confirm compliance, so default to False or handle gracefully
    runtime_ok = False
    memory_ok = False

    if total_runtime_hours is not None:
        runtime_ok = total_runtime_hours <= runtime_limit
        logger.info(f"Runtime check: {total_runtime_hours:.2f}h <= {runtime_limit}h -> {runtime_ok}")
    else:
        logger.warning("Could not determine runtime from logs.")

    if peak_ram_gb is not None:
        memory_ok = peak_ram_gb <= memory_limit
        logger.info(f"Memory check: {peak_ram_gb:.2f}GB <= {memory_limit}GB -> {memory_ok}")
    else:
        logger.warning("Could not determine peak RAM from logs.")

    compliance_status = {
        "runtime_ok": runtime_ok,
        "memory_ok": memory_ok,
        "total_runtime_hours": total_runtime_hours,
        "peak_ram_gb": peak_ram_gb,
        "runtime_limit_hours": runtime_limit,
        "memory_limit_gb": memory_limit
    }

    # 4. Compile Limitations
    limitations = []
    if is_synthetic_mode:
        limitations.append("Analysis performed in Methodology Validation Mode using synthetic data.")
    if validation_gap:
        limitations.append("External validation metric (e.g., Return-to-Work) not found in dataset.")
    if not runtime_ok:
        limitations.append(f"Runtime exceeded limit of {runtime_limit} hours.")
    if not memory_ok:
        limitations.append(f"Peak memory exceeded limit of {memory_limit} GB.")
    if not limitations:
        limitations.append("No significant limitations detected within resource constraints.")

    # 5. Construct Final Report
    report = {
        "report_type": "Final Analysis Report",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "flags": {
            "is_synthetic": is_synthetic_mode,
            "is_pilot": is_pilot,
            "validation_gap": validation_gap
        },
        "compliance_status": compliance_status,
        "metrics": aggregated_metrics,
        "limitations": limitations
    }

    # 6. Write Report
    output_path = RESULTS_DIR / "analysis_report.json"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Report generated successfully at {output_path}. Duration: {duration:.2f}s")

    return report

def main():
    """Entry point for T031."""
    # Ensure logs directory exists for parsing (even if empty)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        report = generate_report()
        print(f"Analysis report generated: {RESULTS_DIR / 'analysis_report.json'}")
        # Print compliance summary
        cs = report.get("compliance_status", {})
        print(f"Compliance: Runtime OK={cs.get('runtime_ok')}, Memory OK={cs.get('memory_ok')}")
    except Exception as e:
        logger.error(f"Failed to generate report: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()