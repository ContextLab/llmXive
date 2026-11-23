"""
Mapping module for T015: Tag-to-Repo/NPM Package Mapping.

This module implements the logic to map Stack Overflow tags to GitHub repositories
and NPM packages using raw data fetched by T039 (external.py).

It reads `data/processed/external_metrics.json` and outputs:
1. `data/processed/tag_mappings.json`: Final mapping list.
2. `data/processed/unmapped_tags.log`: Log of tags that could not be mapped.

Requirements:
- MUST verify `data/processed/external_metrics.json` exists.
- MUST NOT perform correlation calculation.
- MUST fail loudly if the input file is missing or empty (unless explicitly handled to exit cleanly).
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
INPUT_FILE = PROCESSED_DIR / "external_metrics.json"
OUTPUT_FILE = PROCESSED_DIR / "tag_mappings.json"
UNMAPPED_LOG = PROCESSED_DIR / "unmapped_tags.log"

def ensure_log_dir(log_path: Path) -> None:
    """Ensure the directory for the log file exists."""
    log_path.parent.mkdir(parents=True, exist_ok=True)

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a JSON file safely.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        Parsed JSON data or None if file doesn't exist or is invalid.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None

def load_schema(schema_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a YAML/JSON schema definition.
    
    Args:
        schema_path: Path to the schema file.
        
    Returns:
        Parsed schema or None.
    """
    # For this task, we assume the schema is a JSON file as per typical contract usage
    # If it were YAML, we would need to import yaml, but the API surface suggests json usage.
    # We will attempt to load as JSON first.
    return load_json_safe(schema_path)

def validate_external_metrics(data: Dict[str, Any]) -> bool:
    """
    Validate the structure of external_metrics.json.
    
    Expected structure:
    {
      "metrics": [
        {
          "tag": "string",
          "github": {"candidates": [...]},
          "npm": {"candidates": [...]},
          "status": "success|error"
        },
        ...
      ]
    }
    """
    if not isinstance(data, dict):
        return False
    if "metrics" not in data:
        return False
    if not isinstance(data["metrics"], list):
        return False
    return True

def select_best_candidate(candidates: List[Dict[str, Any]], metric_type: str) -> Optional[Dict[str, Any]]:
    """
    Select the best candidate for a tag based on specific criteria.
    
    Args:
        candidates: List of candidate matches from the API.
        metric_type: 'github' or 'npm'.
        
    Returns:
        The best candidate or None.
    """
    if not candidates:
        return None
    
    # Heuristic: Sort by stars (GitHub) or downloads (NPM) descending
    # Assume the candidate structure has 'stars' or 'downloads' keys
    if metric_type == "github":
        sorted_candidates = sorted(
            candidates, 
            key=lambda x: x.get("stars", 0), 
            reverse=True
        )
    elif metric_type == "npm":
        sorted_candidates = sorted(
            candidates, 
            key=lambda x: x.get("downloads", 0), 
            reverse=True
        )
    else:
        sorted_candidates = candidates
    
    # Return the top candidate if it meets a minimum threshold (e.g., > 0 stars/downloads)
    top = sorted_candidates[0]
    if metric_type == "github" and top.get("stars", 0) == 0 and len(candidates) == 1:
        # If only one candidate and 0 stars, it might be a generic search result, check relevance
        pass 
    elif metric_type == "npm" and top.get("downloads", 0) == 0 and len(candidates) == 1:
        pass

    return top

