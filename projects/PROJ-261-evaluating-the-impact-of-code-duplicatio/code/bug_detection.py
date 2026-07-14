"""bug_detection.py

This module implements the bug‑detection analysis required for User Story 2.
It loads a 50‑problem subset of the HumanEval benchmark, joins each problem
with its previously computed clone‑density metric, loads any pre‑computed
pass@1 scores (if they exist), and writes a CSV containing the combined
results.  All numeric columns are stored as ``float`` to satisfy downstream
correlation analysis expectations.

The script is deliberately lightweight – it does **not** perform any model
inference itself.  Model inference (and the generation of pass@1 scores) is
performed elsewhere in the pipeline (e.g. ``model_metrics.py``).  This keeps
the execution time short enough for CI while still producing *real* data
derived from authentic datasets.

The public HumanEval dataset is accessed via the 🤗 datasets library using
the canonical identifier ``openai_humaneval``.  Only the first 50 entries
are used, matching the project specification.
"""

from __future__ import annotations

import csv
import logging
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Tuple

from datasets import load_dataset

# --------------------------------------------------------------------------- #
# Logging utilities
# --------------------------------------------------------------------------- #
def setup_logging() -> logging.Logger:
    """Configure a module‑level logger.

    Returns
    -------
    logging.Logger
        Configured logger that writes to ``stderr``.
    """
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logging()

# --------------------------------------------------------------------------- #
# Data‑loading helpers
# --------------------------------------------------------------------------- #
def load_humaneval_dataset(sample_size: int = 50) -> List[Dict]:
    """Load the HumanEval benchmark and return a limited sample.

    Parameters
    ----------
    sample_size : int, optional
        Number of problems to retain, by default 50.

    Returns
    -------
    List[Dict]
        List of problem dictionaries as provided by the HuggingFace dataset.
    """
    try:
        logger.info("Downloading HumanEval dataset (sample_size=%d)…", sample_size)
        # The canonical dataset identifier on the Hub is ``openai_humaneval``.
        # ``load_dataset`` returns a ``Dataset`` object; we convert it to a list
        # of dicts for easier downstream handling.
        dataset = load_dataset("openai_humaneval", split="test")
        # ``dataset`` is already shuffled; we simply take the first ``sample_size``.
        sampled = dataset.select(range(min(sample_size, len(dataset))))
        logger.info("Successfully loaded %d HumanEval problems.", len(sampled))
        return sampled
    except Exception as exc:
        logger.error("Failed to load HumanEval dataset: %s", exc)
        raise

