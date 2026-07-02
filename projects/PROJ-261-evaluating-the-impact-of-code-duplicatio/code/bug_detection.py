"""bug_detection.py
Implements the bug detection evaluation for the HumanEval subset.
Loads the 50‑problem HumanEval dataset, merges with clone density metrics,
runs the reference solution against the provided tests to compute pass@1
accuracy, and writes the results to ``data/processed/bug_detection_results.csv``.
All metrics are real measurements – no synthetic fall‑backs are used.
"""

from __future__ import annotations

import csv
import logging
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from datasets import load_dataset

# Local imports
from code.checksum_manifest import record_artifact_checksums


LOGGER_NAME = "bug_detection"


def setup_logging() -> None:
    """Configure a module‑level logger."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)


def load_humaneval_dataset(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Load the official HumanEval dataset (via 🤗 Datasets) and return the first
    ``limit`` entries as a list of dictionaries.

    Each entry contains at least the following keys used downstream:
    - ``task_id``: unique identifier (e.g. ``HumanEval/0``)
    - ``prompt``: the problem description (unused here)
    - ``canonical_solution``: reference solution code
    - ``test``: a string containing one or more ``def test_…`` functions.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.info(f"Loading HumanEval dataset (first {limit} problems)…")
    # The dataset is called ``openai_humaneval`` on the Hub.
    dataset = load_dataset("openai_humaneval", split="train")
    # Take a deterministic slice
    subset = dataset.select(range(limit))
    logger.info(f"Loaded {len(subset)} HumanEval problems.")
    return [entry for entry in subset]


def load_clone_metrics() -> pd.DataFrame:
    """
    Load the clone‑density metrics produced by ``code/ast_cloner.py``.
    The CSV is expected to contain at least the columns:
    - ``problem_id`` (matching HumanEval ``task_id``)
    - ``clone_density`` (float)
    """
    logger = logging.getLogger(LOGGER_NAME)
    path = Path("data/processed/clone_metrics.csv")
    if not path.is_file():
        logger.warning(f"Clone metrics file not found at {path}. Continuing with NaNs.")
        return pd.DataFrame(columns=["problem_id", "clone_density"])
    df = pd.read_csv(path)
    # Normalise column names
    if "problem_id" not in df.columns:
        # Fallback to a generic identifier column if the original name differs
        possible_id_cols = [c for c in df.columns if "id" in c.lower()]
        if possible_id_cols:
            df = df.rename(columns={possible_id_cols[0]: "problem_id"})
    if "clone_density" not in df.columns:
        raise ValueError("clone_density column missing from clone metrics CSV.")
    # Ensure the density is stored as a float
    df["clone_density"] = pd.to_numeric(df["clone_density"], errors="coerce")
    return df[["problem_id", "clone_density"]]


def run_tests(solution_code: str, test_code: str) -> bool:
    """
    Execute ``solution_code`` and ``test_code`` in an isolated namespace.
    All functions whose name starts with ``test_`` are invoked.  If any
    raises an exception (typically ``AssertionError``) the problem is
    considered a failure; otherwise it passes.
    """
    logger = logging.getLogger(LOGGER_NAME)
    namespace: Dict[str, Any] = {}
    try:
        exec(solution_code, namespace)
        exec(test_code, namespace)
        test_funcs = [
            obj
            for name, obj in namespace.items()
            if callable(obj) and name.startswith("test_")
        ]
        for func in test_funcs:
            func()
        return True
    except Exception as exc:  # pragma: no cover – exercised via tests
        logger.debug(f"Test execution failed: {exc}")
        logger.debug(traceback.format_exc())
        return False


def compute_pass1_accuracy(passed_flags: List[bool]) -> float:
    """
    Compute the pass@1 accuracy as the proportion of problems for which the
    generated (here, reference) solution passed all tests.
    """
    if not passed_flags:
        return 0.0
    return sum(passed_flags) / len(passed_flags)


def save_results(
    rows: List[Dict[str, Any]],
    output_path: Path = Path("data/processed/bug_detection_results.csv"),
) -> None:
    """
    Persist the per‑problem bug‑detection evaluation to CSV.
    The CSV contains three columns:
    - ``problem_id`` (string)
    - ``clone_density`` (float, may be NaN)
    - ``pass_at_1`` (float, 0.0 or 1.0)
    """
    logger = logging.getLogger(LOGGER_NAME)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["problem_id", "clone_density", "pass_at_1"]
        )
        writer.writeheader()
        for row in rows:
            # Ensure clone_density is a float (or NaN) before writing
            row_to_write = {
                "problem_id": row["problem_id"],
                "clone_density": (
                    "" if pd.isna(row["clone_density"]) else f"{row['clone_density']:.6f}"
                ),
                "pass_at_1": f"{row['pass_at_1']:.6f}",
            }
            writer.writerow(row_to_write)
    logger.info(f"Wrote bug‑detection results to {output_path}")


def main() -> None:
    """Orchestrate the whole bug‑detection evaluation pipeline."""
    setup_logging()
    logger = logging.getLogger(LOGGER_NAME)

    # 1. Load data
    try:
        human_eval = load_humaneval_dataset(limit=50)
    except Exception as exc:  # pragma: no cover
        logger.error(f"Failed to load HumanEval dataset: {exc}")
        sys.exit(1)

    clone_df = load_clone_metrics()

    # 2. Evaluate each problem
    results: List[Dict[str, Any]] = []
    passed_flags: List[bool] = []

    for entry in human_eval:
        problem_id: str = entry["task_id"]
        solution_code: str = entry["canonical_solution"]
        test_code: str = entry["test"]

        passed = run_tests(solution_code, test_code)
        passed_flags.append(passed)

        # Retrieve clone density (may be missing)
        match = clone_df[clone_df["problem_id"] == problem_id]
        if not match.empty:
            density = float(match["clone_density"].iloc[0])
        else:
            density = float("nan")

        results.append(
            {
                "problem_id": problem_id,
                "clone_density": density,
                "pass_at_1": 1.0 if passed else 0.0,
            }
        )

    # 3. Persist per‑problem results
    output_csv = Path("data/processed/bug_detection_results.csv")
    save_results(results, output_csv)

    # 4. Compute and log overall pass@1 accuracy
    overall_accuracy = compute_pass1_accuracy(passed_flags)
    logger.info(f"Overall pass@1 accuracy on {len(human_eval)} problems: {overall_accuracy:.4f}")

    # 5. Record checksum for reproducibility
    try:
        record_artifact_checksums(str(output_csv))
        logger.info("Recorded checksum for bug‑detection results.")
    except Exception as exc:  # pragma: no cover
        logger.warning(f"Checksum recording failed: {exc}")


if __name__ == "__main__":
    main()
