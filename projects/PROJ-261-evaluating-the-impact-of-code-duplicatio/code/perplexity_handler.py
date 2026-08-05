from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def _simple_perplexity_estimate(code: str) -> float:
    """
    Very cheap proxy for perplexity: inverse of average token length.
    This is **not** a true language‑model perplexity but provides a
    reproducible, data‑driven numeric value without requiring a GPU.
    """
    tokens = code.split()
    if not tokens:
        return 0.0
    avg_len = sum(len(tok) for tok in tokens) / len(tokens)
    # Larger average token length -> lower (better) perplexity proxy
    return 1.0 / avg_len

def compute_perplexity_batch(
    *,
    raw_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Compute a proxy perplexity for each file in the raw CSV.

    Parameters
    ----------
    raw_path: Optional[Path]
        Path to the raw CSV. If ``None`` the default path from
        ``config.get_raw_dir`` is used.

    Returns
    -------
    List[Dict[str, Any]]
        Each dict contains ``file_id`` and ``perplexity``.
    """
    from config import get_raw_dir

    if raw_path is None:
        raw_path = get_raw_dir() / "github-code-sample.csv"

    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_path}")

    results: List[Dict[str, Any]] = []
    with raw_path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            file_id = row["file_id"]
            code = row.get("code", "")
            ppl = _simple_perplexity_estimate(code)
            results.append(
                {"file_id": file_id, "perplexity": f"{ppl:.6f}"}
            )
    logger.info("Computed proxy perplexity for %d files", len(results))
    return results

def save_perplexity_scores(perplexity_scores: List[Dict[str, Any]]) -> None:
    """
    Write perplexity scores to ``data/processed/perplexity_scores.csv``.
    The CSV will have the columns ``file_id`` and ``perplexity``.
    """
    from config import get_processed_dir

    out_path = get_processed_dir() / "perplexity_scores.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["file_id", "perplexity"]
    with out_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in perplexity_scores:
            writer.writerow(row)
    logger.info("Perplexity scores saved to %s", out_path)

def main() -> None:
    """
    Convenience entry‑point for debugging.
    """
    scores = compute_perplexity_batch()
    save_perplexity_scores(scores)