import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from validation import load_json_file, save_json_file

logger = logging.getLogger(__name__)

def load_covariate_sources(rubric_path: str, cc_path: str, loc_path: str, doc_quality_path: str) -> Dict[str, Any]:
    """
    Aggregates data from the four prerequisite JSON files.
    Raises FileNotFoundError if any source is missing.
    """
    rubric_data = load_json_file(rubric_path)
    cc_data = load_json_file(cc_path)
    loc_data = load_json_file(loc_path)
    doc_quality_data = load_json_file(doc_quality_path)

    if not rubric_data or 'selected_repos' not in rubric_data:
        raise ValueError(f"Invalid rubric data in {rubric_path}: missing 'selected_repos'")

    selected_repos = rubric_data['selected_repos']
    covariates = {}

    for repo_entry in selected_repos:
        # Handle both string URL and dict with 'url' key
        if isinstance(repo_entry, dict):
            url = repo_entry.get('url')
        else:
            url = repo_entry

        if not url:
            continue

        covariates[url] = {
            'selected': True,
            'cc': cc_data.get(url, {}).get('cc', None),
            'files': cc_data.get(url, {}).get('files', None),
            'loc': loc_data.get(url, {}).get('loc', None),
            'sloc': loc_data.get(url, {}).get('sloc', None),
            'doc_quality_score': doc_quality_data.get(url, {}).get('score', None),
            'doc_sections_present': doc_quality_data.get(url, {}).get('sections', [])
        }

    return covariates

def main():
    """
    T021e Implementation: Generate repo_covariates.json.
    Reads from T021d output and T021a/b/c outputs.
    Writes to data/raw/repo_covariates.json.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Define paths relative to project root
    root = Path(__file__).resolve().parent.parent
    data_raw_dir = root / 'data' / 'raw'
    data_raw_dir.mkdir(parents=True, exist_ok=True)

    rubric_path = data_raw_dir / 'repo_selection_rubric.json'
    cc_path = data_raw_dir / 'repo_cc_raw.json'
    loc_path = data_raw_dir / 'repo_loc_raw.json'
    doc_quality_path = data_raw_dir / 'doc_quality_scores.json'
    output_path = data_raw_dir / 'repo_covariates.json'

    # Verify inputs exist (fail loudly if missing, per constraints)
    missing_inputs = []
    if not rubric_path.exists(): missing_inputs.append(str(rubric_path))
    if not cc_path.exists(): missing_inputs.append(str(cc_path))
    if not loc_path.exists(): missing_inputs.append(str(loc_path))
    if not doc_quality_path.exists(): missing_inputs.append(str(doc_quality_path))

    if missing_inputs:
        logger.error(f"Missing required input files for covariate aggregation: {missing_inputs}")
        sys.exit(1)

    try:
        logger.info("Loading source data files...")
        covariates = load_covariate_sources(
            str(rubric_path),
            str(cc_path),
            str(loc_path),
            str(doc_quality_path)
        )

        logger.info(f"Aggregated covariates for {len(covariates)} repositories.")

        logger.info(f"Writing covariates to {output_path}")
        save_json_file(output_path, covariates)

        logger.info("T021e: repo_covariates.json generated successfully.")

    except Exception as e:
        logger.error(f"Failed to generate covariates: {e}")
        raise

if __name__ == '__main__':
    main()