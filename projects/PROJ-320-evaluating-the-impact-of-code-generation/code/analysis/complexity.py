"""
Complexity Analysis Script (T008)

This script reads the labeled PR dataset, attempts to fetch the full diff for each PR
via the GitHub API, computes cyclomatic complexity and lines‑of‑code (LOC) using the
helpers defined in this module, and writes two artefacts:

1. ``data/processed/complexity_scores.csv`` – contains ``pr_id``, ``loc`` and
   ``complexity_score`` (cyclomatic complexity).
2. ``data/processed/prs_labeled_complex.csv`` – the original labelled CSV with the
   two new columns merged back in (overwrites existing ``loc`` and ``complexity_score``
   fields).

If the diff cannot be fetched or memory usage exceeds the 6 GB threshold, the
script falls back to a simple metric based on added/removed lines extracted from
the diff (or zeros if the diff is unavailable).

The script is safe to run repeatedly; it overwrites the output files.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import requests

# Project utilities
from utils.logging import get_logger, setup_logging
from utils.seeds import set_global_seed
from utils.config import get_config_summary

# Local complexity helpers (already defined in this file)
import ast
import resource
import networkx as nx

SEED = 42
set_global_seed(SEED)

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Memory utilities
# ----------------------------------------------------------------------
def get_memory_usage_mb() -> float:
    """Return current process memory usage in megabytes."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in kilobytes on Linux
    return usage.ru_maxrss / 1024.0

def check_memory_and_fallback(threshold_mb: float = 6000.0) -> bool:
    """
    Return ``True`` if current memory usage exceeds ``threshold_mb``.
    """
    current = get_memory_usage_mb()
    if current > threshold_mb:
        logger.log(
            "memory_warning",
            f"Memory usage {current:.1f} MB exceeds threshold {threshold_mb:.1f} MB – using fallback."
        )
        return True
    return False

# ----------------------------------------------------------------------
# Basic metric calculators
# ----------------------------------------------------------------------
def calculate_loc(code_snippet: str) -> int:
    """Count non‑empty, non‑comment lines in ``code_snippet``."""
    if not code_snippet:
        return 0
    count = 0
    in_multiline = False
    for line in code_snippet.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if '"""' in stripped or "'''" in stripped:
            # toggle multiline string state
            if stripped.count('"""') % 2 != 0 or stripped.count("'''") % 2 != 0:
                in_multiline = not in_multiline
                continue
            if in_multiline:
                continue
        count += 1
    return count

def calculate_cyclomatic_complexity_ast(code_snippet: str) -> int:
    """Compute cyclomatic complexity from an AST."""
    if not code_snippet:
        return 1  # minimal complexity
    try:
        tree = ast.parse(code_snippet)
    except SyntaxError:
        return 1
    complexity = 1
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.For, ast.While, ast.AsyncFor, ast.ExceptHandler, ast.Assert, ast.comprehension)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            # each 'and'/'or' adds a decision point
            complexity += len(node.values) - 1
    return complexity

# ----------------------------------------------------------------------
# Diff handling
# ----------------------------------------------------------------------
def extract_added_removed_lines(diff_text: str) -> Tuple[int, int]:
    """
    Very simple line‑count based metric:
    ``added`` = number of lines starting with '+' (excluding diff headers)
    ``removed`` = number of lines starting with '-' (excluding diff headers)
    """
    added = removed = 0
    for line in diff_text.splitlines():
        if line.startswith('+++') or line.startswith('---') or line.startswith('@@'):
            continue
        if line.startswith('+'):
            added += 1
        elif line.startswith('-'):
            removed += 1
    return added, removed

def analyze_diff_complexity(diff_text: str) -> Dict[str, int]:
    """
    Compute LOC and cyclomatic complexity from the *added* portion of a diff.
    """
    added_lines = [
        line[1:] for line in diff_text.splitlines()
        if line.startswith('+') and not line.startswith('+++')
    ]
    code_block = "\n".join(added_lines)
    loc = calculate_loc(code_block)
    cyclomatic = calculate_cyclomatic_complexity_ast(code_block)
    return {"loc": loc, "cyclomatic": cyclomatic}

# ----------------------------------------------------------------------
# GitHub interaction
# ----------------------------------------------------------------------
def github_api_get(url: str, headers: Dict[str, str] | None = None) -> requests.Response:
    """
    Perform a GET request to the GitHub API, handling optional authentication.
    """
    token = os.getenv("GITHUB_TOKEN")
    auth_headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        auth_headers["Authorization"] = f"token {token}"
    if headers:
        auth_headers.update(headers)
    response = requests.get(url, headers=auth_headers, timeout=30)
    # Basic exponential back‑off for rate‑limit or transient errors
    retries = 0
    backoff = 1
    while response.status_code in {429, 500, 502, 503, 504} and retries < 3:
        logger.log(
            "github_backoff",
            f"{url} returned {response.status_code}; retry {retries + 1} after {backoff}s"
        )
        time.sleep(backoff)
        retries += 1
        backoff *= 2
        response = requests.get(url, headers=auth_headers, timeout=30)
    response.raise_for_status()
    return response

