"""
Preprocessing module for PR data extraction.

Handles:
- Diff truncation for context window limits
- Raw comment extraction
- Checksum generation for data integrity
- Human baseline triangulation
"""
import os
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from code.config.settings import get_paths, ensure_directories
from code.src.utils.logger import get_logger

logger = get_logger(__name__)


def estimate_tokens(text: str) -> int:
    """
    Rough token estimation: 1 token ≈ 4 characters for English text.
    This is a heuristic used to decide if truncation is needed.
    """
    if not text:
        return 0
    return len(text) // 4


def truncate_diff(diff_text: str, max_tokens: int = 8000) -> str:
    """
    Truncate diff text to fit within max_tokens limit.
    
    Args:
        diff_text: The raw diff content.
        max_tokens: Maximum allowed tokens (default 8000).
        
    Returns:
        Truncated diff text.
    """
    current_tokens = estimate_tokens(diff_text)
    
    if current_tokens <= max_tokens:
        return diff_text
    
    # Calculate approximate cut-off point
    # We truncate by character count based on token ratio
    ratio = max_tokens / current_tokens
    max_chars = int(len(diff_text) * ratio)
    
    truncated = diff_text[:max_chars]
    
    logger.warning(
        f"Diff truncated from {current_tokens} to {max_tokens} tokens "
        f"({len(truncated)} chars)."
    )
    
    return truncated


def preprocess_pr_data(pr_data: Dict[str, Any], max_tokens: int = 8000) -> Dict[str, Any]:
    """
    Preprocess a single PR data entry.
    
    - Truncates diffs exceeding context window
    - Validates structure
    
    Args:
        pr_data: Dictionary containing PR information.
        max_tokens: Maximum tokens for diff content.
        
    Returns:
        Processed PR data dictionary.
    """
    processed = pr_data.copy()
    
    if "diffs" in processed and isinstance(processed["diffs"], list):
        for i, diff_entry in enumerate(processed["diffs"]):
            if "diff_content" in diff_entry:
                original_len = len(diff_entry["diff_content"])
                diff_entry["diff_content"] = truncate_diff(
                    diff_entry["diff_content"], max_tokens
                )
                if len(diff_entry["diff_content"]) != original_len:
                    diff_entry["truncated"] = True
                else:
                    diff_entry["truncated"] = False
    
    return processed


