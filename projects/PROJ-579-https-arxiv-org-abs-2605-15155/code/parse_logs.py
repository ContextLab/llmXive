"""
Parse real training logs from the SDAR pipeline execution.

This script reads the raw training log produced by the SDAR training run
(outputs/logs/train_raw.log) and extracts key metrics into structured
CSV and JSON formats for analysis and reporting.

Metrics extracted:
- SDAR Gate Loss
- RL Loss
- kl_divergence
- teacher_update_count
- gate_activation_rate

Output files:
- data/sdar_results.csv: Row-per-step metrics
- data/sdar_summary.json: Aggregated statistics
"""

import json
import os
import re
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_LOG_PATH = PROJECT_ROOT / "outputs" / "logs" / "train_raw.log"
CSV_OUTPUT_PATH = PROJECT_ROOT / "data" / "sdar_results.csv"
JSON_OUTPUT_PATH = PROJECT_ROOT / "data" / "sdar_summary.json"

# Regex patterns to extract metrics from log lines
# Expected log format examples:
# [INFO] Step 1: SDAR Gate Loss = 0.1234, RL Loss = 0.5678
# [INFO] Step 1: kl_divergence = 0.0123, teacher_update_count = 1
# [INFO] Step 1: gate_activation_rate = 0.456
PATTERNS = {
    "step": re.compile(r"Step\s+(\d+)"),
    "sdar_gate_loss": re.compile(r"SDAR\s+Gate\s+Loss\s*=\s*([\d.]+)"),
    "rl_loss": re.compile(r"RL\s+Loss\s*=\s*([\d.]+)"),
    "kl_divergence": re.compile(r"kl_divergence\s*=\s*([\d.]+)"),
    "teacher_update_count": re.compile(r"teacher_update_count\s*=\s*(\d+)"),
    "gate_activation_rate": re.compile(r"gate_activation_rate\s*=\s*([\d.]+)"),
}

def parse_log_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single log line to extract metrics.
    Returns a dict with step and extracted metrics, or None if no step found.
    """
    step_match = PATTERNS["step"].search(line)
    if not step_match:
        return None

    step = int(step_match.group(1))
    metrics = {"step": step}

    # Extract each metric
    for key, pattern in PATTERNS.items():
        if key == "step":
            continue
        match = pattern.search(line)
        if match:
            value = match.group(1)
            # Convert to appropriate type
            if key in ["teacher_update_count"]:
                metrics[key] = int(value)
            else:
                metrics[key] = float(value)

    # Only return if we found at least one metric besides step
    if len(metrics) > 1:
        return metrics
    return None

def parse_raw_log(log_path: Path) -> List[Dict[str, Any]]:
    """
    Parse the entire log file and return a list of metric dictionaries.
    """
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    results = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            parsed = parse_log_line(line)
            if parsed:
                results.append(parsed)

    return results

def compute_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute summary statistics from parsed results.
    """
    if not results:
        return {
            "total_steps": 0,
            "message": "No metrics found in log file",
        }

    # Initialize accumulators
    metrics_sum = {
        "sdar_gate_loss": 0.0,
        "rl_loss": 0.0,
        "kl_divergence": 0.0,
        "gate_activation_rate": 0.0,
    }
    teacher_update_count_sum = 0
    count = 0

    for row in results:
        count += 1
        if "sdar_gate_loss" in row:
            metrics_sum["sdar_gate_loss"] += row["sdar_gate_loss"]
        if "rl_loss" in row:
            metrics_sum["rl_loss"] += row["rl_loss"]
        if "kl_divergence" in row:
            metrics_sum["kl_divergence"] += row["kl_divergence"]
        if "gate_activation_rate" in row:
            metrics_sum["gate_activation_rate"] += row["gate_activation_rate"]
        if "teacher_update_count" in row:
            teacher_update_count_sum += row["teacher_update_count"]

    # Compute averages
    summary = {
        "paper": "Self-Distilled Agentic Reinforcement Learning",
        "simulation_type": "SDAR on ALFWorld (Mini-run)",
        "total_steps": count,
        "findings": [],
    }

    if count > 0:
        summary["findings"].append({
            "condition": "10-step mini-training run",
            "sdar_gate_loss_avg": metrics_sum["sdar_gate_loss"] / count if count > 0 else 0.0,
            "rl_loss_avg": metrics_sum["rl_loss"] / count if count > 0 else 0.0,
            "kl_divergence_avg": metrics_sum["kl_divergence"] / count if count > 0 else 0.0,
            "gate_activation_rate_avg": metrics_sum["gate_activation_rate"] / count if count > 0 else 0.0,
            "teacher_update_count_total": teacher_update_count_sum,
            "interpretation": "Metrics extracted from actual execution of SDAR training loop on ALFWorld environment.",
        })

    return summary

def write_csv(results: List[Dict[str, Any]], csv_path: Path) -> None:
    """
    Write parsed results to CSV file.
    """
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine all possible columns
    all_columns = ["step"]
    for row in results:
        for key in row.keys():
            if key not in all_columns:
                all_columns.append(key)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_columns)
        writer.writeheader()
        writer.writerows(results)

def write_json(summary: Dict[str, Any], json_path: Path) -> None:
    """
    Write summary statistics to JSON file.
    """
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

def main() -> None:
    """
    Main entry point for log parsing.
    """
    print(f"Reading log from: {RAW_LOG_PATH}")

    if not RAW_LOG_PATH.exists():
        print(f"ERROR: Log file not found at {RAW_LOG_PATH}")
        print("Please ensure the training script has been executed first.")
        return

    try:
        # Parse logs
        results = parse_raw_log(RAW_LOG_PATH)
        print(f"Parsed {len(results)} metric entries from log file.")

        if not results:
            print("WARNING: No metrics found in log file.")
            # Still create empty outputs
            write_csv([], CSV_OUTPUT_PATH)
            write_json({"message": "No metrics found"}, JSON_OUTPUT_PATH)
            return

        # Write CSV output
        write_csv(results, CSV_OUTPUT_PATH)
        print(f"Written CSV results to: {CSV_OUTPUT_PATH}")

        # Compute and write summary
        summary = compute_summary(results)
        write_json(summary, JSON_OUTPUT_PATH)
        print(f"Written summary to: {JSON_OUTPUT_PATH}")

        # Print summary stats
        if summary.get("findings"):
            finding = summary["findings"][0]
            print("\nSummary Statistics:")
            print(f"  Total Steps: {summary['total_steps']}")
            print(f"  Avg SDAR Gate Loss: {finding.get('sdar_gate_loss_avg', 'N/A'):.6f}")
            print(f"  Avg RL Loss: {finding.get('rl_loss_avg', 'N/A'):.6f}")
            print(f"  Avg KL Divergence: {finding.get('kl_divergence_avg', 'N/A'):.6f}")
            print(f"  Avg Gate Activation Rate: {finding.get('gate_activation_rate_avg', 'N/A'):.6f}")
            print(f"  Total Teacher Updates: {finding.get('teacher_update_count_total', 0)}")

    except Exception as e:
        print(f"ERROR during log parsing: {e}")
        raise

if __name__ == "__main__":
    main()