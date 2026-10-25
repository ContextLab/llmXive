"""
Preprocess raw PR data and construct triangulated ground truth.

This script performs the following steps (FR‑011):
1. Load all JSON payloads from ``data/raw/`` (excluding ``checksums.json``).
2. Truncate diffs that exceed the LLM context window and log a warning.
3. Build a triangulated ground‑truth label for each PR:
   a) The PR must be linked to at least one **closed** issue.
   b) At least two *independent* human reviewers must have confirmed the bug
      in their comments (simple heuristic based on the presence of the word
      “bug”, “issue”, or “fix” – case‑insensitive).
4. Abort with an ``audit_failure`` event and exit code 1 if fewer than
   50 PRs satisfy the triangulated ground‑truth criteria.
5. Write cleaned PR records to ``data/derived/prs_cleaned.json`` and a
   human‑annotation file to ``data/annotations/human_annotations.json``.
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# llmxive toolkit helpers for deterministic path handling and logging
from llmxive_toolkit import paths, get_logger

# Project configuration utilities
from code.config.settings import get_paths, ensure_directories, get_hyperparams

# ----------------------------------------------------------------------
# Logging setup
# ----------------------------------------------------------------------
log = get_logger(__name__)  # writes to ``logs/pipeline.jsonl`` by default
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def estimate_tokens(text: str) -> int:
    """
    Rough token estimate – 1 token ≈ 4 characters.
    """
    if not isinstance(text, str):
        raise TypeError("estimate_tokens expects a string")
    return len(text) // 4

def truncate_diff(diff_text: str, max_tokens: int) -> str:
    """
    Truncate a diff if its token count exceeds ``max_tokens``.
    Returns the original diff when it fits, otherwise a truncated version
    with a clear ``[TRUNCATED]`` marker.
    """
    if not isinstance(diff_text, str):
        raise TypeError("truncate_diff expects a string")
    if estimate_tokens(diff_text) <= max_tokens:
        return diff_text

    # Simple truncation: keep the first and last portions that fit.
    # This mirrors the behaviour of ``src.extraction.preprocess``.
    tokens = diff_text.split()
    keep_ratio = max_tokens / len(tokens)
    keep_start = int(len(tokens) * keep_ratio / 2)
    keep_end = len(tokens) - keep_start
    truncated = " ".join(tokens[:keep_start]) + "\n[TRUNCATED]\n" + " ".join(tokens[keep_end:])
    logger.warning(
        f"Diff truncated from {len(tokens)} tokens to {max_tokens} tokens."
    )
    return truncated

def load_raw_prs(raw_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all PR JSON payloads from ``raw_dir`` (ignoring ``checksums.json``).
    Handles both a single list per file and a dict with a ``prs`` key.
    """
    pr_records: List[Dict[str, Any]] = []
    for file_path in raw_dir.glob("*.json"):
        if file_path.name == "checksums.json":
            continue
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            log.error(event="json_decode_error", file=str(file_path), error=str(exc))
            continue

        if isinstance(data, list):
            pr_records.extend(data)
        elif isinstance(data, dict):
            if "prs" in data and isinstance(data["prs"], list):
                pr_records.extend(data["prs"])
            else:
                pr_records.append(data)
        else:
            log.warning(event="unexpected_payload_type", file=str(file_path))
    return pr_records

def reviewer_confirmation_count(comments: List[str]) -> int:
    """
    Heuristic: count comments that contain at least one of the keywords
    indicating a reviewer confirmed a bug.
    """
    keywords = {"bug", "issue", "fix", "error", "problem"}
    count = 0
    for comment in comments:
        lowered = comment.lower()
        if any(kw in lowered for kw in keywords):
            count += 1
    return count

def build_ground_truth(prs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Construct a list of human annotations (ground truth) according to FR‑011.
    Each annotation dictionary contains:
        - ``pr_id`` (int or str)
        - ``verified_bug`` (bool)
        - ``closed_issue`` (bool)
        - ``reviewer_confirmations`` (int)
    """
    annotations: List[Dict[str, Any]] = []

    for pr in prs:
        pr_id = pr.get("pr_id") or pr.get("pr_number") or pr.get("number")
        # Linked issues – list of dicts (as built in fetch_prs) or just IDs
        linked_issues = pr.get("linked_issues", [])
        # Normalise to list of dicts with ``state`` field
        closed_issue = any(
            isinstance(issue, dict) and issue.get("state", "").lower() == "closed"
            for issue in linked_issues
        )
        # Human review comments – already a flat list of comment bodies
        comments = pr.get("human_review_comments", [])
        confirmations = reviewer_confirmation_count(comments)

        verified_bug = closed_issue and confirmations >= 2

        annotation = {
            "pr_id": pr_id,
            "verified_bug": verified_bug,
            "closed_issue": closed_issue,
            "reviewer_confirmations": confirmations,
        }
        annotations.append(annotation)

    return annotations

def write_json(path: Path, data: Any) -> None:
    """Write ``data`` as pretty‑printed JSON to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main() -> int:
    """
    Entry point for ``python -m src.extraction.preprocess_and_ground_truth``.
    Returns exit code 0 on success, 1 on audit failure.
    """
    # Ensure all required directories exist
    ensure_directories()
    cfg_paths = get_paths()

    raw_dir = Path(cfg_paths["data_raw"])
    derived_dir = Path(cfg_paths["data_derived"])
    annotations_dir = Path(cfg_paths["data_annotations"])

    # ------------------------------------------------------------------
    # 1. Load raw PR payloads
    # ------------------------------------------------------------------
    prs = load_raw_prs(raw_dir)
    if not prs:
        log.error(event="no_prs_loaded", message="No PR payloads found in data/raw/")
        return 1

    # ------------------------------------------------------------------
    # 2. Truncate diffs that exceed the context window
    # ------------------------------------------------------------------
    hyperparams = get_hyperparams()
    max_tokens = hyperparams.get("max_context_tokens", 8000)  # default if not set
    for pr in prs:
        if "diff" in pr and isinstance(pr["diff"], str):
            original_len = estimate_tokens(pr["diff"])
            if original_len > max_tokens:
                pr["diff"] = truncate_diff(pr["diff"], max_tokens)
                log.warning(
                    event="diff_truncated",
                    pr_id=pr.get("pr_id"),
                    original_tokens=original_len,
                    max_tokens=max_tokens,
                )

    # ------------------------------------------------------------------
    # 3. Build triangulated ground truth
    # ------------------------------------------------------------------
    annotations = build_ground_truth(prs)

    # Count verified PRs
    verified_count = sum(1 for ann in annotations if ann["verified_bug"])
    if verified_count < 50:
        # Emit audit_failure event and abort
        log.error(
            event="audit_failure",
            message=f"Only {verified_count} verified PRs found (minimum required is 50).",
        )
        return 1

    # ------------------------------------------------------------------
    # 4. Write outputs
    # ------------------------------------------------------------------
    cleaned_path = derived_dir / "prs_cleaned.json"
    annotations_path = annotations_dir / "human_annotations.json"

    write_json(cleaned_path, prs)
    write_json(annotations_path, annotations)

    log.info(
        event="preprocess_and_ground_truth_complete",
        cleaned_prs_path=str(cleaned_path),
        annotations_path=str(annotations_path),
        verified_prs=verified_count,
    )
    return 0

if __name__ == "__main__":
    sys.exit(main())