def extract_raw_comments(pr_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract raw review comments from PR data.
    
    Args:
        pr_data_list: List of PR data dictionaries.
        
    Returns:
        List of extracted comment dictionaries.
    """
    comments = []
    
    for pr in pr_data_list:
        pr_id = pr.get("pr_id", "unknown")
        
        if "comments" in pr:
            for comment in pr["comments"]:
                comments.append({
                    "pr_id": pr_id,
                    "comment_id": comment.get("id", "unknown"),
                    "author": comment.get("user", {}).get("login", "unknown"),
                    "body": comment.get("body", ""),
                    "created_at": comment.get("created_at", ""),
                    "path": comment.get("path", ""),
                    "line": comment.get("line", None),
                    "original_line": comment.get("original_line", None),
                })
        
        # Also check for review comments (threaded)
        if "review_comments" in pr:
            for comment in pr["review_comments"]:
                comments.append({
                    "pr_id": pr_id,
                    "comment_id": comment.get("id", "unknown"),
                    "author": comment.get("user", {}).get("login", "unknown"),
                    "body": comment.get("body", ""),
                    "created_at": comment.get("created_at", ""),
                    "path": comment.get("path", ""),
                    "line": comment.get("line", None),
                    "original_line": comment.get("original_line", None),
                })
    
    return comments


def generate_checksums(file_paths: List[Path]) -> Dict[str, str]:
    """
    Generate SHA-256 checksums for a list of files.
    
    Args:
        file_paths: List of Path objects pointing to files.
        
    Returns:
        Dictionary mapping file basename to SHA-256 hex digest.
    """
    checksums = {}
    
    for file_path in file_paths:
        if not file_path.exists():
            logger.warning(f"File not found, skipping checksum: {file_path}")
            continue
        
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            checksums[file_path.name] = sha256_hash.hexdigest()
            logger.info(f"Generated checksum for {file_path.name}: {checksums[file_path.name][:16]}...")
            
        except Exception as e:
            logger.error(f"Failed to compute checksum for {file_path}: {e}")
    
    return checksums


def save_raw_with_checksums(pr_data_list: List[Dict[str, Any]], output_dir: Path) -> None:
    """
    Save raw PR data to JSON and generate SHA-256 checksums.
    
    This function implements T015:
    - Saves raw JSON to data/raw/
    - Generates data/raw/checksums.json
    
    Args:
        pr_data_list: List of PR data dictionaries.
        output_dir: Directory to save files (should be data/raw/).
    """
    ensure_directories([output_dir])
    
    # Save raw JSON
    timestamp = None
    if pr_data_list and "timestamp" in pr_data_list[0]:
        timestamp = pr_data_list[0]["timestamp"]
    
    if timestamp:
        output_file = output_dir / f"pr_data_{timestamp.replace(':', '-')}.json"
    else:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"pr_data_{timestamp}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(pr_data_list, f, indent=2, default=str)
    
    logger.info(f"Saved raw PR data to {output_file}")
    
    # Generate checksums for all JSON files in the directory
    json_files = list(output_dir.glob("*.json"))
    checksums = generate_checksums(json_files)
    
    # Save checksums file
    checksums_file = output_dir / "checksums.json"
    with open(checksums_file, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)
    
    logger.info(f"Saved checksums to {checksums_file}")


def generate_human_baseline(pr_data_list: List[Dict[str, Any]], 
                             llm_detections: List[Dict[str, Any]],
                             output_path: Path) -> None:
    """
    Generate triangulated ground truth baseline.
    
    Requirements (FR-011):
    - Requires linked issue AND ≥2 independent reviewers
    - Excludes bugs not meeting strict criteria
    - Flags excluded bugs
    
    Args:
        pr_data_list: List of PR data dictionaries.
        llm_detections: List of LLM detection results.
        output_path: Path to save human_baseline.json.
    """
    ensure_directories([output_path.parent])
    
    baseline = []
    
    # This is a placeholder for the actual triangulation logic
    # which would merge PR data with review annotations
    # For T015, this function is defined but the main focus is checksums
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2)
    
    logger.info(f"Generated human baseline (empty) at {output_path}")


def main():
    """
    Main entry point for preprocessing.
    
    Usage:
        python -m code.src.extraction.preprocess
    
    This script:
    1. Loads raw PR data from data/raw/ (if exists)
    2. Preprocesses diffs (truncation)
    3. Extracts raw comments to data/annotations/raw_comments.json
    4. Saves raw JSON with checksums to data/raw/checksums.json
    """
    paths = get_paths()
    raw_dir = paths["raw"]
    annotations_dir = paths["annotations"]
    
    ensure_directories([raw_dir, annotations_dir])
    
    # Check if raw data exists
    raw_files = list(raw_dir.glob("pr_data_*.json"))
    
    if not raw_files:
        logger.warning("No raw PR data found. Run fetch_prs.py first.")
        return
    
    # Process the most recent raw file
    latest_file = max(raw_files, key=lambda p: p.stat().st_mtime)
    
    logger.info(f"Processing {latest_file}")
    
    with open(latest_file, "r", encoding="utf-8") as f:
        pr_data_list = json.load(f)
    
    # Preprocess diffs
    processed_data = []
    for pr in pr_data_list:
        processed = preprocess_pr_data(pr)
        processed_data.append(processed)
    
    # Save processed raw data (overwriting with checksums)
    save_raw_with_checksums(processed_data, raw_dir)
    
    # Extract and save raw comments
    comments = extract_raw_comments(processed_data)
    comments_file = annotations_dir / "raw_comments.json"
    
    with open(comments_file, "w", encoding="utf-8") as f:
        json.dump(comments, f, indent=2, default=str)
    
    logger.info(f"Saved {len(comments)} raw comments to {comments_file}")
    
    logger.info("Preprocessing complete.")


if __name__ == "__main__":
    main()
