"""
Report generation utilities.

This module is responsible for creating the final JSON reports that are
expected by the quick‑start run‑book.  In particular, for Task **T028** it
reads the robustness analysis results, applies a multiple‑comparison
correction (Bonferroni or Benjamini‑Hochberg), and writes the corrected
report to ``data/results/robustness_analysis.json``.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# ----------------------------------------------------------------------
# Helper functions for multiple‑comparison correction
# ----------------------------------------------------------------------


def _bonferroni_correction(p_values: List[float]) -> List[float]:
    """
    Apply the Bonferroni correction to a list of p‑values.

    Each p‑value is multiplied by the number of tests (len(p_values)).
    The corrected value is capped at 1.0.
    """
    m = len(p_values)
    return [min(p * m, 1.0) for p in p_values]


def _benjamini_hochberg_correction(p_values: List[float]) -> List[float]:
    """
    Apply the Benjamini‑Hochberg (FDR) correction.

    The algorithm sorts the p‑values, computes adjusted values, then
    restores the original order.
    """
    m = len(p_values)
    if m == 0:
        return []

    # Pair each p‑value with its original index
    indexed = list(enumerate(p_values))
    # Sort by p‑value
    indexed.sort(key=lambda x: x[1])

    corrected = [0.0] * m
    prev_adj_p = 0.0
    for rank, (orig_idx, p) in enumerate(indexed, start=1):
        adj_p = p * m / rank
        adj_p = min(adj_p, 1.0)
        # Ensure monotonicity
        adj_p = max(adj_p, prev_adj_p)
        corrected[orig_idx] = adj_p
        prev_adj_p = adj_p

    return corrected


# ----------------------------------------------------------------------
# Core report generation logic
# ----------------------------------------------------------------------


def _load_robustness_results(path: Path) -> Dict[str, Any]:
    """
    Load the robustness analysis JSON file.

    The expected structure is either:
    * a list of result dictionaries, each containing a ``p_value`` key, or
    * a dictionary with a top‑level ``results`` key that holds such a list.

    The function returns a dictionary with a ``results`` list for uniform
    downstream processing.
    """
    if not path.is_file():
        logging.error("Robustness analysis file not found at %s", path)
        return {"results": []}

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return {"results": data}
    if isinstance(data, dict) and "results" in data and isinstance(data["results"], list):
        return {"results": data["results"]}

    # Fallback: treat the whole dict as a single result entry
    return {"results": [data]}


def _apply_correction(
    results: List[Dict[str, Any]],
    method: str = "bonferroni",
) -> List[Dict[str, Any]]:
    """
    Apply the requested correction method to the ``p_value`` field of each
    result dictionary.  The corrected value is stored under the key
    ``corrected_p_value`` and the original p‑value is retained.

    Parameters
    ----------
    results : list of dict
        Each dict must contain a numeric ``p_value`` entry.
    method : {"bonferroni", "fdr"}
        ``bonferroni`` – classic family‑wise error control.
        ``fdr`` – Benjamini‑Hochberg false discovery rate control.
    """
    p_vals = [float(r.get("p_value", 0.0)) for r in results]

    if method == "bonferroni":
        corrected = _bonferroni_correction(p_vals)
    else:  # method == "fdr"
        corrected = _benjamini_hochberg_correction(p_vals)

    for r, pcorr in zip(results, corrected):
        r["corrected_p_value"] = pcorr

    return results


def generate_robustness_report(
    input_path: Path,
    output_path: Path,
    correction_method: str = "bonferroni",
) -> None:
    """
    Public function used by the quick‑start script and by unit tests.

    It reads the raw robustness results, applies the chosen multiple‑
    comparison correction, and writes the enriched JSON back to
    ``output_path`` (overwriting any existing file).

    The function logs progress and returns ``None``; any I/O errors raise
    the usual exceptions so that the CI can surface them.
    """
    logging.info("Loading robustness results from %s", input_path)
    data = _load_robustness_results(input_path)

    results = data.get("results", [])
    if not results:
        logging.warning("No robustness results to correct – writing empty report.")
    else:
        logging.info(
            "Applying %s correction to %d p‑values.", correction_method, len(results)
        )
        results = _apply_correction(results, method=correction_method)

    # Preserve any additional top‑level keys that were present in the original file
    output_data = {k: v for k, v in data.items() if k != "results"}
    output_data["results"] = results

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    logging.info("Robustness report with corrected p‑values written to %s", output_path)


# ----------------------------------------------------------------------
# Script entry‑point
# ----------------------------------------------------------------------


def main() -> None:
    """
    Entry point used by ``python -m src.report.generate`` and by the
    quick‑start run‑book.

    The script expects the robustness analysis JSON to be located at
    ``data/results/robustness_analysis.json``.  It writes the corrected
    version to the same location (overwriting the original file).
    """
    setup_logging()
    base_dir = Path(__file__).resolve().parents[3]  # project root
    input_file = base_dir / "data" / "results" / "robustness_analysis.json"
    output_file = input_file  # overwrite in‑place

    # Choose correction method based on an environment variable; default to Bonferroni.
    method = os.getenv("MULTIPLE_COMPARISON_METHOD", "bonferroni").lower()
    if method not in {"bonferroni", "fdr"}:
        logging.warning(
            "Unsupported correction method '%s' – falling back to Bonferroni.", method
        )
        method = "bonferroni"

    generate_robustness_report(input_file, output_file, correction_method=method)


# Helper to ensure consistent logging configuration when the module is
# executed directly.
def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


if __name__ == "__main__":
    main()
