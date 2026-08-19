"""
Runner script for Task T021f: Documentation Quality Rubric Scoring.

This script loads the candidate repositories list from data/raw/candidate_repos.json
and calculates a quantitative "Human Doc Quality Score" for each based on the
presence of Setup, API, and Architecture sections in their documentation.

Output: data/raw/doc_quality_scores.json
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from validation import evaluate_repository_rubric, load_json_file, save_json_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_candidate_repos(input_path: str) -> list:
    """Load candidate repositories from the JSON file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    data = load_json_file(input_path)
    return data.get("candidates", [])

def main():
    input_path = "data/raw/candidate_repos.json"
    output_path = "data/raw/doc_quality_scores.json"

    logger.info(f"Loading candidate repositories from {input_path}")
    try:
        candidates = load_candidate_repos(input_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load candidates: {e}")
        sys.exit(1)

    if not candidates:
        logger.warning("No candidate repositories found. Exiting.")
        sys.exit(0)

    logger.info(f"Found {len(candidates)} candidate repositories.")

    results = []
    for repo_path in candidates:
        logger.info(f"Evaluating documentation quality for: {repo_path}")
        try:
            score = evaluate_repository_rubric(repo_path)
            results.append({
                "repo_path": repo_path,
                "doc_quality_score": score
            })
            logger.info(f"  -> Score: {score}/3")
        except Exception as e:
            logger.error(f"  -> Error evaluating {repo_path}: {e}")
            # Record as 0 or skip? Let's record as 0 to maintain list integrity
            results.append({
                "repo_path": repo_path,
                "doc_quality_score": 0,
                "error": str(e)
            })

    output_data = {
        "scores": results,
        "total_repos": len(candidates),
        "completed": len([r for r in results if "error" not in r]),
        "failed": len([r for r in results if "error" in r])
    }

    logger.info(f"Saving results to {output_path}")
    save_json_file(output_path, output_data)
    logger.info("Task T021f completed successfully.")

if __name__ == "__main__":
    main()
