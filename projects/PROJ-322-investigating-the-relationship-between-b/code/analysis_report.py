import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional
from config import is_synthetic, get_runtime_limit_hours, get_memory_limit_gb
from logging_config import get_logger

# Constants for log parsing
LOG_FILE_PATH = Path("data/logs/pipeline.log")
RESULTS_DIR = Path("data/results")
REPORT_OUTPUT_PATH = RESULTS_DIR / "analysis_report.json"

# Paths to other potential outputs to aggregate
METRICS_RESULTS_PATH = RESULTS_DIR / "model_results.json"
ROBUSTNESS_RESULTS_PATH = RESULTS_DIR / "robustness_results.json"
SENSITIVITY_RESULTS_PATH = RESULTS_DIR / "sensitivity_analysis.csv"
BOOTSTRAP_RESULTS_PATH = RESULTS_DIR / "bootstrapped_ci.json"
VIF_REPORT_PATH = RESULTS_DIR / "descriptive_vif_report.json"
PCA_METRICS_PATH = RESULTS_DIR / "pca_metrics.json"
GAPS_PATH = RESULTS_DIR / "gaps.json"

def load_json_safely(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file if it exists, otherwise return None."""
    if not path.exists():
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logging.warning(f"Could not load {path}: {e}")
        return None

def parse_log_for_memory(log_path: Path) -> Optional[float]:
    """
    Parse the log file to find the peak RAM usage reported.
    Looks for patterns like 'Peak RAM: X GB' or 'Memory usage: X GB'.
    Returns None if not found.
    """
    if not log_path.exists():
        return None
    
    peak_ram = 0.0
    try:
        with open(log_path, 'r') as f:
            for line in f:
                # Simple heuristic: look for "Peak RAM" or "Memory usage" in the line
                # Assuming log format: "INFO ... Peak RAM: 4.5 GB"
                if "Peak RAM" in line or "Memory usage" in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.replace('.', '').isdigit() or (part.replace('.', '').isdigit() and i > 0):
                            try:
                                val = float(part)
                                if val > peak_ram:
                                    peak_ram = val
                            except ValueError:
                                continue
    except IOError as e:
        logging.error(f"Could not read log file {log_path}: {e}")
        return None
    
    return peak_ram if peak_ram > 0 else None

def parse_log_for_runtime(log_path: Path) -> Optional[float]:
    """
    Parse the log file to find total runtime.
    Assumes the log starts with a timestamp or we track start/end.
    If explicit 'Total runtime' log exists, use that.
    Otherwise, return None and caller might need to calculate externally.
    """
    if not log_path.exists():
        return None
    
    total_runtime = None
    try:
        with open(log_path, 'r') as f:
            content = f.read()
            # Look for explicit runtime log
            if "Total runtime" in content:
                # Heuristic: find the number following "Total runtime"
                import re
                match = re.search(r"Total runtime[:\s]+([\d.]+)\s*hours?", content, re.IGNORECASE)
                if match:
                    total_runtime = float(match.group(1))
            elif "Elapsed time" in content:
                match = re.search(r"Elapsed time[:\s]+([\d.]+)\s*hours?", content, re.IGNORECASE)
                if match:
                    total_runtime = float(match.group(1))
    except IOError as e:
        logging.error(f"Could not read log file {log_path}: {e}")
    
    return total_runtime

def aggregate_metrics() -> Dict[str, Any]:
    """
    Aggregate results from various JSON/CSV files into a single metrics dictionary.
    """
    metrics = {
        "statistical_model": load_json_safely(METRICS_RESULTS_PATH),
        "robustness": load_json_safely(ROBUSTNESS_RESULTS_PATH),
        "sensitivity": None,
        "bootstrap": load_json_safely(BOOTSTRAP_RESULTS_PATH),
        "collinearity": None,
        "pca": load_json_safely(PCA_METRICS_PATH),
        "validation_gaps": load_json_safely(GAPS_PATH)
    }

    # Handle CSV for sensitivity
    if SENSITIVITY_RESULTS_PATH.exists():
        try:
            import pandas as pd
            df = pd.read_csv(SENSITIVITY_RESULTS_PATH)
            # Convert to list of dicts for JSON serialization
            metrics["sensitivity"] = df.to_dict(orient='records')
        except Exception as e:
            logging.warning(f"Could not load sensitivity CSV: {e}")

    # Determine collinearity report
    if load_json_safely(VIF_REPORT_PATH):
        metrics["collinearity"] = "descriptive_report"
    elif load_json_safely(PCA_METRICS_PATH):
        metrics["collinearity"] = "pca_applied"
    else:
        metrics["collinearity"] = "none"

    return metrics

def generate_report() -> Dict[str, Any]:
    """
    Generate the final analysis report including metrics, flags, and compliance status.
    """
    logger = get_logger("analysis_report")
    logger.info("Generating final analysis report...")

    # 1. Aggregate Metrics
    aggregated_metrics = aggregate_metrics()

    # 2. Flags
    flags = {
        "is_synthetic": is_synthetic(),
        "pilot": True,  # Assumed pilot based on context, could be dynamic
        "validation_gap": aggregated_metrics.get("validation_gaps") is not None
    }

    # 3. Limitations
    limitations = []
    if flags["is_synthetic"]:
        limitations.append("Results derived from synthetic data for methodology validation.")
    if flags["validation_gap"]:
        limitations.append("External validation metric not found in available datasets.")
    if aggregated_metrics.get("collinearity") == "descriptive_report":
        limitations.append("Multicollinearity detected; descriptive report provided instead of PCA.")
    
    # 4. Compliance Status
    # Parse logs for runtime and memory
    peak_ram_gb = parse_log_for_memory(LOG_FILE_PATH)
    total_runtime_hours = parse_log_for_runtime(LOG_FILE_PATH)

    # Limits from config
    mem_limit = get_memory_limit_gb()
    time_limit = get_runtime_limit_hours()

    # If logs don't have explicit values, we might default to False or handle gracefully
    # Assuming if we can't parse, we assume non-compliant for safety or mark as unknown
    runtime_ok = False
    memory_ok = False

    if total_runtime_hours is not None:
        runtime_ok = total_runtime_hours <= time_limit
    else:
        # If no log data, we can't confirm, but for the sake of the report structure:
        # If the script ran to completion, we might assume it was within limits if no crash?
        # Strictly, we should say unknown, but the task asks for booleans.
        # Let's assume if no log, we can't verify -> False (fail loud principle implies we need data)
        # However, to be helpful, if the script ran, maybe we assume it passed unless log says otherwise?
        # Better: If we can't parse, we mark as False and note in limitations.
        limitations.append("Runtime compliance could not be verified (missing log data).")

    if peak_ram_gb is not None:
        memory_ok = peak_ram_gb <= mem_limit
    else:
        limitations.append("Memory compliance could not be verified (missing log data).")

    compliance_status = {
        "runtime_ok": runtime_ok,
        "memory_ok": memory_ok
    }

    # 5. Construct Final Report
    report = {
        "report_metadata": {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "project_id": "PROJ-322",
            "task_id": "T031"
        },
        "flags": flags,
        "limitations": limitations,
        "compliance_status": compliance_status,
        "aggregated_metrics": aggregated_metrics
    }

    return report

def main():
    """
    Main entry point to generate and save the analysis report.
    """
    logger = get_logger("analysis_report")
    logger.info("Starting analysis report generation.")

    try:
        report = generate_report()
        
        # Ensure output directory exists
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Write report
        with open(REPORT_OUTPUT_PATH, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Analysis report successfully written to {REPORT_OUTPUT_PATH}")
        print(f"Report generated: {REPORT_OUTPUT_PATH}")
        
    except Exception as e:
        logger.error(f"Failed to generate analysis report: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()