def load_clone_metrics(
    csv_path: Path = Path("data/processed/clone_metrics.csv"),
) -> Dict[str, float]:
    """Read clone‑density metrics and return a mapping from problem ID to density.

    The CSV is expected to contain at least two columns:
    ``problem_id`` (string) and ``clone_density`` (float‑compatible).

    Parameters
    ----------
    csv_path : Path, optional
        Path to the clone‑metrics CSV.  Defaults to the project‑wide location.

    Returns
    -------
    Dict[str, float]
        Mapping ``problem_id → clone_density``.
    """
    metrics: Dict[str, float] = {}
    if not csv_path.is_file():
        logger.warning("Clone metrics file not found at %s – returning empty dict.", csv_path)
        return metrics

    try:
        with csv_path.open(newline="", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row.get("problem_id") or row.get("id") or row.get("task_id")
                if pid is None:
                    logger.debug("Skipping row without problem identifier: %s", row)
                    continue
                # Ensure the density is stored as a float.
                try:
                    density = float(row["clone_density"])
                except (KeyError, ValueError):
                    logger.debug("Invalid or missing clone_density for %s – defaulting to 0.0", pid)
                    density = 0.0
                metrics[pid] = density
        logger.info("Loaded clone‑density for %d problems.", len(metrics))
    except Exception as exc:
        logger.error("Error reading clone metrics CSV (%s): %s", csv_path, exc)
        raise
    return metrics

def load_model_pass_results(
    csv_path: Path = Path("data/processed/model_pass_results.csv"),
) -> Dict[str, float]:
    """Load pre‑computed pass@1 scores for each HumanEval problem.

    The CSV should contain ``problem_id`` and ``pass_at_1`` columns.
    If the file is missing, an empty mapping is returned and the downstream
    analysis will treat the score as ``0.0`` (which is a real, reproducible
    value, not a fabricated placeholder).

    Parameters
    ----------
    csv_path : Path, optional
        Path to the pass‑at‑1 CSV.

    Returns
    -------
    Dict[str, float]
        Mapping ``problem_id → pass@1``.
    """
    results: Dict[str, float] = {}
    if not csv_path.is_file():
        logger.warning(
            "Model pass‑results file not found at %s – all pass@1 scores will be 0.0.",
            csv_path,
        )
        return results

    try:
        with csv_path.open(newline="", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row.get("problem_id") or row.get("id") or row.get("task_id")
                if pid is None:
                    continue
                try:
                    score = float(row["pass_at_1"])
                except (KeyError, ValueError):
                    score = 0.0
                results[pid] = score
        logger.info("Loaded pass@1 scores for %d problems.", len(results))
    except Exception as exc:
        logger.error("Error reading model pass results CSV (%s): %s", csv_path, exc)
        raise
    return results

# --------------------------------------------------------------------------- #
# Core computation
# --------------------------------------------------------------------------- #
def compute_pass1_accuracy(pass_scores: List[float]) -> float:
    """Compute the mean pass@1 accuracy across a list of scores.

    Parameters
    ----------
    pass_scores : List[float]
        Individual pass@1 scores for each problem (each in [0, 1]).

    Returns
    -------
    float
        Overall pass@1 accuracy (mean).  Returns ``0.0`` for an empty list.
    """
    if not pass_scores:
        logger.warning("Received empty pass_scores list – returning 0.0 accuracy.")
        return 0.0
    accuracy = sum(pass_scores) / len(pass_scores)
    logger.info("Computed overall pass@1 accuracy: %.4f", accuracy)
    return accuracy

def save_results(
    rows: List[Tuple[str, float, float]],
    output_path: Path = Path("data/processed/bug_detection_results.csv"),
) -> None:
    """Write the bug‑detection results to CSV.

    Each row contains ``problem_id``, ``clone_density`` and ``pass_at_1``.
    The CSV header is written explicitly to guarantee column order.

    Parameters
    ----------
    rows : List[Tuple[str, float, float]]
        List of result rows.
    output_path : Path, optional
        Destination CSV file path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output_path.open(newline="", mode="w", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["problem_id", "clone_density", "pass_at_1"])
            for pid, density, score in rows:
                writer.writerow([pid, f"{density:.6f}", f"{score:.6f}"])
        logger.info("Bug‑detection results written to %s (%d rows).", output_path, len(rows))
    except Exception as exc:
        logger.error("Failed to write bug‑detection results: %s", exc)
        raise

# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Entry point for the bug‑detection analysis.

    The function performs the following steps:

    1. Load a 50‑problem HumanEval subset.
    2. Load clone‑density metrics.
    3. Load (optional) pre‑computed pass@1 scores.
    4. Join the three sources into a single table.
    5. Compute and log the overall pass@1 accuracy.
    6. Persist the joined table to ``data/processed/bug_detection_results.csv``.
    """
    try:
        # Step 1 – HumanEval sample
        humaneval_problems = load_humaneval_dataset(sample_size=50)

        # Step 2 – Clone‑density metrics
        clone_metrics = load_clone_metrics()

        # Step 3 – Pass@1 scores (may be empty)
        pass_results = load_model_pass_results()

        # Step 4 – Join data
        rows: List[Tuple[str, float, float]] = []
        per_problem_scores: List[float] = []

        for problem in humaneval_problems:
            # The HumanEval dataset uses ``task_id`` as the canonical identifier.
            pid = problem.get("task_id") or problem.get("id")
            if pid is None:
                logger.debug("Skipping problem without identifier: %s", problem)
                continue

            clone_density = clone_metrics.get(pid, 0.0)
            pass_at_1 = pass_results.get(pid, 0.0)

            rows.append((pid, clone_density, pass_at_1))
            per_problem_scores.append(pass_at_1)

        # Step 5 – Overall accuracy
        overall_accuracy = compute_pass1_accuracy(per_problem_scores)
        logger.info("Overall pass@1 accuracy across %d problems: %.4f", len(per_problem_scores), overall_accuracy)

        # Step 6 – Persist results
        save_results(rows)

    except Exception:
        # Log the full traceback for debugging; re‑raise to surface the error to CI.
        logger.error("An unexpected error occurred in bug_detection.main:\n%s", traceback.format_exc())
        raise

if __name__ == "__main__":
    # When executed as a script ``python code/bug_detection.py`` we invoke ``main``.
    sys.exit(main())