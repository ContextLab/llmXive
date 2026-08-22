import json
import os
import sys
import logging
from pathlib import Path

from validation import calculate_cyclomatic_complexity, load_json_file, save_json_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_candidate_repos(path: str) -> list:
    """Load candidate repository paths from a JSON file."""
    if not os.path.exists(path):
        logger.error(f"Candidate repos file not found: {path}")
        return []
    return load_json_file(path)

def collect_cc_metrics(repos: list, output_path: str) -> None:
    """
    Run radon cc -a -s for each candidate repository and save results.
    Output: data/raw/repo_cc_raw.json
    """
    results = []
    for repo_path in repos:
        if not os.path.isdir(repo_path):
            logger.warning(f"Skipping non-directory: {repo_path}")
            continue
        
        logger.info(f"Calculating CC for: {repo_path}")
        cc_value = calculate_cyclomatic_complexity(repo_path)
        
        results.append({
            "repo_path": repo_path,
            "cyclomatic_complexity": cc_value
        })

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Save results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"CC metrics saved to {output_path}")

def main():
    """Main entry point for CC collection."""
    # Default paths relative to project root
    # Assuming this script is run from the project root
    candidate_file = "data/raw/candidate_repos.json"
    output_file = "data/raw/repo_cc_raw.json"

    # Allow overrides via command line
    if len(sys.argv) > 1:
        candidate_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    logger.info(f"Loading candidates from {candidate_file}")
    repos = load_candidate_repos(candidate_file)
    
    if not repos:
        logger.error("No candidate repositories found. Exiting.")
        sys.exit(1)

    logger.info(f"Collecting CC for {len(repos)} repositories...")
    collect_cc_metrics(repos, output_file)
    logger.info("CC collection complete.")

if __name__ == "__main__":
    main()