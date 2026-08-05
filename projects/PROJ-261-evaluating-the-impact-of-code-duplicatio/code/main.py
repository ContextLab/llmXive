from __future__ import annotations

import logging
from pathlib import Path

from config import (
    get_processed_dir,
    get_raw_dir,
    get_clone_thresholds,
    get_memory_limit_mb,
)
from data_loader import download_and_save_sample
from ast_cloner import compute_clone_density_batch, save_clone_metrics
from model_metrics import compute_perplexity_batch

logger = logging.getLogger(__name__)

def _ensure_clone_metrics() -> Path:
    """
    Compute clone‑density metrics and persist them.
    Returns the path to the created CSV.
    """
    raw_path = get_raw_dir() / "github-code-sample.csv"
    metrics = compute_clone_density_batch(raw_path=raw_path)
    output_path = get_processed_dir() / "clone_metrics.csv"
    save_clone_metrics(metrics, output_path=output_path)
    return output_path

def _ensure_perplexity_scores() -> Path:
    """
    Compute token‑level perplexity scores and persist them.
    Returns the path to the created CSV.
    """
    raw_path = get_raw_dir() / "github-code-sample.csv"
    scores = compute_perplexity_batch(raw_path=raw_path)
    output_path = get_processed_dir() / "perplexity_scores.csv"
    # The ``compute_perplexity_batch`` function returns a list of dicts with
    # ``file_id`` and ``perplexity`` keys.
    logger.info("Saving perplexity scores to %s", output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        import csv

        writer = csv.DictWriter(f, fieldnames=["file_id", "perplexity"])
        writer.writeheader()
        for row in scores:
            writer.writerow(row)
    return output_path

def _join_and_validate(clone_path: Path, perplexity_path: Path) -> None:
    """
    Join the two metric CSVs on ``file_id`` and log any mismatches.
    The joined result is *not* written to disk because downstream tasks
    (e.g., correlation analysis) read the individual files directly.
    """
    import csv

    logger.info("Joining %s and %s", clone_path, perplexity_path)

    # Load clone metrics.
    clone_map: dict[str, dict] = {}
    with clone_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            clone_map[row["file_id"]] = row

    # Validate each perplexity entry.
    mismatches: List[str] = []
    with perplexity_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fid = row["file_id"]
            if fid not in clone_map:
                mismatches.append(fid)

    if mismatches:
        logger.warning(
            "Found %d ID mismatches between clone metrics and perplexity scores.",
            len(mismatches),
        )
    else:
        logger.info("No ID mismatches detected.")

def run_pipeline() -> None:
    """
    Orchestrate the full US‑1 pipeline, guaranteeing that both required CSV
    artifacts are produced and that any ID mismatches are logged.

    The steps are:

    1. Ensure the raw sample exists (download if necessary).
    2. Compute and persist clone‑density metrics.
    3. Compute and persist perplexity scores.
    4. Join the two tables and emit a warning if IDs diverge.
    """
    logging.basicConfig(level=logging.INFO)

    # 1️⃣  Ensure raw data.
    raw_path = get_raw_dir() / "github-code-sample.csv"
    if not raw_path.is_file():
        logger.info("Raw sample missing – invoking downloader.")
        download_and_save_sample(path=raw_path, sample_size=100)

    # 2️⃣  Clone density.
    clone_csv = _ensure_clone_metrics()

    # 3️⃣  Perplexity.
    perplexity_csv = _ensure_perplexity_scores()

    # 4️⃣  Validation / join.
    _join_and_validate(clone_csv, perplexity_csv)

    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    run_pipeline()
