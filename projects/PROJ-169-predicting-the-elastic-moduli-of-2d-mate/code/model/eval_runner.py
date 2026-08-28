"""Evaluation runner with scientific integrity disclaimers."""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.config import get_config
from utils.logger import log_operation
from utils.disclaimer_template import DISCLAIMER_TEXT, FEYNMAN_QUOTE

def load_json_file(path: str) -> Dict[str, Any]:
    """Load a JSON file."""
    with open(path, "r") as f:
        return json.load(f)

def save_json_file(path: str, data: Dict[str, Any]):
    """Save a JSON file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def calculate_mape(predictions: List[float], targets: List[float]) -> float:
    """Calculate Mean Absolute Percentage Error."""
    if len(predictions) != len(targets):
        raise ValueError("Predictions and targets must have the same length")
    errors = [abs(p - t) / abs(t) if t != 0 else 0 for p, t in zip(predictions, targets)]
    return sum(errors) / len(errors) if errors else 0.0

@log_operation
def run_success_criteria_assertion(mape: float, threshold: float = 0.15) -> Dict[str, Any]:
    """Run success criteria assertion with disclaimer."""
    result = {
        "mape": mape,
        "threshold": threshold,
        "passed": mape < threshold,
        "disclaimer": DISCLAIMER_TEXT + "\n\n" + FEYNMAN_QUOTE
    }
    if not result["passed"]:
        raise ValueError(f"SC-002 Failed: Inter-family MAPE ({mape:.4f}) >= {threshold:.2f}")
    return result

def main():
    """CLI entry point for evaluation runner."""
    parser = argparse.ArgumentParser(description="Run evaluation with disclaimers")
    parser.add_argument("--predictions", type=str, required=True, help="Path to predictions file")
    parser.add_argument("--split", type=str, required=True, help="Path to split indices file")
    parser.add_argument("--output", type=str, default="data/results/eval_report.json", help="Output report path")
    parser.add_argument("--threshold", type=float, default=0.15, help="MAPE threshold")

    args = parser.parse_args()

    # Load data
    predictions_data = load_json_file(args.predictions)
    split_data = load_json_file(args.split)

    # Extract test predictions and targets
    test_indices = split_data.get("test_indices", [])
    test_predictions = predictions_data.get("predictions", [])[test_indices]
    test_targets = predictions_data.get("targets", [])[test_indices]

    # Calculate MAPE
    mape = calculate_mape(test_predictions, test_targets)

    # Run assertion
    result = run_success_criteria_assertion(mape, args.threshold)
    result["report"] = f"Scientific Integrity Statement:\n{DISCLAIMER_TEXT}\n\nRichard Feynman Quote:\n{FEYNMAN_QUOTE}"

    # Save report
    save_json_file(args.output, result)
    print(f"Evaluation report written to {args.output}")

if __name__ == "__main__":
    main()