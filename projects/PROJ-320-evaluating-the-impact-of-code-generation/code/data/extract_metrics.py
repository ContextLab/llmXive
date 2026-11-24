"""
T009 Implementation: Extract review metrics, temporal covariates, and defect density.

This script:
  * Loads the labeled PR dataset (expected to be the output of the classification
    step, e.g. ``prs_labeled_complex.csv``) which already contains columns such
    as ``pr_id``, ``source_type``, ``confidence_score`` etc.
  * Loads the raw GitHub PR JSON payloads from ``data/raw/*.jsonl``.
  * For each PR calculates:
      - ``comment_count``      : sum of ``comments`` and ``review_comments``.
      - ``time_to_merge_minutes`` : difference between ``merged_at`` and
        ``created_at`` in minutes (rows with no ``merged_at`` are omitted from
        the final CSV and logged).
      - ``review_cycles``      : ``max(1, comment_count // 2)``.
      - ``hour_of_day``        : hour (0‑23) extracted from ``created_at``.
      - ``day_of_week``        : weekday (0=Monday … 6=Sunday) from ``created_at``.
      - ``defect_count``       : ``1`` if the PR has a label named ``bug`` (case‑insensitive)
        **or** its body contains a pattern like ``fixes #123`` (case‑insensitive),
        otherwise ``0``.
      - ``defect_density``     : ``defect_count / loc`` (``loc`` comes from the
        complexity step). If ``loc`` is ``0`` the density is set to ``0.0``.
  * Writes the enriched dataset to ``data/processed/prs_metrics.csv``.
    The output conforms to the original ``pr_schema`` plus the additional
    ``defect_density`` column.

The CLI matches the Quickstart guide:
    python code/data/extract_metrics.py --input <labeled_csv> --output <metrics_csv>
"""
import argparse
import csv
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

