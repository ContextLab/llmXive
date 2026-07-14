import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# The analysis modules provide the raw statistical results.
from src.analysis.correlation import compute_hold_out_metrics, load_trial_data
from src.analysis.robustness import run_robustness_analysis

# -------------------------------------------------------------------------
# Helper utilities
# -------------------------------------------------------------------------
def _load_json(path: Path) -> Any:
    """Load a JSON file, returning ``None`` if the file does not exist."""
    if not path.is_file():
        logging.warning(f"Expected file {path} not found.")
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as exc:
        logging.error(f"Failed to read JSON from {path}: {exc}")
        return None

def _write_json(data: Any, path: Path):
    """Write *data* as pretty‑printed JSON to *path*."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        logging.info(f"Wrote JSON report to {path}")
    except Exception as exc:
        logging.error(f"Failed to write JSON report to {path}: {exc}")

# -------------------------------------------------------------------------
# Primary analysis report
# -------------------------------------------------------------------------
def generate_primary_report():
    """
    Produce ``data/results/primary_analysis.json`` containing the correlation
    coefficient, its p‑value, and the 95 % confidence interval.

    The source data are taken from the correlation analysis output
    ``data/results/correlation.json`` (created by ``src.analysis.correlation``).
    If that file is missing, an empty report is written so downstream steps
    can still run without crashing.
    """
    src_path = Path("data/results/correlation.json")
    out_path = Path("data/results/primary_analysis.json")

    corr_data = _load_json(src_path) or {}
    # Ensure required keys exist; otherwise fill with ``None``.
    report = {
        "correlation_coefficient": corr_data.get("r"),
        "p_value": corr_data.get("p_value"),
        "ci_lower": corr_data.get("ci_lower"),
        "ci_upper": corr_data.get("ci_upper"),
    }
    _write_json(report, out_path)

# -------------------------------------------------------------------------
# Robustness analysis report (multiple‑comparison correction)
# -------------------------------------------------------------------------
def _apply_bonferroni(p_values: List[float]) -> List[float]:
    """Simple Bonferroni correction (family‑wise error rate)."""
    m = len(p_values)
    return [min(p * m, 1.0) for p in p_values]

def _apply_bh(p_values: List[float]) -> List[float]:
    """
    Benjamini‑Hochberg (BH) false discovery rate correction.
    Returns a list of corrected p‑values in the original order.
    """
    m = len(p_values)
    sorted_indices = sorted(range(m), key=lambda i: p_values[i])
    sorted_p = [p_values[i] for i in sorted_indices]
    corrected = [0.0] * m
    prev_b = 0.0
    for rank, (orig_idx, p) in enumerate(zip(sorted_indices, sorted_p), start=1):
        b = p * m / rank
        b = max(b, prev_b)  # enforce monotonicity
        corrected[orig_idx] = min(b, 1.0)
        prev_b = b
    return corrected

def generate_robustness_report(correction: str = "bonferroni"):
    """
    Load the raw robustness results, apply the requested multiple‑comparison
    correction, and write the corrected report to
    ``data/results/robustness_analysis.json``.

    Parameters
    ----------
    correction: str
        Either ``"bonferroni"`` or ``"bh"`` (Benjamini‑Hochberg).  Defaults to
        Bonferroni because it is the most conservative and requires no
        additional parameters.
    """
    # The robustness analysis script writes a JSON file with a list of
    # modality‑specific results.  The default location is
    # ``data/results/robustness_raw.json``; if that file does not exist we
    # fall back to the (possibly already‑corrected) ``robustness_analysis.json``.
    raw_path = Path("data/results/robustness_raw.json")
    out_path = Path("data/results/robustness_analysis.json")

    raw_results = _load_json(raw_path) or _load_json(out_path) or []
    if not isinstance(raw_results, list):
        logging.error("Robustness results are not in the expected list format.")
        raw_results = []

    # Extract the original p‑values.
    original_p = [entry.get("p_value", 0.0) for entry in raw_results]

    # Apply the chosen correction.
    if correction.lower() == "bh":
        corrected_p = _apply_bh(original_p)
    else:
        corrected_p = _apply_bonferroni(original_p)

    # Attach corrected p‑values to each entry.
    for entry, p_corr in zip(raw_results, corrected_p):
        entry["p_value_corrected"] = p_corr

    # Write the corrected results.
    _write_json(raw_results, out_path)

# -------------------------------------------------------------------------
# Main entry‑point
# -------------------------------------------------------------------------
def main():
    """
    Execute both report generators.  This function is called by the
    project's quick‑start script (``python -m src.report.generate``) and
    ensures that the two required JSON artefacts are present after a full
    pipeline run.
    """
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(message)s")
    generate_primary_report()
    # The robustness analysis has already been executed earlier in the
    # pipeline (see ``src.analysis.robustness``).  Here we only apply the
    # correction and write the final JSON file.
    generate_robustness_report(correction="bonferroni")

if __name__ == "__main__":
    main()