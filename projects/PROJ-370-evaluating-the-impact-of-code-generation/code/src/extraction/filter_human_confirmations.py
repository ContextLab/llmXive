"""
T014c: Filter human confirmations from raw comments.

Reads data/annotations/raw_comments.json (produced by T014b),
applies a standardized rubric to identify explicit bug confirmations,
and writes data/derived/human_confirmations.json.

Rubric (case-insensitive substring match on comment body):
  - "bug confirmed"
  - "confirmed bug"
  - "merged with fix"
  - "lgtm with fix"
  - "fixed and merged"
  - "addressed and merged"
  - "resolved"
  - "verified"

Output schema (per task spec):
  [
    {
      "pr_id": int,
      "file_path": str,
      "line_start": int,
      "line_end": int,
      "reviewer_id": str,
      "confirmation_type": str  # One of the matched rubric phrases (normalized)
    },
    ...
  ]
"""

import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from code.config.settings import get_paths, ensure_directories
from code.src.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Standardized rubric phrases (lowercase for matching)
CONFIRMATION_PHRASES = [
    "bug confirmed",
    "confirmed bug",
    "merged with fix",
    "lgtm with fix",
    "fixed and merged",
    "addressed and merged",
    "resolved",
    "verified"
]

def normalize_phrase(phrase: str) -> str:
    """Normalize a matched phrase for output."""
    return phrase.strip().lower()

def find_confirmation_type(comment_body: str) -> Optional[str]:
    """
    Check if comment_body contains any confirmation phrase.
    Returns the matched phrase (normalized) or None.
    """
    lower_body = comment_body.lower()
    for phrase in CONFIRMATION_PHRASES:
        if phrase in lower_body:
            return normalize_phrase(phrase)
    return None

def extract_location_from_comment(comment: Dict[str, Any]) -> Tuple[Optional[str], Optional[int], Optional[int]]:
    """
    Extract file_path, line_start, line_end from a comment.
    Comments may be review comments (with path/line) or issue comments (no location).
    Returns (file_path, line_start, line_end).
    """
    file_path = comment.get("path")
    line_start = comment.get("line") or comment.get("position")
    line_end = line_start  # Default to single line if not specified

    # Handle diff hunk positions if available (simplified: treat as single line)
    if line_start is None and "original_line" in comment:
        line_start = comment["original_line"]
        line_end = comment.get("current_line", line_start)

    return file_path, line_start, line_end

def filter_confirmations(raw_comments_path: Path) -> List[Dict[str, Any]]:
    """
    Read raw comments, filter for confirmations, and format output.
    """
    if not raw_comments_path.exists():
        raise FileNotFoundError(f"Input file not found: {raw_comments_path}")

    logger.info(f"Loading raw comments from {raw_comments_path}")
    with open(raw_comments_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    confirmations = []
    processed_count = 0
    confirmed_count = 0

    # raw_data structure expected:
    # {
    #   "repo": "...",
    #   "prs": [
    #     { "pr_id": 123, "comments": [ { "reviewer_id": "...", "body": "...", ... }, ... ] },
    #     ...
    #   ]
    # }
    # OR a flat list of comments with pr_id attached.
    # We handle both.

    prs = raw_data.get("prs", raw_data if isinstance(raw_data, list) else [])

    for pr_entry in prs:
        pr_id = pr_entry.get("pr_id")
        if pr_id is None:
            logger.warning("Skipping entry without pr_id")
            continue

        comments = pr_entry.get("comments", [])
        if not isinstance(comments, list):
            logger.warning(f"PR {pr_id} has no comments or invalid format")
            continue

        for comment in comments:
            processed_count += 1
            body = comment.get("body", "")
            if not body:
                continue

            confirmation_type = find_confirmation_type(body)
            if not confirmation_type:
                continue

            confirmed_count += 1
            reviewer_id = comment.get("reviewer_id") or comment.get("user", {}).get("login", "unknown")
            file_path, line_start, line_end = extract_location_from_comment(comment)

            # Only include if we have a location (file/line)
            # If it's an issue comment without location, we might skip or mark as global.
            # Per task spec, we need file_path and line_start/line_end.
            if file_path is None or line_start is None:
                logger.debug(f"Skipping confirmation in PR {pr_id} (no location info): {comment.get('id')}")
                continue

            entry = {
                "pr_id": pr_id,
                "file_path": file_path,
                "line_start": int(line_start),
                "line_end": int(line_end),
                "reviewer_id": str(reviewer_id),
                "confirmation_type": confirmation_type
            }
            confirmations.append(entry)

    logger.info(f"Processed {processed_count} comments, found {confirmed_count} confirmations")
    return confirmations

def save_confirmations(confirmations: List[Dict[str, Any]], output_path: Path) -> None:
    """Save the filtered confirmations to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(confirmations, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(confirmations)} confirmations to {output_path}")

def main() -> None:
    """Main entry point for T014c."""
    paths = get_paths()
    input_path = paths["annotations_raw"]
    output_path = paths["derived_human_confirmations"]

    ensure_directories([output_path.parent])

    logger.info("Starting T014c: Filter human confirmations")

    try:
        confirmations = filter_confirmations(input_path)
        save_confirmations(confirmations, output_path)
        logger.info("T014c completed successfully")
    except FileNotFoundError as e:
        logger.error(f"Input data missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during filtering: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
