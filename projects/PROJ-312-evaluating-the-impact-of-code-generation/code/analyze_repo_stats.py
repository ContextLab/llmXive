"""
Task T017: Calculate and log median star count and median number of contributors
for selected repositories.

Reads the list of repositories from data/raw/repos.json (produced by T012a),
computes the median stars and median contributors, and logs the results.
"""
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any
from statistics import median

# Ensure logging is configured (re-uses project logging config if available)
try:
    from logging_config import setup_logging, get_logger
    logger = get_logger(__name__)
except ImportError:
    # Fallback if logging_config isn't imported yet or fails
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

def load_repos(filepath: str) -> List[Dict[str, Any]]:
    """Load repositories from the JSON file produced by T012a."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Repository data not found at {filepath}. "
                                "Ensure T012a has been executed.")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def calculate_medians(repos: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate median stars and median contributors.
    
    Args:
        repos: List of repository objects containing 'stars' and optionally 'contributors'.
    
    Returns:
        Dictionary with 'median_stars' and 'median_contributors'.
    """
    if not repos:
        raise ValueError("No repositories found to calculate medians.")

    stars = []
    contributors = []

    for repo in repos:
        if 'stars' in repo:
            stars.append(repo['stars'])
        
        # Handle missing contributors field gracefully
        if 'contributors' in repo:
            contributors.append(repo['contributors'])

    if not stars:
        raise ValueError("No star count data found in repositories.")

    median_stars = median(stars)
    median_contributors = median(contributors) if contributors else 0.0

    return {
        "median_stars": median_stars,
        "median_contributors": median_contributors,
        "total_repos_analyzed": len(repos),
        "repos_with_contributor_data": len(contributors)
    }

def main():
    """Main entry point for T017."""
    logger.info("Starting T017: Calculating repository statistics.")
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    repos_path = project_root / "data" / "raw" / "repos.json"

    try:
        repos = load_repos(str(repos_path))
        logger.info(f"Loaded {len(repos)} repositories from {repos_path}.")

        results = calculate_medians(repos)

        logger.info("-" * 50)
        logger.info("T017 RESULTS:")
        logger.info(f"  Total Repositories Analyzed: {results['total_repos_analyzed']}")
        logger.info(f"  Median Star Count: {results['median_stars']:.2f}")
        logger.info(f"  Median Number of Contributors: {results['median_contributors']:.2f}")
        logger.info(f"  Repos with Contributor Data: {results['repos_with_contributor_data']}")
        logger.info("-" * 50)

        # Optional: Save the summary to a JSON file for downstream tasks (FR-013)
        # This ensures the values are available for T029 without re-calculation
        summary_path = project_root / "data" / "processed" / "repo_summary_stats.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Summary statistics saved to {summary_path}")

    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data processing error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during T017 execution: {e}")
        raise

if __name__ == "__main__":
    main()