import os
import csv
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.logging import get_logger, setup_logging
from utils.config import get_path
from analysis.complexity import compute_complexity_for_prs

logger = get_logger(__name__)

def setup_logging_and_config():
    """Initialize logging and configuration for complexity score saving."""
    setup_logging()
    return get_path("processed", "complexity_scores.csv")

def load_labeled_prs() -> List[Dict[str, Any]]:
    """Load the labeled PRs dataset from data/processed/prs_labeled.csv."""
    input_path = get_path("processed", "prs_labeled.csv")
    if not input_path.exists():
        logger.error(f"Labeled PRs file not found: {input_path}")
        raise FileNotFoundError(f"Labeled PRs file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def extract_pr_diff(pr: Dict[str, Any]) -> str:
    """Extract the diff text from a PR object."""
    # In a real implementation, this would fetch the actual diff
    # For now, we assume the diff is available in the raw data
    diff_data = pr.get('diff', '')
    if not diff_data and 'raw' in pr:
        diff_data = pr['raw'].get('diff', '')
    return str(diff_data)

def calculate_complexity_score(diff_text: str) -> float:
    """
    Calculate complexity score for a PR diff using cyclomatic complexity.
    Uses the complexity analysis module.
    """
    if not diff_text:
        return 0.0
    
    # Use the complexity module to calculate score
    # This is a simplified wrapper around the actual complexity calculation
    try:
        # In a real implementation, we would parse the diff and calculate
        # cyclomatic complexity. For now, we use a placeholder that calls
        # the actual complexity module.
        from analysis.complexity import analyze_diff_complexity
        complexity = analyze_diff_complexity(diff_text)
        return float(complexity)
    except Exception as e:
        logger.warning(f"Failed to calculate complexity for diff: {e}")
        return 0.0

def save_complexity_scores(prs: List[Dict[str, Any]], output_path: Path):
    """
    Save complexity scores to CSV with pr_id and complexity_score columns.
    Implements T033: Create save_complexity_scores.py to output complexity_scores.csv
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['pr_id', 'complexity_score']
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for pr in prs:
            pr_id = int(pr['pr_id'])
            diff_text = extract_pr_diff(pr)
            complexity_score = calculate_complexity_score(diff_text)
            
            row = {
                'pr_id': pr_id,
                'complexity_score': float(complexity_score)
            }
            writer.writerow(row)
        
        logger.info(f"Saved complexity scores for {len(prs)} PRs to {output_path}")

def main():
    """Main entry point for saving complexity scores."""
    setup_logging_and_config()
    
    try:
        # Load labeled PRs
        logger.info("Loading labeled PRs...")
        labeled_prs = load_labeled_prs()
        logger.info(f"Loaded {len(labeled_prs)} labeled PRs")
        
        # Save complexity scores
        output_path = get_path("processed", "complexity_scores.csv")
        save_complexity_scores(labeled_prs, output_path)
        
        logger.info("Complexity scores saving completed successfully")
    except Exception as e:
        logger.error(f"Failed to save complexity scores: {e}")
        raise

if __name__ == "__main__":
    main()
