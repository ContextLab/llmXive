"""
Report generation utilities for the project.

This module provides functions to generate JSON reports from analysis
results.  The primary focus of task T028 is to implement a robustness
analysis report that applies a multiple‑comparisons correction (Bonferroni
or Benjamini‑Hochberg) to the per‑modality correlation p‑values produced
by the robustness pipeline.

The function ``generate_robustness_report`` reads the raw correlation
metrics (expected to be a list of dictionaries with at least the keys
``modality`` and ``p_value``) from
``data/results/correlation_metrics.json`` and writes a corrected report to
``data/results/robustness_analysis.json``.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def _load_json(path: Path) -> Any:
    """Utility to load a JSON file, returning ``None`` if the file does not exist."""
    if not path.is_file():
        logger.error(f"Expected JSON file not found: {path}")
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        logger.error(f"Failed to decode JSON from {path}: {exc}")
        return None


def _save_json(data: Any, path: Path) -> None:
    """Utility to write ``data`` as pretty‑printed JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Wrote JSON report to {path}")


def _apply_bonferroni(p_values: List[float]) -> List[float]:
    """Bonferroni correction – multiply each p‑value by the number of tests."""
    m = len(p_values)
    return [min(p * m, 1.0) for p in p_values]


def _apply_bh(p_values: List[float]) -> List[float]:
    """
    Benjamini‑Hochberg (BH) false discovery rate correction.

    Returns a list of adjusted p‑values preserving the original order.
    """
    m = len(p_values)
    # Sort p‑values while keeping original indices
    sorted_indices = sorted(range(m), key=lambda i: p_values[i])
    sorted_p = [p_values[i] for i in sorted_indices]

    # Compute BH adjusted values (ascending order)
    bh_adj = [0.0] * m
    min_adj = 1.0
    for rank in range(m, 0, -1):
        i = rank - 1
        p = sorted_p[i]
        adj = p * m / rank
        min_adj = min(min_adj, adj)
        bh_adj[i] = min_adj

    # Re‑order to original indexing
    adjusted = [0.0] * m
    for orig_idx, sorted_idx in enumerate(sorted_indices):
        adjusted[sorted_idx] = min(bh_adj[orig_idx], 1.0)
    return adjusted


def generate_robustness_report(
    correlation_file: Path = Path("data/results/correlation_metrics.json"),
    output_file: Path = Path("data/results/robustness_analysis.json"),
    method: str = "bonferroni",
) -> None:
    """
    Generate a robustness analysis JSON report with multiple‑comparisons correction.

    Parameters
    ----------
    correlation_file : Path
        Path to the JSON file containing raw per‑modality correlation results.
        Expected format:
        ``[
            {"modality": "visual", "r": 0.32, "p_value": 0.045, ...},
            {"modality": "auditory", "r": -0.12, "p_value": 0.67, ...}
         ]``
    output_file : Path
        Destination path for the corrected report.
    method : str, optional
        Correction method – ``"bonferroni"`` (default) or ``"bh"`` (Benjamini‑Hochberg).

    The function writes a list of dictionaries to ``output_file``.  Each entry
    contains the original keys plus an additional ``p_corrected`` field.
    """
    logger.info("Generating robustness report with %s correction", method)

    raw_data = _load_json(correlation_file)
    if raw_data is None:
        # No input – produce an empty but valid JSON list so downstream scripts
        # do not fail with a missing file.
        logger.warning("No correlation data found; writing empty robustness report.")
        _save_json([], output_file)
        return

    if not isinstance(raw_data, list) or not raw_data:
        logger.warning("Correlation file contains no entries; writing empty robustness report.")
        _save_json([], output_file)
        return

    # Extract p‑values, ignoring entries where p_value is missing or not numeric.
    p_vals: List[float] = []
    valid_indices: List[int] = []
    for idx, entry in enumerate(raw_data):
        p = entry.get("p_value")
        if isinstance(p, (int, float)):
            p_vals.append(float(p))
            valid_indices.append(idx)

    if not p_vals:
        logger.warning("No valid p‑values found in correlation data; writing empty robustness report.")
        _save_json([], output_file)
        return

    # Apply the requested correction
    if method.lower() == "bonferroni":
        corrected = _apply_bonferroni(p_vals)
    elif method.lower() in {"bh", "benjamini-hochberg"}:
        corrected = _apply_bh(p_vals)
    else:
        logger.error("Unsupported correction method: %s", method)
        raise ValueError(f"Unsupported correction method: {method}")

    # Build the output list, preserving the original ordering
    corrected_entries: List[Dict[str, Any]] = []
    corr_iter = iter(corrected)
    for idx, entry in enumerate(raw_data):
        new_entry = dict(entry)  # shallow copy
        if idx in valid_indices:
            new_entry["p_corrected"] = next(corr_iter)
        else:
            new_entry["p_corrected"] = None
        corrected_entries.append(new_entry)

    _save_json(corrected_entries, output_file)


def main() -> None:
    """
    CLI entry point used by the project's quick‑start script.

    It simply forwards to :func:`generate_robustness_report` using the default
    locations and the Bonferroni method.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    generate_robustness_report()


if __name__ == "__main__":
    main()