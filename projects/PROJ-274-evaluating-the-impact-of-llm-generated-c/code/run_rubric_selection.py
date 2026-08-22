"""
T021d: Filter repositories based on documentation quality.

Reads data/raw/doc_quality_scores.json, applies the minimum rubric score 
defined in FR-009 (score >= 2), and writes the filtered list to 
data/raw/repo_selection_rubric_intermediate.json.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Configure logging to avoid FileNotFoundError by ensuring directory exists
log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "rubric_selection.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("rubric_selection")

# FR-009 Minimum Rubric Score Threshold
# The rubric sums binary indicators for Setup, API, and Architecture.
# A score of 2 or higher indicates sufficient documentation quality.
MIN_RUBRIC_SCORE = 2

def load_json_file(filepath: str) -> dict:
    """Load a JSON file and return its contents."""
    logger.info(f"Loading JSON file: {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(filepath: str, data: dict) -> None:
    """Save data to a JSON file."""
    logger.info(f"Saving JSON file: {filepath}")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Successfully saved {len(data.get('repositories', []))} repositories to {filepath}")

def filter_repos_by_rubric(input_path: str, output_path: str) -> dict:
    """
    Filter repositories based on documentation quality score.
    
    Args:
        input_path: Path to data/raw/doc_quality_scores.json
        output_path: Path to data/raw/repo_selection_rubric_intermediate.json
        
    Returns:
        The filtered dataset dictionary.
    """
    try:
        data = load_json_file(input_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load input data: {e}")
        raise

    repositories = data.get("repositories", [])
    if not repositories:
        logger.warning("No repositories found in input file.")
        # Still write empty result to maintain pipeline contract
        result = {
            "criteria": f"doc_quality_score >= {MIN_RUBRIC_SCORE}",
            "count": 0,
            "repositories": []
        }
        save_json_file(output_path, result)
        return result

    filtered_repos = []
    excluded_repos = []

    for repo in repositories:
        repo_id = repo.get("repo_id", repo.get("name", "unknown"))
        score = repo.get("doc_quality_score", 0)
        
        if score >= MIN_RUBRIC_SCORE:
            filtered_repos.append(repo)
            logger.debug(f"Repository '{repo_id}' included (score: {score})")
        else:
            excluded_repos.append({
                "repo_id": repo_id,
                "score": score,
                "reason": f"Score {score} < {MIN_RUBRIC_SCORE}"
            })
            logger.info(f"Repository '{repo_id}' excluded (score: {score})")

    result = {
        "criteria": f"doc_quality_score >= {MIN_RUBRIC_SCORE}",
        "total_input": len(repositories),
        "included_count": len(filtered_repos),
        "excluded_count": len(excluded_repos),
        "repositories": filtered_repos,
        "excluded_details": excluded_repos
    }

    save_json_file(output_path, result)
    return result

def main():
    """Main entry point for the script."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parents[1]
    input_file = project_root / "data" / "raw" / "doc_quality_scores.json"
    output_file = project_root / "data" / "raw" / "repo_selection_rubric_intermediate.json"

    # Ensure input exists (fail loudly if missing, per constraints)
    if not input_file.exists():
        logger.error(f"Input file missing: {input_file}")
        logger.error("T021c (doc_quality_scores.json generation) must run before T021d.")
        sys.exit(1)

    logger.info(f"Starting repository filtering based on rubric score (min: {MIN_RUBRIC_SCORE})")
    logger.info(f"Input: {input_file}")
    logger.info(f"Output: {output_file}")

    try:
        result = filter_repos_by_rubric(str(input_file), str(output_file))
        logger.info("Filtering complete.")
        logger.info(f"Included: {result['included_count']}, Excluded: {result['excluded_count']}")
    except Exception as e:
        logger.error(f"Filtering failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()