"""
Sensitivity analysis for significance thresholds with Benjamini‑Hochberg correction.
"""
import json
from pathlib import Path
from typing import List, Dict, Any

# Updated import path
from code.utils.logging import get_logger, log_duration

logger = get_logger(__name__)


def apply_benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Apply the Benjamini‑Hochberg procedure.
    Returns a list of booleans indicating which hypotheses are significant.
    """
    m = len(p_values)
    sorted_idx = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_idx]
    thresholds = (np.arange(1, m + 1) / m) * alpha
    significant = sorted_p <= thresholds
    # Find the largest i where condition holds
    if not significant.any():
        return [False] * m
    max_i = np.where(significant)[0].max()
    sig_mask = np.arange(m) <= max_i
    # Re‑order to original order
    unsorted = np.empty(m, dtype=bool)
    unsorted[sorted_idx] = sig_mask
    return unsorted.tolist()


@log_duration
def run_sensitivity_analysis(
    results: Dict[str, Any],
    thresholds: List[float] = [0.01, 0.05, 0.10],
) -> Dict[float, int]:
    """
    Sweep significance thresholds and count number of significant predictors.
    Returns a mapping from threshold to count of significant predictors.
    """
    p_vals = [res["p_value"] for res in results.values()]
    summary = {}
    for thr in thresholds:
        sig_flags = apply_benjamini_hochberg(p_vals, alpha=thr)
        summary[thr] = int(sum(sig_flags))
    return summary


def save_sensitivity_results(
    summary: Dict[float, int],
    output_path: Path,
) -> None:
    """
    Write the sensitivity summary to CSV.
    """
    rows = [{"threshold": thr, "num_significant_predictors": cnt} for thr, cnt in summary.items()]
    df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


def main() -> None:
    logger.info("Sensitivity module executed as script – no action defined.")


if __name__ == "__main__":
    main()
