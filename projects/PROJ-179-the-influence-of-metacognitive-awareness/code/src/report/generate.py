"""
Report generation utilities.

This module currently provides three public helpers:
  * ``generate_regression_analysis_report`` – reads the regression JSON output and
    returns the parsed data (used by unit tests).
  * ``generate_robustness_report`` – applies a multiple‑comparison correction
    (Bonferroni or Benjamini‑Hochberg) to the raw robustness results and writes a
    corrected JSON file.
  * ``main`` – a tiny CLI wrapper that forwards arguments to the appropriate
    generator.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Helper for regression analysis report (used by existing unit tests)
# --------------------------------------------------------------------------- #
def generate_regression_analysis_report(
    input_path: Path = Path("data/results/regression_analysis.json"),
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Load the regression analysis JSON file and return its contents.

    If ``output_path`` is supplied, the same data are written back to that file.
    This function is deliberately lightweight because the regression report
    format is already defined elsewhere in the pipeline.
    """
    if not input_path.is_file():
        logger.error(f"Regression analysis file not found: {input_path}")
        raise FileNotFoundError(str(input_path))

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    return data


# --------------------------------------------------------------------------- #
# Robustness analysis report with multiple‑comparison correction
# --------------------------------------------------------------------------- #
def _bonferroni_correction(p_values: List[float]) -> List[float]:
    """Simple Bonferroni correction."""
    m = len(p_values)
    return [min(p * m, 1.0) for p in p_values]


def _benjamini_hochberg_correction(p_values: List[float]) -> List[float]:
    """
    Benjamini‑Hochberg (BH) false discovery rate correction.

    The algorithm returns the adjusted p‑values in the original order.
    """
    m = len(p_values)
    if m == 0:
        return []

    # Pair each p‑value with its original index
    indexed = list(enumerate(p_values))
    # Sort by p‑value ascending
    indexed.sort(key=lambda x: x[1])

    corrected = [0.0] * m
    prev_b = 0.0
    for rank, (orig_idx, p) in enumerate(indexed, start=1):
        b = p * m / rank
        b = min(b, 1.0)
        # Ensure monotonicity (non‑decreasing when moving from smallest to largest)
        b = max(b, prev_b)
        corrected[orig_idx] = b
        prev_b = b

    return corrected


def generate_robustness_report(
    input_path: Path = Path("data/results/robustness_analysis.json"),
    output_path: Optional[Path] = None,
    method: str = "bonferroni",
) -> List[Dict[str, Any]]:
    """
    Apply a family‑wise error correction to robustness analysis results.

    Parameters
    ----------
    input_path : Path
        Path to the JSON file containing raw robustness results.  The file is
        expected to be a list of dictionaries, each with at least a ``p_value``
        field (float).

    output_path : Path | None
        Destination for the corrected results.  If ``None`` the function overwrites
        ``input_path``.

    method : {"bonferroni", "bh", "benjamini-hochberg"}
        Choice of correction method.  ``"bh"`` and ``"benjamini-hochberg"`` are
        treated identically.

    Returns
    -------
    List[Dict[str, Any]]
        The corrected result objects (same structure as the input, but with an
        additional ``p_value_corrected`` key).
    """
    if not input_path.is_file():
        logger.error(f"Robustness analysis file not found: {input_path}")
        raise FileNotFoundError(str(input_path))

    with open(input_path, "r", encoding="utf-8") as f:
        raw_results: List[Dict[str, Any]] = json.load(f)

    if not raw_results:
        logger.warning("Robustness analysis input is empty; nothing to correct.")
        corrected_results: List[Dict[str, Any]] = []
    else:
        # Extract p‑values, handling missing entries gracefully
        p_vals = [
            float(item.get("p_value", 0.0))
            for item in raw_results
        ]

        method_key = method.lower()
        if method_key in ("bonferroni",):
            corrected_p = _bonferroni_correction(p_vals)
        elif method_key in ("bh", "benjamini-hochberg", "benjamini_hochberg"):
            corrected_p = _benjamini_hochberg_correction(p_vals)
        else:
            logger.error(f"Unknown correction method: {method}")
            raise ValueError(f"Unsupported correction method: {method}")

        # Attach corrected p‑values to the original dictionaries
        corrected_results = []
        for original, corr_p in zip(raw_results, corrected_p):
            entry = original.copy()
            entry["p_value_corrected"] = corr_p
            entry["correction_method"] = method_key
            corrected_results.append(entry)

    # Determine where to write the corrected data
    dest_path = output_path or input_path
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(corrected_results, f, indent=2)

    logger.info(
        f"Robustness report written to {dest_path} using {method} correction."
    )
    return corrected_results


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    """
    Minimal command‑line interface.

    Example usage:
        python -m src.report.generate \\
            --input data/results/robustness_analysis.json \\
            --output data/results/robustness_analysis_corrected.json \\
            --method bh
    """
    parser = argparse.ArgumentParser(
        description="Generate corrected robustness analysis reports."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/results/robustness_analysis.json"),
        help="Path to raw robustness JSON results.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Destination for corrected JSON. Overwrites input if omitted.",
    )
    parser.add_argument(
        "--method",
        choices=["bonferroni", "bh", "benjamini-hochberg"],
        default="bonferroni",
        help="Multiple‑comparison correction method.",
    )
    args = parser.parse_args()
    generate_robustness_report(
        input_path=args.input,
        output_path=args.output,
        method=args.method,
    )


if __name__ == "__main__":
    # When the module is executed directly, run the CLI.
    main()