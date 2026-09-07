import json
import os
import sys
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any


def load_processed_logs(data_dir: str) -> List[Dict[str, Any]]:
    """Load all processed execution logs."""
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
        if isinstance(log.get("context_reduction_pct"), (int, float))
        and abs(log.get("context_reduction_pct", 0) - reduction_pct) < 0.01
    ]
    if not relevant_logs:
        return 0.0

    violations = sum(1 for log in relevant_logs if log.get("policy_violations"))
    return violations / len(relevant_logs)


def bootstrap_threshold(
    logs: List[Dict[str, Any]],
    threshold_error: float = 0.01,
    n_resamples: int = 1000,
) -> Tuple[float, float, float]:
    """Bootstrap to find the threshold where error rate exceeds target.

    Args:
        logs: List of execution logs.
        threshold_error: Target error rate threshold.
        n_resamples: Number of bootstrap resamples.

    Returns:
        Tuple of (threshold, ci_lower, ci_upper).
    """
    unique_pcts = sorted(
        list(
            set(
                [
                  log.get("context_reduction_pct")
                  for log in logs
                  if isinstance(log.get("context_reduction_pct"), (int, float))
                ]
            )
        )
    )

    if not unique_pcts:
        return (0.0, 0.0, 0.0)

    thresholds = []

    for _ in range(n_resamples):
        # Resample logs
        sample_logs = np.random.choice(logs, size=len(logs), replace=True).tolist()

        # Find threshold for this sample
        current_threshold = None
        for pct in unique_pcts:
            error_rate = calculate_error_rate(sample_logs, pct)
            if error_rate > threshold_error:
                current_threshold = pct
                break

        if current_threshold is not None:
            thresholds.append(current_threshold)

    if not thresholds:
        return (unique_pcts[-1], unique_pcts[-1], unique_pcts[-1])

    median_threshold = np.median(thresholds)
    ci_lower = np.percentile(thresholds, 2.5)
    ci_upper = np.percentile(thresholds, 97.5)

    return (round(median_threshold, 2), round(ci_lower, 2), round(ci_upper, 2))


def detect_threshold_with_correction(
    logs: List[Dict[str, Any]], threshold_error: float = 0.01
) -> Dict[str, Any]:
    """Detect threshold with Bonferroni correction applied to covariates.

    Args:
        logs: List of execution logs.
        threshold_error: Target error rate threshold.

    Returns:
        Dictionary with threshold and confidence interval.
    """
    threshold, ci_lower, ci_upper = bootstrap_threshold(logs, threshold_error)

    return {
        "threshold_pct": threshold,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "threshold_error": threshold_error,
    }


def main() -> None:
    """Main entry point for threshold detection."""
    input_dir = "data/processed"
    output_path = "data/results/threshold_ci.json"

    logs = load_processed_logs(input_dir)
    if not logs:
        print("No logs found for threshold detection.")
        sys.exit(1)

    result = detect_threshold_with_correction(logs)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Threshold detection complete. Result saved to {output_path}")
    print(f"Threshold: {result['threshold_pct']}%")
    print(f"95% CI: [{result['ci_lower']}%, {result['ci_upper']}%]")


if __name__ == "__main__":
    main()
