"""
Tag-to-Repository/Package Mapping Logic (Task T015).

This module implements the logic to map Stack Overflow tags to GitHub repositories
and NPM packages using the raw metrics and candidate data fetched by T039.

It reads `data/processed/external_metrics.json`, performs the mapping selection,
writes `data/processed/tag_mappings.json`, and logs unmapped tags to
`data/processed/unmapped_tags.log`.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/processed/mapping_process.log')
    ]
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "external_metrics.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "tag_mappings.json"
UNMAPPED_LOG = PROJECT_ROOT / "data" / "processed" / "unmapped_tags.log"


def load_external_metrics() -> Dict[str, Any]:
    """
    Load the external metrics data fetched by T039.

    Returns:
        Dict containing the raw metrics and candidate matches.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or malformed.
    """
    if not INPUT_FILE.exists():
        logger.critical(f"Input file not found: {INPUT_FILE}")
        raise FileNotFoundError(
            f"Critical Error: {INPUT_FILE} does not exist. "
            "Ensure T039 (external.py) has completed successfully."
        )

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.critical(f"Failed to parse JSON in {INPUT_FILE}: {e}")
        raise ValueError(f"Malformed JSON in {INPUT_FILE}")

    if not data:
        logger.critical(f"Input file {INPUT_FILE} is empty or contains no data.")
        raise ValueError(f"Input file {INPUT_FILE} is empty.")

    logger.info(f"Successfully loaded external metrics from {INPUT_FILE}")
    return data


def select_best_candidate(tag: str, candidates: List[Dict[str, Any]], source_type: str) -> Optional[Dict[str, Any]]:
    """
    Select the best candidate repository/package for a given tag.

    Strategy:
    1. Prefer candidates with the highest star count (GitHub) or download count (NPM).
    2. If counts are equal or missing, prefer the first one (most relevant search result).
    3. Filter out candidates with zero stars/downloads if possible.

    Args:
        tag: The Stack Overflow tag name.
        candidates: List of candidate dicts from the external fetch.
        source_type: 'github' or 'npm'.

    Returns:
        The best candidate dict, or None if no suitable candidate exists.
    """
    if not candidates:
        return None

    # Filter out empty/invalid candidates
    valid_candidates = [
        c for c in candidates
        if c.get('stars') is not None or c.get('downloads') is not None
    ]

    if not valid_candidates:
        # Fallback to first candidate even if metrics are missing (e.g. private repo)
        valid_candidates = candidates

    # Sort by metric descending
    if source_type == 'github':
        sorted_candidates = sorted(
            valid_candidates,
            key=lambda x: x.get('stars', 0) or 0,
            reverse=True
        )
    else:  # npm
        sorted_candidates = sorted(
            valid_candidates,
            key=lambda x: x.get('downloads', 0) or 0,
            reverse=True
        )

    return sorted_candidates[0]


def map_tag_to_repos(external_data: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Process the external data to create final tag mappings.

    Iterates through the tags found in the external data, selects the best
    candidate for each, and separates unmapped tags.

    Args:
        external_data: The loaded data from load_external_metrics().

    Returns:
        Tuple of (list of mapping dicts, list of unmapped tag names).
    """
    mappings = []
    unmapped_tags = []

    # The structure from T039 is expected to be a dict with 'github' and 'npm' keys
    # Each containing a list of entries or a dict keyed by tag.
    # Based on T039 description: "write the fetched raw metrics and candidate matches"
    # We assume a structure like: {"github": {tag: [candidates]}, "npm": {tag: [candidates]}}
    # or a list of objects. We will handle the most common robust structure.

    github_data = external_data.get('github', {})
    npm_data = external_data.get('npm', {})

    # Normalize input to a unified dict of tag -> {github: [...], npm: [...]}
    all_tags = set(github_data.keys()) | set(npm_data.keys())

    for tag in all_tags:
        github_candidates = github_data.get(tag, [])
        npm_candidates = npm_data.get(tag, [])

        # Ensure candidates are lists
        if isinstance(github_candidates, dict):
            github_candidates = list(github_candidates.values())
        if isinstance(npm_candidates, dict):
            npm_candidates = list(npm_candidates.values())

        best_github = select_best_candidate(tag, github_candidates, 'github')
        best_npm = select_best_candidate(tag, npm_candidates, 'npm')

        mapping_entry = {
            "tag": tag,
            "github_repo": best_github,
            "npm_package": best_npm,
            "mapping_status": "mapped"
        }

        # Check if we actually found a match for either
        if best_github is None and best_npm is None:
            mapping_entry["mapping_status"] = "unmapped"
            unmapped_tags.append(tag)
            logger.warning(f"Tag '{tag}' could not be mapped to any GitHub repo or NPM package.")
        else:
            logger.info(f"Tag '{tag}' mapped to: "
                        f"GitHub({best_github['name'] if best_github else 'None'}), "
                        f"NPM({best_npm['name'] if best_npm else 'None'})")

        mappings.append(mapping_entry)

    return mappings, unmapped_tags


def run_mapping_pipeline():
    """
    Main entry point for the mapping pipeline (T015).

    1. Verifies input file existence.
    2. Loads external metrics.
    3. Performs mapping logic.
    4. Writes tag_mappings.json.
    5. Writes unmapped_tags.log (if any).
    """
    logger.info("Starting Tag-to-Repo Mapping Pipeline (T015)...")

    try:
        # 1. Load Data
        external_data = load_external_metrics()

        # 2. Perform Mapping
        mappings, unmapped_tags = map_tag_to_repos(external_data)

        # 3. Write Output: tag_mappings.json
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully wrote {len(mappings)} mappings to {OUTPUT_FILE}")

        # 4. Write Output: unmapped_tags.log (newline-delimited JSON)
        if unmapped_tags:
            UNMAPPED_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(UNMAPPED_LOG, 'w', encoding='utf-8') as f:
                for tag in unmapped_tags:
                    f.write(json.dumps({"tag": tag, "status": "unmapped"}) + '\n')
            logger.warning(f"Wrote {len(unmapped_tags)} unmapped tags to {UNMAPPED_LOG}")
        else:
            logger.info("All tags successfully mapped. No unmapped_tags.log generated.")

        logger.info("Mapping Pipeline completed successfully.")
        return True

    except FileNotFoundError as e:
        logger.critical(f"Pipeline failed: {e}")
        raise
    except Exception as e:
        logger.critical(f"Unexpected error during mapping: {e}")
        raise


def main():
    """Standard entry point for execution."""
    run_mapping_pipeline()


if __name__ == "__main__":
    main()