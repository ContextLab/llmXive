"""
Tag-to-Repository Mapping Module (T015)

Implements the logic to map Stack Overflow tags to GitHub repositories and NPM packages
using the raw metrics fetched by T039 (data/processed/external_metrics.json).

This module adheres to FR-007:
- Reads raw external metrics.
- Performs mapping logic (best candidate selection).
- Outputs tag_mappings.json.
- Logs unmapped tags to unmapped_tags.log.
- Does NOT perform correlation calculations.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
INPUT_FILE = DATA_PROCESSED_DIR / "external_metrics.json"
OUTPUT_FILE = DATA_PROCESSED_DIR / "tag_mappings.json"
UNMAPPED_LOG_FILE = DATA_PROCESSED_DIR / "unmapped_tags.log"
CONTRACT_FILE = PROJECT_ROOT / "contracts" / "external_metrics.schema.yaml"

# Constants for mapping logic
MAX_REPOS_TO_CHECK = 5  # Limit candidates to top 5 to avoid noise
MIN_GITHUB_STARS = 100  # Minimum stars to consider a repo valid
MIN_NPM_DOWNLOADS = 1000  # Minimum weekly downloads to consider a package valid


def load_external_metrics() -> Dict[str, Any]:
    """
    Loads the external metrics JSON fetched by T039.
    
    Returns:
        Dict containing 'github_metrics' and 'npm_metrics'.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not INPUT_FILE.exists():
        logger.error(f"Input file not found: {INPUT_FILE}")
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    logger.info(f"Loading external metrics from {INPUT_FILE}")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Basic validation
    if not isinstance(data, dict):
        raise ValueError(f"Expected dict in {INPUT_FILE}, got {type(data)}")
        
    return data


def select_best_candidate(
    candidates: List[Dict[str, Any]], 
    source_type: str, 
    min_threshold: int
) -> Optional[Dict[str, Any]]:
    """
    Selects the best candidate repository/package from a list based on metrics.
    
    Args:
        candidates: List of candidate objects with 'stars' or 'downloads' keys.
        source_type: 'github' or 'npm'.
        min_threshold: Minimum metric value required for validity.
        
    Returns:
        The best candidate dict, or None if no valid candidate exists.
    """
    if not candidates:
        return None

    # Sort by metric descending (stars for GH, downloads for NPM)
    key = 'stars' if source_type == 'github' else 'downloads'
    
    # Filter valid candidates
    valid_candidates = [
        c for c in candidates 
        if c.get(key, 0) >= min_threshold
    ]

    if not valid_candidates:
        return None

    # Sort valid candidates by metric descending
    valid_candidates.sort(key=lambda x: x.get(key, 0), reverse=True)
    
    # Return the top one
    return valid_candidates[0]


def map_tag_to_repos(
    tag: str, 
    github_data: Optional[List[Dict]], 
    npm_data: Optional[List[Dict]]
) -> Dict[str, Any]:
    """
    Determines the best mapping for a single tag from GitHub and NPM candidates.
    
    Logic:
    1. Try to find a valid GitHub repo (stars >= MIN_GITHUB_STARS).
    2. Try to find a valid NPM package (downloads >= MIN_NPM_DOWNLOADS).
    3. If both exist, prefer the one with the higher relative popularity 
       (normalized by typical max for that source, or just pick GitHub as primary).
       For simplicity in this task: GitHub is primary if valid, else NPM.
    4. If neither, return unmapped status.
    
    Args:
        tag: The SO tag name.
        github_data: List of candidate GitHub repos from external_metrics.
        npm_data: List of candidate NPM packages from external_metrics.
        
    Returns:
        A mapping record dict.
    """
    mapping_record = {
        "tag": tag,
        "source": None,
        "repository_name": None,
        "metric_value": None,
        "metric_type": None,
        "unmapped": False
    }

    # Process GitHub
    github_best = None
    if github_data:
        github_best = select_best_candidate(
            github_data, 
            "github", 
            MIN_GITHUB_STARS
        )

    # Process NPM
    npm_best = None
    if npm_data:
        npm_best = select_best_candidate(
            npm_data, 
            "npm", 
            MIN_NPM_DOWNLOADS
        )

    # Decision Logic
    if github_best:
        mapping_record["source"] = "github"
        mapping_record["repository_name"] = github_best.get("full_name")
        mapping_record["metric_value"] = github_best.get("stars")
        mapping_record["metric_type"] = "stars"
    elif npm_best:
        mapping_record["source"] = "npm"
        mapping_record["repository_name"] = npm_best.get("name")
        mapping_record["metric_value"] = npm_best.get("downloads")
        mapping_record["metric_type"] = "weekly_downloads"
    else:
        mapping_record["unmapped"] = True
        logger.debug(f"Tag '{tag}' has no valid mapping candidates.")

    return mapping_record