# Project‑root import helpers
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging import setup_logging, get_logger
from utils.config import get_path

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def parse_timestamp(ts: str) -> Optional[datetime]:
    """Parse ISO‑8601 timestamps returned by the GitHub API."""
    if not ts:
        return None
    # GitHub timestamps are usually ``YYYY‑MM‑DDTHH:MM:SSZ`` or with
    # fractional seconds.
    for fmt in (
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    return None

def load_raw_prs(raw_dir: Path) -> Dict[int, Dict]:
    """
    Load all ``*.jsonl`` files from ``raw_dir`` into a dictionary keyed by PR id.
    """
    raw_prs: Dict[int, Dict] = {}
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory does not exist: {raw_dir}")

    for jsonl_file in raw_dir.glob("*_prs.jsonl"):
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                pr = json.loads(line)
                pr_id = pr.get("id") or pr.get("number")
                if pr_id is None:
                    continue
                raw_prs[int(pr_id)] = pr
    return raw_prs

def compute_comment_count(pr: Dict) -> int:
    """Sum of top‑level ``comments`` and ``review_comments`` fields."""
    return int(pr.get("comments", 0)) + int(pr.get("review_comments", 0))

def compute_time_to_merge_minutes(pr: Dict) -> Optional[float]:
    """Return minutes between creation and merge; ``None`` if not merged."""
    created = parse_timestamp(pr.get("created_at", ""))
    merged = parse_timestamp(pr.get("merged_at", ""))
    if created and merged and merged > created:
        delta = merged - created
        return delta.total_seconds() / 60.0
    return None

def compute_review_cycles(comment_count: int) -> int:
    """Derived as ``max(1, comment_count // 2)``."""
    return max(1, comment_count // 2)

def compute_temporal_features(pr: Dict) -> (int, int):
    """Return (hour_of_day, day_of_week) extracted from ``created_at``."""
    created = parse_timestamp(pr.get("created_at", ""))
    if not created:
        # Use sentinel values that will be easy to spot in downstream analysis
        return -1, -1
    return created.hour, created.weekday()

BUG_LABEL_RE = re.compile(r"\bbug\b", re.IGNORECASE)
FIXES_PATTERN_RE = re.compile(r"fixes\s+#\d+", re.IGNORECASE)

def compute_defect_count(pr: Dict) -> int:
    """
    Return ``1`` if the PR is associated with a bug fix, otherwise ``0``.
    Detection rules:
      * Any label whose name matches ``bug`` (case‑insensitive).
      * Body text containing ``fixes #<num>`` (case‑insensitive).
    """
    # Check labels
    labels = pr.get("labels", [])
    for label in labels:
        name = label.get("name", "")
        if BUG_LABEL_RE.search(name):
            return 1

    # Check body for explicit "fixes #123"
    body = pr.get("body", "")
    if FIXES_PATTERN_RE.search(body):
        return 1

    return 0

# ----------------------------------------------------------------------
# Main extraction pipeline
# ----------------------------------------------------------------------
def run_extraction(
    labeled_path: str,
    output_path: str,
    raw_dir: Optional[Path] = None,
) -> bool:
    """
    Load the labeled CSV, enrich it with metrics derived from the raw JSON,
    and write the final CSV.

    Returns ``True`` on success, ``False`` otherwise.
    """
    logger = setup_logging(script_name="extract_metrics")
    logger = get_logger("extract_metrics")
    logger.info(f"Loading labeled data from {labeled_path}")

    # ------------------------------------------------------------------
    # Load inputs
    # ------------------------------------------------------------------
    if not os.path.exists(labeled_path):
        logger.error(f"Labeled CSV not found: {labeled_path}")
        return False

    # Use pandas for convenience – the dataset fits comfortably in memory.
    df = pd.read_csv(labeled_path, dtype={"pr_id": int})
    logger.info(f"Loaded {len(df)} labeled PR rows")

    # Load raw JSON payloads
    raw_dir = raw_dir or get_path("raw")
    raw_prs = load_raw_prs(raw_dir)
    logger.info(f"Loaded {len(raw_prs)} raw PR objects")

    # Prepare containers for new columns
    comment_counts: List[int] = []
    time_to_merge: List[Optional[float]] = []
    review_cycles: List[int] = []
    hour_of_day: List[int] = []
    day_of_week: List[int] = []
    defect_counts: List[int] = []
    defect_density: List[float] = []

    rows_to_keep = []  # indices of rows where we have a valid merge time

    for idx, row in df.iterrows():
        pr_id = int(row["pr_id"])
        raw = raw_prs.get(pr_id)

        if raw is None:
            logger.warning(f"No raw payload for PR {pr_id}; skipping")
            continue

        # Comment count
        ccount = compute_comment_count(raw)
        comment_counts.append(ccount)

        # Time to merge (skip rows without a merge)
        ttm = compute_time_to_merge_minutes(raw)
        if ttm is None:
            logger.info(f"PR {pr_id} not merged; omitting from final CSV")
            continue  # Omit this PR per specification
        time_to_merge.append(ttm)

        # Review cycles
        review_cycles.append(compute_review_cycles(ccount))

        # Temporal covariates
        hod, dow = compute_temporal_features(raw)
        hour_of_day.append(hod)
        day_of_week.append(dow)

        # Defect count
        dcount = compute_defect_count(raw)
        defect_counts.append(dcount)

        # Defect density (loc column must exist in the labeled data)
        loc = row.get("loc")
        if pd.isna(loc) or loc == 0:
            density = 0.0
        else:
            density = dcount / float(loc)
        defect_density.append(density)

        rows_to_keep.append(idx)

    if not rows_to_keep:
        logger.error("No PRs with a valid merge timestamp were found.")
        return False

    # Slice the original dataframe to the rows we kept and add new columns
    final_df = df.iloc[rows_to_keep].copy()
    final_df["comment_count"] = comment_counts
    final_df["time_to_merge_minutes"] = time_to_merge
    final_df["review_cycles"] = review_cycles
    final_df["hour_of_day"] = hour_of_day
    final_df["day_of_week"] = day_of_week
    final_df["defect_count"] = defect_counts
    final_df["defect_density"] = defect_density

    # Ensure output directory exists
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV
    final_df.to_csv(out_path, index=False)
    logger.info(f"Wrote enriched metrics CSV with {len(final_df)} rows to {out_path}")
    return True

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract PR review metrics, temporal covariates, and defect density (T009)"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the labeled PR CSV (e.g., data/processed/prs_labeled_complex.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path for the output metrics CSV (e.g., data/processed/prs_metrics.csv)",
    )
    args = parser.parse_args()

    success = run_extraction(
        labeled_path=args.input,
        output_path=args.output,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()