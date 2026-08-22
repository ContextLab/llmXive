import os
import sys
import json
import logging
from pathlib import Path
from validation import evaluate_repository_rubric, load_json_file, save_json_file

# Ensure log directory exists
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "doc_quality.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_candidate_repos(filepath: str = "data/raw/candidate_repos.json") -> list:
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return []

def main():
    """
    Run doc quality rubric evaluation and save to data/raw/doc_quality_scores.json.
    """
    candidates = load_candidate_repos()
    if not candidates:
        logger.warning("No candidate repos found. Creating placeholder scores.")
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        with open("data/raw/doc_quality_scores.json", 'w') as f:
            json.dump([], f)
        return

    scores = []
    for repo in candidates:
        score = evaluate_repository_rubric(repo)
        scores.append(score)
    
    with open("data/raw/doc_quality_scores.json", 'w') as f:
        json.dump(scores, f, indent=2)
    
    logger.info(f"Doc quality scores saved for {len(scores)} repos.")

if __name__ == "__main__":
    main()