def run_mapping_pipeline() -> Dict[str, Any]:
    """
    Executes the full mapping pipeline:
    1. Load external_metrics.json.
    2. Iterate over tags found in the metrics.
    3. Apply mapping logic.
    4. Write tag_mappings.json.
    5. Write unmapped_tags.log if necessary.
    
    Returns:
        Summary stats of the mapping process.
    """
    logger.info("Starting tag-to-repo mapping pipeline (T015)...")
    
    # Load data
    try:
        metrics_data = load_external_metrics()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load external metrics: {e}")
        # Per spec: If file missing/empty, create empty unmapped log and exit.
        # However, since we can't produce tag_mappings.json without input,
        # we create an empty output file to satisfy the "write output" requirement
        # while indicating failure via the log.
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump({"mappings": [], "metadata": {"status": "no_input"}}, f)
        
        UNMAPPED_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(UNMAPPED_LOG_FILE, 'w', encoding='utf-8') as f:
            pass # Empty log
            
        return {"status": "failed_no_input", "error": str(e)}

    github_metrics = metrics_data.get("github_metrics", [])
    npm_metrics = metrics_data.get("npm_metrics", [])

    # Index by tag for easier lookup
    # Structure expected: [{"tag": "python", "candidates": [...]}, ...]
    # The schema from T039 usually looks like:
    # { "tag": "python", "github": [...], "npm": [...] }
    # Let's handle the structure generically.
    
    all_tags = set()
    for item in github_metrics:
        if "tag" in item: all_tags.add(item["tag"])
    for item in npm_metrics:
        if "tag" in item: all_tags.add(item["tag"])

    mappings = []
    unmapped_tags = []

    logger.info(f"Processing {len(all_tags)} unique tags...")

    for tag in sorted(all_tags):
        # Find candidates for this tag
        g_candidates = [
            c for c in github_metrics 
            if c.get("tag") == tag
        ]
        n_candidates = [
            c for c in npm_metrics 
            if c.get("tag") == tag
        ]
        
        # Extract the 'candidates' list if the structure is nested
        # Expected structure from T039: {"tag": "...", "candidates": [...]}
        # Or flat list: {"tag": "...", "stars": 100, ...}
        # Let's assume the structure from T039 is a list of objects per tag.
        # If the object has a 'candidates' key, use that.
        
        g_list = []
        if g_candidates:
            first_g = g_candidates[0]
            if "candidates" in first_g:
                g_list = first_g["candidates"]
            else:
                # Assume the object itself is the candidate or part of a list
                g_list = g_candidates

        n_list = []
        if n_candidates:
            first_n = n_candidates[0]
            if "candidates" in first_n:
                n_list = first_n["candidates"]
            else:
                n_list = n_candidates

        result = map_tag_to_repos(tag, g_list, n_list)
        mappings.append(result)

        if result["unmapped"]:
            unmapped_tags.append(tag)

    # Write outputs
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "mappings": mappings,
        "metadata": {
            "total_tags": len(all_tags),
            "mapped_count": len(mappings) - len(unmapped_tags),
            "unmapped_count": len(unmapped_tags),
            "sources": ["github", "npm"],
            "thresholds": {
                "github_stars": MIN_GITHUB_STARS,
                "npm_downloads": MIN_NPM_DOWNLOADS
            }
        }
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Written {len(mappings)} mappings to {OUTPUT_FILE}")

    # Write unmapped log
    UNMAPPED_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(UNMAPPED_LOG_FILE, 'w', encoding='utf-8') as f:
        for tag in unmapped_tags:
            f.write(json.dumps({"tag": tag}) + "\n")
    
    if unmapped_tags:
        logger.warning(f"Found {len(unmapped_tags)} unmapped tags. Log written to {UNMAPPED_LOG_FILE}")
    else:
        logger.info("All tags successfully mapped.")

    return output_data["metadata"]


def main():
    """Entry point for the script."""
    try:
        result = run_mapping_pipeline()
        logger.info(f"Mapping pipeline completed. Status: {result}")
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        # Fail loudly as per constraints if a critical error occurs
        # (though the function handles missing input gracefully)
        raise


if __name__ == "__main__":
    main()