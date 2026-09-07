import json
import os
import sys
import csv
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np


def load_processed_logs(data_dir: str) -> List[Dict[str, Any]]:
    """Load all processed execution logs from the specified directory."""
    logs = []
    log_dir = Path(data_dir)
    if not log_dir.exists():
        return logs

    for file_path in log_dir.glob("*.json"):
        with open(file_path, "r") as f:
            try:
                data = json.load(f)
                logs.append(data)
            except json.JSONDecodeError:
                continue
    return logs


def calculate_error_rate(logs: List[Dict[str, Any]], reduction_pct: float) -> float:
    """Calculate error rate for a specific reduction percentage."""
    relevant_logs = [
        log
        for log in logs
        if abs(log.get("context_reduction_pct", 0) - reduction_pct) < 0.01
    ]
    if not relevant_logs:
        return 0.0

    violations = sum(1 for log in relevant_logs if log.get("policy_violations", []))
    return violations / len(relevant_logs)


def get_unique_reduction_pcts(logs: List[Dict[str, Any]]) -> List[float]:
    """Get unique reduction percentages from logs."""
    pcts = set()
    for log in logs:
        pct = log.get("context_reduction_pct", 0)
        if isinstance(pct, str) and pct == "[deferred]":
            continue
        pcts.add(round(float(pct), 2))
    return sorted(list(pcts))


def bootstrap_confidence_interval(
    data: List[float], n_resamples: int = 1000, confidence: float = 0.95
) -> Tuple[float, float]:
    """Calculate bootstrap confidence interval for a statistic."""
    if not data:
        return (0.0, 0.0)

    resampled_means = []
    for _ in range(n_resamples):
        sample = random.choices(data, k=len(data))
        resampled_means.append(np.mean(sample))

    lower = np.percentile(resampled_means, (1 - confidence) / 2 * 100)
    upper = np.percentile(resampled_means, (1 + confidence) / 2 * 100)
    return (lower, upper)


def save_regression_data_to_csv(
    data: List[Dict[str, Any]], output_path: str
) -> None:
    """Save regression data to a CSV file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["reduction_pct", "error_rate", "depth", "ci_lower", "ci_upper"]
        )
        writer.writeheader()
        writer.writerows(data)


def main() -> None:
    """Main entry point for regression data generation."""
    input_dir = "data/processed"
    output_path = "data/results/tradeoff_curve.csv"

    logs = load_processed_logs(input_dir)
    if not logs:
        print("No logs found to process.")
        return

    unique_pcts = get_unique_reduction_pcts(logs)
    results = []

    for pct in unique_pcts:
        error_rate = calculate_error_rate(logs, pct)
        # Calculate CI for error rate
        relevant_logs = [
            log
            for log in logs
            if abs(log.get("context_reduction_pct", 0) - pct) < 0.01
        ]
        error_values = [
            1.0 if log.get("policy_violations") else 0.0 for log in relevant_logs
        ]
        ci_lower, ci_upper = bootstrap_confidence_interval(error_values)

        # Use average depth for this reduction pct
        depths = [
            log.get("depth", 0)
            for log in relevant_logs
            if isinstance(log.get("depth"), (int, float))
        ]
        avg_depth = np.mean(depths) if depths else 0

        results.append(
            {
                "reduction_pct": round(pct, 2),
                "error_rate": round(error_rate, 4),
                "depth": round(avg_depth, 2),
                "ci_lower": round(ci_lower, 4),
                "ci_upper": round(ci_upper, 4),
            }
        )

    save_regression_data_to_csv(results, output_path)
    print(f"Regression data saved to {output_path}")


if __name__ == "__main__":
    main()