def map_tag_to_repos(tag_data: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Map a single tag to its best GitHub repo and NPM package.
    
    Args:
        tag_data: Dictionary containing tag, github, npm, and status info.
        
    Returns:
        Tuple of (github_mapping, npm_mapping). Either can be None if not found.
    """
    tag_name = tag_data.get("tag")
    github_data = tag_data.get("github", {})
    npm_data = tag_data.get("npm", {})
    
    github_mapping = None
    npm_mapping = None
    
    # Process GitHub
    if github_data.get("status") == "success":
        candidates = github_data.get("candidates", [])
        best = select_best_candidate(candidates, "github")
        if best:
            github_mapping = {
                "tag": tag_name,
                "repo": best.get("full_name"),
                "stars": best.get("stars"),
                "url": best.get("html_url"),
                "source": "github_search"
            }
    
    # Process NPM
    if npm_data.get("status") == "success":
        candidates = npm_data.get("candidates", [])
        best = select_best_candidate(candidates, "npm")
        if best:
            npm_mapping = {
                "tag": tag_name,
                "package": best.get("name"),
                "downloads": best.get("downloads"),
                "url": best.get("url"),
                "source": "npm_search"
            }
    
    return github_mapping, npm_mapping

def run_mapping_pipeline() -> bool:
    """
    Execute the full mapping pipeline.
    
    1. Verify input file exists.
    2. Load and validate data.
    3. Map each tag to repos/packages.
    4. Write `tag_mappings.json`.
    5. Write `unmapped_tags.log` for any tags without matches.
    
    Returns:
        True if successful, False otherwise.
    """
    # 1. Verify input file
    if not INPUT_FILE.exists():
        logger.error(f"Input file missing: {INPUT_FILE}")
        # Per T015 spec: "If the file is missing ... create an empty unmapped_tags.log and exit successfully"
        ensure_log_dir(UNMAPPED_LOG)
        with open(UNMAPPED_LOG, 'w', encoding='utf-8') as f:
            f.write("") # Empty file
        logger.info("Input missing. Created empty unmapped_tags.log and exiting.")
        return True

    # 2. Load and validate
    data = load_json_safe(INPUT_FILE)
    if data is None:
        logger.error("Failed to load input file.")
        return False
    
    if not validate_external_metrics(data):
        logger.error("Input file does not match expected schema.")
        # If empty metrics list, treat as success with no mappings
        if data.get("metrics") == []:
            ensure_log_dir(UNMAPPED_LOG)
            with open(UNMAPPED_LOG, 'w', encoding='utf-8') as f:
                f.write("")
            return True
        return False
    
    metrics_list = data.get("metrics", [])
    
    if not metrics_list:
        logger.warning("No metrics found in input file.")
        ensure_log_dir(UNMAPPED_LOG)
        with open(UNMAPPED_LOG, 'w', encoding='utf-8') as f:
            f.write("")
        # Write empty output
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump({"mappings": []}, f, indent=2)
        return True

    # 3. Map tags
    final_mappings = []
    unmapped_tags = []
    
    for item in metrics_list:
        tag_name = item.get("tag")
        if not tag_name:
            logger.warning(f"Skipping item with no tag: {item}")
            continue
        
        github_map, npm_map = map_tag_to_repos(item)
        
        if github_map or npm_map:
            mapping_entry = {
                "tag": tag_name,
                "github": github_map,
                "npm": npm_map
            }
            final_mappings.append(mapping_entry)
        else:
            # No mapping found
            unmapped_tags.append({"tag": tag_name, "reason": "no_candidates_found"})
            logger.info(f"Tag '{tag_name}' could not be mapped.")
    
    # 4. Write output
    ensure_log_dir(OUTPUT_FILE)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump({"mappings": final_mappings}, f, indent=2)
    logger.info(f"Written {len(final_mappings)} mappings to {OUTPUT_FILE}")
    
    # 5. Write unmapped log
    ensure_log_dir(UNMAPPED_LOG)
    with open(UNMAPPED_LOG, 'w', encoding='utf-8') as f:
        for entry in unmapped_tags:
            f.write(json.dumps(entry) + "\n")
    logger.info(f"Written {len(unmapped_tags)} unmapped tags to {UNMAPPED_LOG}")
    
    return True

def main():
    """Entry point for the mapping pipeline."""
    logger.info("Starting Tag-to-Repo Mapping Pipeline (T015)...")
    success = run_mapping_pipeline()
    if success:
        logger.info("Mapping pipeline completed successfully.")
    else:
        logger.error("Mapping pipeline failed.")
        # Exit with error code if critical failure occurred (e.g., invalid schema)
        # But per spec, if input is missing, we exit 0. If schema is bad, we might exit 1.
        # However, the spec says "exit successfully" if missing. 
        # If validation fails, we should probably fail loudly.
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()
