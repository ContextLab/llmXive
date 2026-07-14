"""
Re‑run statistical analyses (t‑tests & linear regressions) on each cleaned
dataset variant and persist the aggregated results to
``data/processed/cleaned_metrics.json``.

The script is deliberately lightweight – it discovers cleaned CSV files in
the processed data directory (those whose filename contains ``cleaned``),
invokes :func:`run_baseline_analysis` on each, and writes a single JSON
artifact that downstream reporting scripts consume.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

from utils import setup_logging, pin_random_seed
from analysis import run_baseline_analysis

logger = setup_logging(log_level="INFO")


def _discover_cleaned_files(processed_dir: Path) -> Dict[str, Path]:
    """
    Return a mapping from a short identifier to the Path of each cleaned CSV
    file found under *processed_dir*. A cleaned file is recognised by the
    substring ``cleaned`` in its filename.
    """
    cleaned = {}
    for p in processed_dir.glob("*cleaned*.csv"):
        cleaned[p.stem] = p
    return cleaned


def main() -> None:
    """
    Entry‑point used by the quick‑start run‑book.

    Steps:
    1. Ensure reproducibility.
    2. Locate cleaned dataset files.
    3. Analyse each cleaned variant via ``run_baseline_analysis``.
    4. Persist the combined metrics to ``data/processed/cleaned_metrics.json``.
    """
    pin_random_seed(42)

    processed_dir = Path("data/processed")
    if not processed_dir.is_dir():
        logger.error("Processed data directory %s does not exist.", processed_dir)
        return

    cleaned_files = _discover_cleaned_files(processed_dir)
    if not cleaned_files:
        logger.warning("No cleaned CSV files found in %s. Nothing to analyse.", processed_dir)
        return

    all_metrics: Dict[str, Any] = {}
    for name, csv_path in cleaned_files.items():
        try:
            logger.info("Analyzing cleaned dataset: %s", csv_path.name)
            # Load the CSV into a DataFrame and let run_baseline_analysis handle it.
            # We use the in‑memory variant of the API.
            import pandas as pd

            df = pd.read_csv(csv_path)
            metrics = run_baseline_analysis(dataframe=df)
            # ``run_baseline_analysis`` returns a dict with a single key
            # ``in_memory``; we unwrap it for clarity.
            all_metrics[name] = metrics.get("in_memory", {})
        except Exception as exc:
            logger.error("Failed to analyse %s: %s", csv_path, exc)

    # Write the aggregated results
    output_path = processed_dir / "cleaned_metrics.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2)
    logger.info("Cleaned metrics written to %s", output_path)


if __name__ == "__main__":
    main()
