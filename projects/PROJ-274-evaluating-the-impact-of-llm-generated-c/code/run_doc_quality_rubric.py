"""
Task T021f: Documentation Quality Rubric Scoring Runner.

This script executes the documentation quality rubric on candidate repositories
to generate a quantitative "Human Doc Quality Score".

Output: data/raw/doc_quality_scores.json
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from validation import run_rubric_on_candidates, evaluate_repository_rubric

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_candidate_repos():
    """
    Load candidate repositories from data/raw/repo_selection_rubric.json.
    This file is produced by T021b.
    """
    input_path = project_root / "data" / "raw" / "repo_selection_rubric.json"
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T021b (Repository Selection) has completed successfully."
        )
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Expecting a list of repos or a dict with a 'repos' key
    if isinstance(data, dict) and 'repos' in data:
        return data['repos']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected format in {input_path}. Expected list or dict with 'repos' key.")

def main():
    """
    Main entry point for T021f.
    1. Loads candidate repos from T021b output.
    2. Evaluates documentation quality for each.
    3. Writes results to data/raw/doc_quality_scores.json.
    """
    logger.info("Starting Documentation Quality Rubric Scoring (T021f)...")
    
    try:
        repos = load_candidate_repos()
        logger.info(f"Loaded {len(repos)} candidate repositories.")
    except Exception as e:
        logger.error(f"Failed to load candidate repos: {e}")
        sys.exit(1)

    scores = []

    for repo in repos:
        repo_name = repo.get('name') or repo.get('repo_name') or str(repo)
        repo_path = repo.get('path') or repo.get('local_path')
        
        if not repo_path or not os.path.isdir(repo_path):
            logger.warning(f"Skipping {repo_name}: Path '{repo_path}' not found or invalid.")
            # We still record it as 0 or skip? The task says "Calculate ... based on presence".
            # If we can't read it, we can't score. We'll record a failure state or skip.
            # Let's skip to avoid noise, or log a 0. Let's log a 0 with a note.
            scores.append({
                "repo_name": repo_name,
                "doc_quality_score": 0,
                "status": "skipped",
                "reason": "Repository path not found"
            })
            continue

        try:
            logger.info(f"Evaluating documentation for: {repo_name} at {repo_path}")
            score_data = evaluate_repository_rubric(repo_path)
            
            # score_data should contain the binary breakdown and total
            scores.append({
                "repo_name": repo_name,
                "doc_quality_score": score_data['total_score'],
                "has_setup": score_data.get('has_setup', False),
                "has_api": score_data.get('has_api', False),
                "has_architecture": score_data.get('has_architecture', False),
                "status": "success"
            })
            logger.info(f"  -> Score: {score_data['total_score']}/3")
            
        except Exception as e:
            logger.error(f"Error evaluating {repo_name}: {e}")
            scores.append({
                "repo_name": repo_name,
                "doc_quality_score": 0,
                "status": "error",
                "reason": str(e)
            })

    # Define output path
    output_dir = project_root / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "doc_quality_scores.json"

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(scores, f, indent=2)
        logger.info(f"Successfully wrote doc quality scores to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        sys.exit(1)

    logger.info("T021f completed.")

if __name__ == "__main__":
    main()
