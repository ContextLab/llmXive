from __future__ import annotations
import json
from pathlib import Path

import pandas as pd
from scipy.stats import pearsonr, spearmanr

from reproducibility.logs import get_logger, log_operation

@log_operation
def compute_correlations(df: pd.DataFrame) -> dict:
    """Compute Pearson and Spearman correlations between selected invariants."""
    # Ensure numeric conversion
    numeric_cols = ["crossing_number", "braid_index", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    results = {}
    # Pairwise correlations
    pairs = [("crossing_number", "volume"), ("braid_index", "volume")]
    for x, y in pairs:
        clean = df[[x, y]].dropna()
        if clean.empty:
            results[f"{x}_vs_{y}"] = {"pearson": None, "spearman": None}
            continue
        pearson, _ = pearsonr(clean[x], clean[y])
        spearman, _ = spearmanr(clean[x], clean[y])
        results[f"{x}_vs_{y}"] = {"pearson": pearson, "spearman": spearman}
    return results

@log_operation
def generate_report(correlations: dict, output_path: Path) -> None:
    """Write a JSON report of correlation results."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(correlations, f, indent=2)

def main() -> None:
    logger = get_logger()
    logger.info("Computing correlation metrics")
    from analysis._utils import load_cleaned_knots

    df = load_cleaned_knots()
    corr = compute_correlations(df)
    out_path = Path("data/processed/correlation_report.json")
    generate_report(corr, out_path)
    logger.info(f"Correlation report written to {out_path}")

if __name__ == "__main__":
    main()
