import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any
from statistics import median

logger = logging.getLogger(__name__)

def load_repos(filepath: str) -> List[Dict[str, Any]]:
    """Load repository metadata."""
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_medians(repos: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate median stars and contributors."""
    if not repos:
        return {"median_stars": 0, "median_contributors": 0}
    
    stars = [r['stars'] for r in repos]
    # Contributors is not in repos.json yet, defaulting to 0 or 1 for now if missing
    contributors = [r.get('contributors', 1) for r in repos]
    
    return {
        "median_stars": median(stars),
        "median_contributors": median(contributors)
    }

def main():
    """Main entry point for repo stats analysis."""
    logging.basicConfig(level=logging.INFO)
    
    repos = load_repos("data/raw/repos.json")
    stats = calculate_medians(repos)
    
    logger.info(f"Median Stars: {stats['median_stars']}")
    logger.info(f"Median Contributors: {stats['median_contributors']}")

if __name__ == "__main__":
    main()
