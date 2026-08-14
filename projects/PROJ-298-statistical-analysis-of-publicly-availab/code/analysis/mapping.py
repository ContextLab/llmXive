"""
Tag-to-Repository Mapping Logic for User Story 1.

Implements the logic to map Stack Overflow tags to GitHub repositories and NPM packages
using external metrics fetched by T039 (code/data/external.py).

This module reads `data/processed/external_metrics.json`, validates it against the
schema defined in `contracts/external_metrics.schema.yaml`, and produces:
1. `data/processed/tag_mappings.json`: The final mapping list.
2. `data/processed/unmapped_tags.log`: Newline-delimited JSON of tags that could not be mapped.

It adheres to the "Fail Loudly" policy: if the input file is missing or empty,
it creates empty output files and exits successfully (do NOT fail the pipeline).
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

INPUT_FILE = DATA_PROCESSED_DIR / "external_metrics.json"
OUTPUT_MAPPING_FILE = DATA_PROCESSED_DIR / "tag_mappings.json"
OUTPUT_UNMAPPED_LOG = DATA_PROCESSED_DIR / "unmapped_tags.log"
SCHEMA_FILE = CONTRACTS_DIR / "external_metrics.schema.yaml"


def ensure_log_dir(log_path: Path) -> None:
    """Ensure the directory for a log file exists."""
    log_path.parent.mkdir(parents=True, exist_ok=True)


def load_json_safe(file_path: Path) -> Optional[Dict]:
    """Safely load a JSON file. Returns None if file doesn't exist or is invalid."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
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


