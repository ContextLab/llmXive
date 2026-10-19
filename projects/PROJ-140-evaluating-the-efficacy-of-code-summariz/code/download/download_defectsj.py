#!/usr/bin/env python
"""
Defects4J fetcher and stratified sampler (FR‑001)

This script streams the real Defects4J dataset from HuggingFace,
extracts a stratified sample of buggy methods across the three projects
Chart, Time, and Math (20 methods per project, 60 total), and writes the
resulting ground‑truth CSV to ``data/raw/defects4j/ground_truth.csv``.
Methods that lack a ``ground_truth_line`` are recorded in
``data/interaction_logs/missing_ground_truth.json``.
The script fails loudly on any fetch or processing error – no synthetic
fallback is provided.
"""

import argparse
import json
import random
from pathlib import Path

import pandas as pd
from datasets import load_dataset

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _stream_defects4j() -> "datasets.arrow_dataset.Dataset":
    """
    Load the Defects4J dataset in streaming mode.

    Returns
    -------
    Dataset
        An iterable HuggingFace ``datasets`` object.
    """
    # The canonical HuggingFace identifier for the Defects4J dataset.
    # If the identifier changes, this line should be updated accordingly.
    return load_dataset("defects4j", split="train", streaming=True)

def _collect_methods(
    ds,
    target_projects=("Chart", "Time", "Math"),
) -> tuple[dict[str, list[dict]], list[dict]]:
    """
    Iterate over the streamed dataset, bucket methods by project and
    record any entries missing a ground‑truth line.

    Parameters
    ----------
    ds : Dataset
        The streamed Defects4J dataset.
    target_projects : tuple[str, ...]
        Projects for which we want to sample methods.

    Returns
    -------
    tuple
        - ``project_buckets``: dict mapping project name → list of method dicts
          (only those with a non‑null ``ground_truth_line``).
        - ``missing``: list of dicts for methods where ``ground_truth_line`` is
          missing or null.
    """
    project_buckets: dict[str, list[dict]] = {p: [] for p in target_projects}
    missing: list[dict] = []

    for record in ds:
        project = record.get("project_name")
        if project not in target_projects:
            continue

        method_id = record.get("method_id")
        ground_truth_line = record.get("ground_truth_line")

        # Record missing ground‑truth information
        if ground_truth_line is None:
            missing.append(
                {
                    "method_id": method_id,
                    "project_name": project,
                    "bug_id": record.get("bug_id"),
                }
            )
            continue

        # Preserve all required fields for the CSV output
        project_buckets[project].append(
            {
                "method_id": method_id,
                "project_name": project,
                "bug_id": record.get("bug_id"),
                "source_code": record.get("source_code"),
                "ground_truth_line": int(ground_truth_line),
                "context_code": record.get("context_code"),
            }
        )

    return project_buckets, missing

def _sample_stratified(
    project_buckets: dict[str, list[dict]],
    per_project: int = 20,
    seed: int = 42,
) -> list[dict]:
    """
    Perform a stratified random sample (fixed seed) of ``per_project`` methods
    from each project bucket.

    Parameters
    ----------
    project_buckets : dict
        Mapping from project name to list of method dicts.
    per_project : int
        Number of methods to sample from each project.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    list[dict]
        Sampled method records (total ``per_project * len(project_buckets)``).
    """
    random.seed(seed)
    sampled: list[dict] = []

    for project, methods in project_buckets.items():
        if len(methods) < per_project:
            raise ValueError(
                f"Not enough methods in project '{project}' for sampling: "
                f"required {per_project}, found {len(methods)}."
            )
        sampled.extend(random.sample(methods, per_project))

    return sampled

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download Defects4J, extract a stratified sample, and write CSV/JSON outputs."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used for stratified sampling (default: 42).",
    )
    args = parser.parse_args()

    log.info("Streaming Defects4J dataset...")
    dataset = _stream_defects4j()

    log.info("Collecting methods and tracking missing ground‑truth entries...")
    project_buckets, missing = _collect_methods(dataset)

    log.info("Performing stratified sampling (20 methods per project)...")
    sampled_methods = _sample_stratified(project_buckets, per_project=20, seed=args.seed)

    # ------------------------------------------------------------------
    # Write outputs
    # ------------------------------------------------------------------
    csv_path: Path = paths.data("raw", "defects4j", "ground_truth.csv")
    json_path: Path = paths.data("interaction_logs", "missing_ground_truth.json")

    # ``paths.data`` creates the parent directory if it does not exist.
    df = pd.DataFrame(sampled_methods)
    df.to_csv(csv_path, index=False)
    log.info(f"Wrote ground‑truth CSV with {len(df)} rows to {csv_path}")

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(missing, f, indent=2, ensure_ascii=False)
    log.info(f"Wrote missing‑ground‑truth log with {len(missing)} entries to {json_path}")

if __name__ == "__main__":
    main()
