#!/usr/bin/env python
"""
Defects4J fetcher and stratified sampler (FR‑001)

This script streams a public Defects4J‑related dataset from HuggingFace,
extracts a stratified sample of buggy methods across the three projects
Chart, Time, and Math (20 methods per project, 60 total), and writes the
result to ``data/raw/defects4j/ground_truth.csv``.
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
def _stream_defects4j(dataset_name: str):
    """
    Load the Defects4J‑related dataset in streaming mode.
    """
    # streaming=True ensures we never load the whole dataset into RAM.
    return load_dataset(dataset_name, split="train", streaming=True)

def _collect_methods(
    ds,
    target_projects=("Chart", "Time", "Math"),
) -> tuple[dict[str, list[dict]], list[dict]]:
    """
    Iterate over the streamed dataset, bucket methods by project and
    record any entries missing a ground‑truth line.
    """
    project_buckets: dict[str, list[dict]] = {p: [] for p in target_projects}
    missing: list[dict] = []

    for record in ds:
        project = record.get("project_name")
        if project not in target_projects:
            continue

        method_id = record.get("method_id")
        ground_truth_line = record.get("ground_truth_line")

        # Record missing or invalid ground‑truth information
        try:
            if ground_truth_line is None:
                raise ValueError("Missing ground_truth_line")
            gt_val = int(ground_truth_line)
        except (ValueError, TypeError):
            missing.append(
                {
                    "method_id": method_id,
                    "project_name": project,
                    "bug_id": record.get("bug_id"),
                    "error": "Missing or non-integer ground_truth_line"
                }
            )
            continue

        # Preserve required fields for the CSV output
        project_buckets[project].append(
            {
                "method_id": method_id,
                "project_name": project,
                "bug_id": record.get("bug_id"),
                "source_code": record.get("source_code"),
                "ground_truth_line": gt_val,
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
        description=(
            "Download a Defects4J‑related dataset from HuggingFace, "
            "extract a stratified sample, and write CSV/JSON outputs."
        )
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used for stratified sampling (default: 42).",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="chathuranga-jayanath/defects4j-context-5-len-10000-prompt-3",
        help=(
            "HuggingFace dataset identifier."
        ),
    )
    args = parser.parse_args()

    log.info("Streaming Defects4J dataset '%s'...", args.dataset)
    try:
        dataset = _stream_defects4j(args.dataset)
    except Exception as e:
        log.error("Failed to fetch dataset from HuggingFace: %s", e)
        raise

    log.info("Collecting methods and tracking missing ground‑truth entries...")
    project_buckets, missing = _collect_methods(dataset)

    log.info("Performing stratified sampling (20 methods per project)...")
    sampled_methods = _sample_stratified(project_buckets, per_project=20, seed=args.seed)

    # ------------------------------------------------------------------
    # Write outputs
    # ------------------------------------------------------------------
    csv_path = paths.data("raw", "defects4j", "ground_truth.csv")
    json_path = paths.data("interaction_logs", "missing_ground_truth.json")

    # Write CSV
    df = pd.DataFrame(sampled_methods)
    df.to_csv(csv_path, index=False)
    log.info(f"Wrote ground‑truth CSV with {len(df)} rows to {csv_path}")

    # Write JSON
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(missing, f, indent=2, ensure_ascii=False)
    log.info(f"Wrote missing‑ground‑truth log with {len(missing)} entries to {json_path}")

if __name__ == "__main__":
    main()