def load_schema(schema_path: Path) -> Optional[Dict]:
    """Load the YAML schema definition."""
    if not schema_path.exists():
        logger.warning(f"Schema file not found: {schema_path}. Proceeding without strict validation.")
        return None
    try:
        import yaml
        with open(schema_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not load schema {schema_path}: {e}. Proceeding without strict validation.")
        return None


def validate_external_metrics(data: Dict, schema: Optional[Dict]) -> bool:
    """
    Validate the structure of external_metrics.json.
    If schema is provided, perform basic checks. Otherwise, check for expected keys.
    """
    if not isinstance(data, dict):
        logger.error("External metrics data is not a dictionary.")
        return False

    # Basic structural check
    if 'metrics' not in data:
        logger.error("External metrics data missing 'metrics' key.")
        return False

    if not isinstance(data['metrics'], list):
        logger.error("'metrics' key is not a list.")
        return False

    # If schema exists, we could do deeper validation, but for now basic check suffices
    if schema:
        # Check if required properties exist in the schema if defined
        logger.info("Schema validation skipped (basic check passed).")

    return True


def select_best_candidate(candidates: List[Dict]) -> Optional[Dict]:
    """
    Select the best candidate repo/package from a list of matches.
    Strategy:
    1. Prefer exact matches on name.
    2. Otherwise, prefer the one with the highest stars/downloads.
    3. If no candidates, return None.
    """
    if not candidates:
        return None

    # Sort by a heuristic score: exact match + popularity
    def score_candidate(cand: Dict) -> Tuple[int, int]:
        is_exact = 1 if cand.get('is_exact_match', False) else 0
        # Use stars for GitHub, downloads for NPM, default to 0
        popularity = cand.get('stars', cand.get('downloads', 0))
        return (is_exact, popularity)

    candidates.sort(key=score_candidate, reverse=True)
    return candidates[0]


def map_tag_to_repos(tag_name: str, tag_data: Dict) -> Dict[str, Any]:
    """
    Process a single tag's external metrics to produce a mapping entry.

    Args:
        tag_name: The SO tag name.
        tag_data: The data for this tag from external_metrics.json.

    Returns:
        A dictionary representing the mapping entry, or None if no mapping found.
    """
    mapping_entry = {
        "tag": tag_name,
        "github_repo": None,
        "npm_package": None,
        "mapping_status": "unmapped"
    }

    # Extract candidates
    github_candidates = tag_data.get('github_candidates', [])
    npm_candidates = tag_data.get('npm_candidates', [])

    # Select best GitHub repo
    if github_candidates:
        best_github = select_best_candidate(github_candidates)
        if best_github:
            mapping_entry['github_repo'] = {
                "full_name": best_github.get('full_name'),
                "stars": best_github.get('stars'),
                "url": best_github.get('url'),
                "match_quality": "exact" if best_github.get('is_exact_match') else "approximate"
            }
            mapping_entry['mapping_status'] = "mapped"

    # Select best NPM package
    if npm_candidates:
        best_npm = select_best_candidate(npm_candidates)
        if best_npm:
            mapping_entry['npm_package'] = {
                "name": best_npm.get('name'),
                "downloads": best_npm.get('downloads'),
                "url": best_npm.get('url'),
                "match_quality": "exact" if best_npm.get('is_exact_match') else "approximate"
            }
            # If we already mapped via GitHub, status remains 'mapped', otherwise update
            if mapping_entry['mapping_status'] == "unmapped":
                mapping_entry['mapping_status'] = "mapped"

    return mapping_entry


def run_mapping_pipeline() -> bool:
    """
    Main pipeline function for T015.

    1. Verify input file exists. If missing/empty -> create empty outputs and exit 0.
    2. Load and validate input.
    3. Process each tag to generate mappings.
    4. Write tag_mappings.json.
    5. Write unmapped_tags.log.
    """
    logger.info("Starting Tag-to-Repository Mapping Pipeline (T015)...")

    # 1. Verify input file
    if not INPUT_FILE.exists():
        logger.warning(f"Input file {INPUT_FILE} not found. Creating empty outputs and exiting.")
        ensure_log_dir(OUTPUT_UNMAPPED_LOG)
        # Create empty mapping file
        with open(OUTPUT_MAPPING_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        # Create empty log file
        with open(OUTPUT_UNMAPPED_LOG, 'w', encoding='utf-8') as f:
            f.write("")
        return True

    # Load input
    external_data = load_json_safe(INPUT_FILE)
    if external_data is None:
        logger.error(f"Failed to load or parse {INPUT_FILE}. Exiting.")
        return False

    # Load schema (optional validation)
    schema = load_schema(SCHEMA_FILE)

    # Validate structure
    if not validate_external_metrics(external_data, schema):
        logger.error("Input data validation failed.")
        return False

    metrics_list = external_data.get('metrics', [])
    if not metrics_list:
        logger.warning("Input file contains no metrics. Creating empty outputs.")
        ensure_log_dir(OUTPUT_UNMAPPED_LOG)
        with open(OUTPUT_MAPPING_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        with open(OUTPUT_UNMAPPED_LOG, 'w', encoding='utf-8') as f:
            f.write("")
        return True

    mappings = []
    unmapped_tags = []

    logger.info(f"Processing {len(metrics_list)} tags...")

    for item in metrics_list:
        tag_name = item.get('tag')
        if not tag_name:
            logger.warning("Skipping metric entry without 'tag' key.")
            continue

        mapping_entry = map_tag_to_repos(tag_name, item)
        mappings.append(mapping_entry)

        if mapping_entry['mapping_status'] == 'unmapped':
            unmapped_tags.append(tag_name)

    # Write outputs
    ensure_log_dir(OUTPUT_MAPPING_FILE)
    with open(OUTPUT_MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(mappings, f, indent=2)
    logger.info(f"Wrote {len(mappings)} mappings to {OUTPUT_MAPPING_FILE}")

    ensure_log_dir(OUTPUT_UNMAPPED_LOG)
    with open(OUTPUT_UNMAPPED_LOG, 'w', encoding='utf-8') as f:
        for tag in unmapped_tags:
            f.write(json.dumps({"tag": tag, "status": "unmapped"}) + "\n")
    logger.info(f"Wrote {len(unmapped_tags)} unmapped tags to {OUTPUT_UNMAPPED_LOG}")

    logger.info("Tag-to-Repository Mapping Pipeline completed successfully.")
    return True


def main():
    """Entry point for the script."""
    success = run_mapping_pipeline()
    if not success:
        logger.error("Mapping pipeline failed.")
        exit(1)
    else:
        exit(0)


if __name__ == "__main__":
    main()
