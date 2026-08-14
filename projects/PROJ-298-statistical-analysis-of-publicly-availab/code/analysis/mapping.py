"""
Tag-to-Repository Mapping Logic for User Story 1.

This module implements the logic to map Stack Overflow tags to corresponding
GitHub repositories and NPM packages using raw data fetched by T039.

It reads:
  - data/processed/external_metrics.json (raw metrics and candidates from T039)
  - data/processed/top_50_tags.json (list of top tags)
  - contracts/external_metrics.schema.yaml (schema for validation)

It writes:
  - data/processed/tag_mappings.json (final mapping list)
  - data/processed/unmapped_tags.log (newline-delimited JSON for unmapped tags)
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

# Project root path (assuming code/analysis is the current working context or relative)
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

# Input/Output paths
EXTERNAL_METRICS_PATH = DATA_PROCESSED_DIR / "external_metrics.json"
TOP_TAGS_PATH = DATA_PROCESSED_DIR / "top_50_tags.json"
SCHEMA_PATH = CONTRACTS_DIR / "external_metrics.schema.yaml"
MAPPINGS_OUTPUT_PATH = DATA_PROCESSED_DIR / "tag_mappings.json"
UNMAPPED_LOG_PATH = DATA_PROCESSED_DIR / "unmapped_tags.log"


def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if it doesn't exist or is invalid."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return None


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the schema definition."""
    # For YAML schema, we assume the file exists as per T002 dependencies
    # If yaml is not installed, we might need to handle that, but T002 includes pyyaml
    try:
        import yaml
        with open(schema_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except ImportError:
        logger.warning("PyYAML not installed. Attempting to load schema as JSON if possible, or skipping validation.")
        # Fallback: try reading as JSON if YAML fails due to import
        return load_json_safe(schema_path) or {}
    except Exception as e:
        logger.warning(f"Could not load schema {schema_path}: {e}. Proceeding without strict schema validation.")
        return {}


def load_external_metrics() -> Optional[Dict[str, Any]]:
    """Load the external metrics data fetched by T039."""
    return load_json_safe(EXTERNAL_METRICS_PATH)


def load_top_tags() -> List[str]:
    """Load the list of top 50 tags."""
    data = load_json_safe(TOP_TAGS_PATH)
    if data is None:
        return []
    # Handle different possible structures: list of strings or list of dicts
    if isinstance(data, list):
        if all(isinstance(item, str) for item in data):
            return data
        elif all(isinstance(item, dict) and 'tag' in item for item in data):
            return [item['tag'] for item in data]
    elif isinstance(data, dict) and 'tags' in data:
        return data['tags']
    return []


def select_best_candidate(tag: str, candidates: List[Dict[str, Any]], source: str) -> Optional[Dict[str, Any]]:
    """
    Select the best candidate repository/package for a given tag.

    Criteria (simplified for robustness):
    1. Exact match in name or keywords.
    2. Highest star count (GitHub) or download count (NPM).
    3. If no candidates match criteria, return None.
    """
    if not candidates:
        return None

    # Filter for exact name match first
    exact_matches = [
        c for c in candidates
        if c.get('name', '').lower() == tag.lower()
    ]

    if exact_matches:
        # Pick the one with highest popularity metric
        if source == 'github':
            return max(exact_matches, key=lambda x: x.get('stargazers_count', 0))
        else: # npm
            return max(exact_matches, key=lambda x: x.get('downloads', 0))

    # Fallback: pick the most popular among all candidates
    if source == 'github':
        return max(candidates, key=lambda x: x.get('stargazers_count', 0))
    else:
        return max(candidates, key=lambda x: x.get('downloads', 0))


def map_tag_to_repos(tag: str, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map a single tag to its best GitHub repo and NPM package.

    Returns a dict:
    {
      "tag": "string",
      "github": {"name": "...", "stars": ..., "url": "..."} or None,
      "npm": {"name": "...", "downloads": ..., "url": "..."} or None,
      "mapped": True/False
    }
    """
    # Check if we have data for this tag
    tag_data = metrics_data.get('metrics', {}).get(tag, {})
    if not tag_data:
        return {"tag": tag, "github": None, "npm": None, "mapped": False}

    github_candidates = tag_data.get('github_candidates', [])
    npm_candidates = tag_data.get('npm_candidates', [])

    best_github = select_best_candidate(tag, github_candidates, 'github')
    best_npm = select_best_candidate(tag, npm_candidates, 'npm')

    result = {
        "tag": tag,
        "github": None,
        "npm": None,
        "mapped": False
    }

    if best_github:
        result["github"] = {
            "name": best_github.get('name'),
            "stargazers_count": best_github.get('stargazers_count'),
            "html_url": best_github.get('html_url')
        }
        result["mapped"] = True

    if best_npm:
        result["npm"] = {
            "name": best_npm.get('name'),
            "downloads": best_npm.get('downloads'),
            "url": best_npm.get('url')
        }
        result["mapped"] = True

    return result


def run_mapping_pipeline() -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Run the full mapping pipeline.

    Returns:
      (mappings_list, unmapped_tags_list)
    """
    # 1. Verify inputs exist
    if not EXTERNAL_METRICS_PATH.exists():
        logger.error(f"External metrics file not found: {EXTERNAL_METRICS_PATH}")
        # Per spec: create empty unmapped log and exit successfully if T039 failed
        UNMAPPED_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(UNMAPPED_LOG_PATH, 'w', encoding='utf-8') as f:
            pass # Empty file
        return [], []

    metrics_data = load_external_metrics()
    if metrics_data is None:
        logger.error("Failed to load external metrics data.")
        UNMAPPED_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(UNMAPPED_LOG_PATH, 'w', encoding='utf-8') as f:
            pass
        return [], []

    top_tags = load_top_tags()
    if not top_tags:
        logger.warning("No top tags found. Returning empty mappings.")
        return [], []

    mappings = []
    unmapped_tags = []

    for tag in top_tags:
        mapping_result = map_tag_to_repos(tag, metrics_data)
        mappings.append(mapping_result)

        # Check if mapped at least one source
        if not mapping_result["mapped"]:
            unmapped_tags.append(tag)
            logger.info(f"Tag '{tag}' could not be mapped to any repo/package.")

    return mappings, unmapped_tags


def save_mappings(mappings: List[Dict[str, Any]], unmapped_tags: List[str]) -> None:
    """Save the final mappings and unmapped tags log."""
    # Ensure output directory exists
    MAPPINGS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Save mappings
    with open(MAPPINGS_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(mappings, f, indent=2)
    logger.info(f"Saved tag mappings to {MAPPINGS_OUTPUT_PATH}")

    # Save unmapped tags log (newline-delimited JSON)
    UNMAPPED_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(UNMAPPED_LOG_PATH, 'w', encoding='utf-8') as f:
        for tag in unmapped_tags:
            f.write(json.dumps({"tag": tag}) + '\n')
    logger.info(f"Saved unmapped tags log to {UNMAPPED_LOG_PATH}")


def main():
    """Main entry point for T015."""
    logger.info("Starting Tag-to-Repository Mapping (T015)...")

    # Run the pipeline
    mappings, unmapped_tags = run_mapping_pipeline()

    # Save results
    save_mappings(mappings, unmapped_tags)

    logger.info("Tag-to-Repository Mapping (T015) completed successfully.")
    return 0


if __name__ == "__main__":
    exit(main())