def fetch_diff(repo: str, pr_number: str) -> str | None:
    """
    Retrieve the unified diff for a PR.

    Returns ``None`` if the diff cannot be obtained.
    """
    try:
        # 1. Pull request metadata
        pr_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
        pr_resp = github_api_get(pr_url)
        pr_data = pr_resp.json()
        diff_url = pr_data.get("diff_url")
        if not diff_url:
            logger.log(
                "diff_missing",
                f"PR {repo}#{pr_number} has no diff_url."
            )
            return None

        # 2. Fetch the raw diff
        diff_resp = github_api_get(diff_url, headers={"Accept": "application/vnd.github.v3.diff"})
        return diff_resp.text
    except Exception as exc:
        logger.log(
            "diff_fetch_error",
            f"Failed to fetch diff for {repo}#{pr_number}: {exc}"
        )
        return None

# ----------------------------------------------------------------------
# Main processing
# ----------------------------------------------------------------------
def compute_complexity_for_prs(
    input_csv_path: str,
    complexity_csv_path: str,
    merged_csv_path: str
) -> None:
    """
    Compute complexity metrics for all PRs in ``input_csv_path``.

    * Writes ``complexity_csv_path`` with columns: ``pr_id``, ``loc``,
      ``complexity_score`` (cyclomatic complexity).
    * Merges those columns back into the original CSV and writes the result to
      ``merged_csv_path`` (named ``prs_labeled_complex.csv``).
    """
    logger.log(
        "start_complexity_analysis",
        f"input={input_csv_path} complexity_out={complexity_csv_path} merged_out={merged_csv_path}"
    )

    if not os.path.exists(input_csv_path):
        raise FileNotFoundError(f"Input file not found: {input_csv_path}")

    # ------------------------------------------------------------------
    # Load input rows
    # ------------------------------------------------------------------
    with open(input_csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    results: List[Dict[str, int]] = []

    for row in rows:
        pr_id = row.get("pr_id")
        repo = row.get("repo")
        if not pr_id or not repo:
            logger.log(
                "row_skip",
                f"Missing pr_id or repo in row: {row}"
            )
            continue

        diff_text = fetch_diff(repo, pr_id)
        if diff_text:
            # Decide whether to use full analysis or fallback based on memory
            if check_memory_and_fallback():
                added, removed = extract_added_removed_lines(diff_text)
                loc = added + removed
                cyclomatic = loc  # simple proxy when falling back
            else:
                metrics = analyze_diff_complexity(diff_text)
                loc = metrics["loc"]
                cyclomatic = metrics["cyclomatic"]
        else:
            # No diff – fallback to zeros (or could use added/removed if available elsewhere)
            loc = 0
            cyclomatic = 1  # minimal complexity

        results.append({
            "pr_id": int(pr_id),
            "loc": loc,
            "complexity_score": cyclomatic
        })

    # ------------------------------------------------------------------
    # Write complexity_scores.csv
    # ------------------------------------------------------------------
    os.makedirs(os.path.dirname(complexity_csv_path), exist_ok=True)
    with open(complexity_csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["pr_id", "loc", "complexity_score"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.log(
        "complexity_file_written",
        f"Wrote {len(results)} rows to {complexity_csv_path}"
    )

    # ------------------------------------------------------------------
    # Merge back into original CSV
    # ------------------------------------------------------------------
    # Build lookup dict for fast merge
    complexity_lookup = {r["pr_id"]: r for r in results}
    merged_rows = []
    for row in rows:
        pid = int(row["pr_id"])
        comp = complexity_lookup.get(pid, {"loc": 0, "complexity_score": 1})
        # Overwrite (or add) the columns
        row["loc"] = comp["loc"]
        row["complexity_score"] = comp["complexity_score"]
        merged_rows.append(row)

    os.makedirs(os.path.dirname(merged_csv_path), exist_ok=True)
    with open(merged_csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = merged_rows[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged_rows)

    logger.log(
        "merged_file_written",
        f"Merged complexity columns into {merged_csv_path}"
    )

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute code‑complexity metrics for PRs (T008)."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to input CSV (prs_labeled.csv)."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to output complexity CSV (complexity_scores.csv)."
    )
    args = parser.parse_args()

    # Initialise logging
    setup_logging()

    # Determine merged output path (fixed name as per spec)
    merged_path = Path(args.output).parent / "prs_labeled_complex.csv"

    compute_complexity_for_prs(
        input_csv_path=args.input,
        complexity_csv_path=args.output,
        merged_csv_path=str(merged_path)
    )

if __name__ == "__main__":
    main()
