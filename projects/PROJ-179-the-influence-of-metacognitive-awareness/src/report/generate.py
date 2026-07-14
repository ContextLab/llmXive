"""
src/report/generate.py

Report generation utilities for the project.

This module currently provides functionality to generate a robustness analysis
report that applies a multiple‑comparisons correction (Bonferroni or
Benjamini‑Hochberg) to the p‑values obtained from the modality‑specific
correlation analysis.

The script is intended to be executed directly:

    python -m src.report.generate

When run, it reads the raw robustness results produced by
``src.analysis.robustness`` (expected at ``data/results/robustness_analysis.json``),
applies the selected correction, and overwrites the same file with the
corrected results.

The JSON schema after correction looks like:

{
    "visual": {
        "r": <float>,
        "p_raw": <float>,
        "p_corrected": <float>
    },
    "auditory": {
        "r": <float>,
        "p_raw": <float>,
        "p_corrected": <float>
    },
    "correction_method": "bonferroni" | "benjamini-hochberg",
    "num_comparisons": 2
}

The implementation purposefully avoids hard‑coding any assumptions about the
exact keys written by the robustness analysis script – it works with any
mapping that contains a ``p`` (or ``p_raw``) entry for each modality.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_raw_results(filepath: Path) -> Dict:
    """
    Load the raw robustness analysis JSON.

    Parameters
    ----------
    filepath : Path
        Path to the JSON file produced by ``src.analysis.robustness``.

    Returns
    ----------
    dict
        Parsed JSON content.
    """
    if not filepath.is_file():
        logger.error(f"Robustness results file not found: {filepath}")
        raise FileNotFoundError(f"Robustness results file not found: {filepath}")

    with filepath.open("r", encoding="utf-8") as f:
        data = json.load(f)

    logger.info(f"Loaded raw robustness results from {filepath}")
    return data

def _extract_p_values(data: Dict) -> Tuple[List[float], List[str]]:
    """
    Extract raw p‑values and the associated modality keys from the data.

    The function is tolerant to a few common naming conventions:
    - ``p`` or ``p_raw`` for the raw p‑value.
    - The top‑level keys are assumed to be modality identifiers (e.g.
      ``visual`` and ``auditory``).

    Parameters
    ----------
    data : dict
        The raw robustness JSON.

    Returns
    ----------
    Tuple[List[float], List[str]]
        A list of p‑values and the corresponding modality keys in the same
        order.
    """
    p_values = []
    modalities = []
    for modality, subdict in data.items():
        if not isinstance(subdict, dict):
            continue
        # Accept either "p" or "p_raw"
        raw_p = subdict.get("p") if "p" in subdict else subdict.get("p_raw")
        if raw_p is None:
            logger.warning(f"No p‑value found for modality '{modality}'. Skipping.")
            continue
        try:
            p_val = float(raw_p)
        except (TypeError, ValueError):
            logger.warning(f"Invalid p‑value for modality '{modality}': {raw_p}")
            continue
        p_values.append(p_val)
        modalities.append(modality)

    if not p_values:
        logger.error("No valid p‑values extracted from robustness results.")
        raise ValueError("No valid p‑values extracted from robustness results.")

    return p_values, modalities

def _bonferroni_correction(p_vals: List[float], m: int) -> List[float]:
    """
    Apply Bonferroni correction.

    Parameters
    ----------
    p_vals : List[float]
        Raw p‑values.
    m : int
        Number of comparisons.

    Returns
    ----------
    List[float]
        Bonferroni‑corrected p‑values, capped at 1.0.
    """
    corrected = [min(p * m, 1.0) for p in p_vals]
    logger.debug(f"Bonferroni corrected values: {corrected}")
    return corrected

def _benjamini_hochberg_correction(p_vals: List[float], m: int) -> List[float]:
    """
    Apply Benjamini‑Hochberg (FDR) correction.

    Parameters
    ----------
    p_vals : List[float]
        Raw p‑values.
    m : int
        Number of comparisons.

    Returns
    ----------
    List[float]
        BH‑corrected p‑values in the original order.
    """
    # Pair each p‑value with its original index
    indexed = list(enumerate(p_vals))
    # Sort by p‑value
    indexed.sort(key=lambda x: x[1])

    corrected = [0.0] * m
    prev_correction = 0.0
    for rank, (orig_idx, p) in enumerate(indexed, start=1):
        # Compute the BH factor
        bh_val = p * m / rank
        # Ensure monotonicity (non‑decreasing when moving from smallest to largest)
        bh_val = max(bh_val, prev_correction)
        bh_val = min(bh_val, 1.0)
        corrected[orig_idx] = bh_val
        prev_correction = bh_val

    logger.debug(f"Benjamini‑Hochberg corrected values: {corrected}")
    return corrected

def _apply_correction(
    p_vals: List[float],
    method: str = "bonferroni",
) -> List[float]:
    """
    Dispatch to the selected correction method.

    Parameters
    ----------
    p_vals : List[float]
        Raw p‑values.
    method : str, optional
        ``'bonferroni'`` or ``'benjamini-hochberg'``. Defaults to
        ``'bonferroni'``.

    Returns
    ----------
    List[float]
        Corrected p‑values.
    """
    m = len(p_vals)
    method = method.lower()
    if method == "bonferroni":
        return _bonferroni_correction(p_vals, m)
    elif method in ("benjamini-hochberg", "bh", "fdr"):
        return _benjamini_hochberg_correction(p_vals, m)
    else:
        logger.error(f"Unsupported correction method: {method}")
        raise ValueError(f"Unsupported correction method: {method}")

def _write_corrected_results(
    original_data: Dict,
    corrected_p: List[float],
    modalities: List[str],
    method: str,
    output_path: Path,
) -> None:
    """
    Merge corrected p‑values back into the original structure and write JSON.

    Parameters
    ----------
    original_data : dict
        The raw robustness JSON.
    corrected_p : List[float]
        Corrected p‑values aligned with ``modalities``.
    modalities : List[str]
        Modality keys in the same order as ``corrected_p``.
    method : str
        Correction method name.
    output_path : Path
        Destination file (overwrites if exists).
    """
    for modality, p_corr in zip(modalities, corrected_p):
        subdict = original_data.get(modality, {})
        # Preserve the original raw p‑value under a canonical name
        raw_p = subdict.get("p") if "p" in subdict else subdict.get("p_raw")
        subdict["p_raw"] = raw_p
        subdict["p_corrected"] = p_corr
        original_data[modality] = subdict

    original_data["correction_method"] = method
    original_data["num_comparisons"] = len(modalities)

    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(original_data, f, indent=4)

    logger.info(f"Corrected robustness report written to {output_path}")

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def generate_robustness_report(
    correction_method: str = "bonferroni",
    input_path: str = "data/results/robustness_analysis.json",
    output_path: str = "data/results/robustness_analysis.json",
) -> None:
    """
    Generate the robustness analysis report with multiple‑comparisons correction.

    The function reads the raw results, applies the requested correction,
    and writes the corrected JSON back to ``output_path`` (by default the same
    file as the input, overwriting it).

    Parameters
    ----------
    correction_method : str, optional
        ``'bonferroni'`` (default) or ``'benjamini-hochberg'``.
    input_path : str, optional
        Path to the raw robustness JSON produced by the analysis step.
    output_path : str, optional
        Destination path for the corrected report.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)

    raw_data = _load_raw_results(input_file)
    raw_p_vals, modalities = _extract_p_values(raw_data)
    corrected_p_vals = _apply_correction(raw_p_vals, method=correction_method)

    _write_corrected_results(
        original_data=raw_data,
        corrected_p=corrected_p_vals,
        modalities=modalities,
        method=correction_method,
        output_path=output_file,
    )

# ----------------------------------------------------------------------
# Command‑line entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Simple CLI that forwards arguments to ``generate_robustness_report``.

    Usage examples:
        python -m src.report.generate               # default Bonferroni
        python -m src.report.generate bh            # Benjamini‑Hochberg
    """
    import sys

    method = "bonferroni"
    if len(sys.argv) > 1:
        method = sys.argv[1]

    logger.info(f"Generating robustness report using '{method}' correction.")
    generate_robustness_report(correction_method=method)

if __name__ == "__main__":
    main()
