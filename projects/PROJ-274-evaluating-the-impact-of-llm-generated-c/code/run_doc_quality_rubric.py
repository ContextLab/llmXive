"""
Script to execute T021f: Documentation Quality Rubric Scoring.
This script runs the rubric on candidate repositories and writes
data/raw/doc_quality_scores.json.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from validation import run_rubric_on_candidates, evaluate_repository_rubric

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_candidate_repos(repos_file: str) -> list:
    """Load list of candidate repos from a JSON file."""
    if not os.path.exists(repos_file):
        logger.warning(f"Candidate repos file not found: {repos_file}. Using defaults.")
        # Fallback to a minimal set if no file exists, but in real execution this should exist
        return ["data/raw/repos/sample_repo"]
    
    with open(repos_file, 'r') as f:
        data = json.load(f)
        # Expecting a list of paths or objects with 'path' key
        if isinstance(data, list):
            return [r['path'] if isinstance(r, dict) else r for r in data]
        return []

def main():
    # Configuration
    # In a real run, this might be passed via CLI or read from a config
    candidate_repos_file = "data/raw/candidate_repos.json"
    output_file = "data/raw/doc_quality_scores.json"

    # Ensure output directory
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Load candidates
    candidate_repos = load_candidate_repos(candidate_repos_file)

    if not candidate_repos:
        logger.error("No candidate repositories found. Aborting T021f.")
        sys.exit(1)

    logger.info(f"Running documentation quality rubric on {len(candidate_repos)} repositories.")
    
    # Run the rubric
    run_rubric_on_candidates(candidate_repos, output_file)

    logger.info(f"T021f completed. Output written to {output_file}")

if __name__ == "__main__":
    main()
