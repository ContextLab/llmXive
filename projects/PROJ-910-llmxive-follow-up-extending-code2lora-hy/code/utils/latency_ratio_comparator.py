"""
Latency Ratio Comparator for T049b.

Computes the latency reduction ratio (AST generation latency / baseline generation latency)
and stores a comparison report in data/results/generation_latency_comparison.json.
Verifies the reduction is >= 10x as required by SC-001.
"""
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from utils.logging import get_logger

logger = get_logger(__name__)


def ensure_results_dir() -> Path:
    """Ensure the results directory exists."""
    results_dir = Path("data/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir


def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_latency_ratio(
    ast_latency: float, baseline_latency: float
) -> Tuple[float, str]:
    """
    Compute the latency reduction ratio.

    Returns:
        Tuple of (ratio, status_message)
        ratio = baseline_latency / ast_latency (how many times faster AST is)
    """
    if ast_latency <= 0:
        raise ValueError("AST latency must be positive")
    if baseline_latency <= 0:
        raise ValueError("Baseline latency must be positive")

    ratio = baseline_latency / ast_latency
    return ratio, "success"


def generate_comparison_report(
    ast_latency: float,
    baseline_latency: float,
    ratio: float,
    threshold: float = 10.0,
) -> Dict[str, Any]:
    """Generate the comparison report dictionary."""
    meets_threshold = ratio >= threshold
    status = "PASS" if meets_threshold else "FAIL"

    report = {
        "ast_generation_latency_seconds": ast_latency,
        "baseline_generation_latency_seconds": baseline_latency,
        "latency_reduction_ratio": ratio,
        "threshold": threshold,
        "meets_threshold": meets_threshold,
        "status": status,
        "message": (
            f"AST generation is {ratio:.2f}x faster than baseline. "
            f"Threshold: {threshold}x. Result: {status}"
        ),
    }
    return report


def save_comparison_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save the comparison report to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Comparison report saved to {output_path}")


def run_latency_comparison() -> Dict[str, Any]:
    """
    Main entry point for T049b.

    Loads T040 (AST) and T049a (baseline) latency files, computes the ratio,
    and saves the comparison report.
    """
    results_dir = ensure_results_dir()

    # Paths to input files (T040 and T049a outputs)
    # Note: T040 output is generation_latency_comparison.json (from original plan)
    # But T049a specifically produces baseline_generation_latency.json
    # T040 might have produced a file, but we need the AST generation latency specifically.
    # Based on the task chain:
    # T040: "Output comparison report to data/results/generation_latency_comparison.json"
    # T049a: "save to data/results/baseline_generation_latency.json"
    # T049b: "Compute the latency reduction ratio (AST generation latency from T040 / baseline generation latency from T049a)"

    # We need the AST generation latency. T040's output file is generation_latency_comparison.json.
    # However, T049b says "AST generation latency from T040".
    # Let's assume T040 produced a file with the AST latency.
    # Actually, looking at the API surface, there is a `utils.latency_monitor` which has `run_latency_analysis`.
    # And `utils.latency_ratio_comparator` is the new file for T049b.

    # Let's assume the AST generation latency is stored in a file produced by T040.
    # The task T040 description says: "Output comparison report to data/results/generation_latency_comparison.json".
    # But T049b needs the AST latency specifically.
    # Let's assume T040 also saved the raw AST latency somewhere, or we extract it.
    # However, the task T049b description is: "Compute the latency reduction ratio (AST generation latency from T040 / baseline generation latency from T049a)".
    # This implies T040 output contains the AST generation latency.

    # Let's look at the API surface for `utils.latency_monitor`:
    # `measure_baseline_generation_latency` - this is for baseline.
    # `run_latency_analysis` - this might be for the AST side.

    # Let's assume T040 produced `data/results/ast_generation_latency.json` or similar.
    # But the task description for T040 says: "Output comparison report to data/results/generation_latency_comparison.json".
    # This is ambiguous. Let's assume the AST generation latency is in `data/results/ast_generation_latency.json`
    # or we need to read it from the T040 output.

    # Given the ambiguity, let's assume the AST generation latency is stored in:
    # `data/results/ast_generation_latency.json` (produced by T040's internal logic, or T040's output file).
    # But the task T040 says the output is `generation_latency_comparison.json`.
    # Let's assume T040's output file contains the AST latency.

    # Actually, let's re-read T040: "Implement ... to measure adapter generation latency ... and compare against the original ... Output comparison report to data/results/generation_latency_comparison.json".
    # So T040's output file `generation_latency_comparison.json` likely contains both AST and Baseline latencies?
    # But T049a produces `baseline_generation_latency.json`.
    # T049b says: "AST generation latency from T040 / baseline generation latency from T049a".
    # This implies T040's output file has the AST latency.

    # Let's assume T040's output file `generation_latency_comparison.json` has a key `ast_latency` or similar.
    # But to be safe, let's assume there is a file `data/results/ast_generation_latency.json` produced by T040.
    # If not, we might need to adjust.

    # Let's try to load `data/results/ast_generation_latency.json` first.
    # If that fails, try `data/results/generation_latency_comparison.json` and extract.

    ast_latency_path = Path("data/results/ast_generation_latency.json")
    baseline_latency_path = Path("data/results/baseline_generation_latency.json")

    ast_latency = None

    # Try to load AST latency
    if ast_latency_path.exists():
        ast_data = load_json_file(ast_latency_path)
        ast_latency = ast_data.get("ast_generation_latency_seconds")
        if ast_latency is None:
            # Try alternative key
            ast_latency = ast_data.get("latency_seconds")

    if ast_latency is None:
        # Try the T040 output file
        t040_output_path = Path("data/results/generation_latency_comparison.json")
        if t040_output_path.exists():
            t040_data = load_json_file(t040_output_path)
            ast_latency = t040_data.get("ast_generation_latency_seconds")
            if ast_latency is None:
                ast_latency = t040_data.get("ast_latency")

    if ast_latency is None:
        raise FileNotFoundError(
            "Could not find AST generation latency. "
            "Expected data/results/ast_generation_latency.json or data/results/generation_latency_comparison.json"
        )

    # Load baseline latency from T049a
    baseline_data = load_json_file(baseline_latency_path)
    baseline_latency = baseline_data.get("baseline_generation_latency_seconds")
    if baseline_latency is None:
        baseline_latency = baseline_data.get("latency_seconds")

    if baseline_latency is None:
        raise KeyError("Could not find baseline_generation_latency_seconds in baseline file")

    # Compute ratio
    ratio, status = compute_latency_ratio(ast_latency, baseline_latency)

    # Generate report
    report = generate_comparison_report(ast_latency, baseline_latency, ratio)

    # Save report
    output_path = Path("data/results/generation_latency_comparison.json")
    save_comparison_report(report, output_path)

    logger.info(f"Latency comparison complete. Ratio: {ratio:.2f}, Status: {report['status']}")

    return report


def main() -> None:
    """CLI entry point for T049b."""
    try:
        report = run_latency_comparison()
        print(f"Task T049b completed successfully.")
        print(f"Result: {report['status']}")
        print(f"Ratio: {report['latency_reduction_ratio']:.2f}x")
        print(f"Message: {report['message']}")
    except Exception as e:
        logger.error(f"Task T049b failed: {e}")
        raise


if __name__ == "__main__":
    main()
