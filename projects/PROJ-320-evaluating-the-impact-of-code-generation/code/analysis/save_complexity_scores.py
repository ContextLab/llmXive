"""
Script to generate complexity_scores.csv from processed PR data and complexity analysis.

This script reads the labeled PR dataset, computes complexity metrics for each PR
using the existing complexity analysis module, and outputs a CSV with pr_id and
complexity_score columns.
"""

import os
import csv
import json
from pathlib import Path

# Import from sibling modules using the provided API surface
from utils.logging import get_logger, setup_logging
from utils.config import get_config_summary
from analysis.complexity import compute_complexity_for_prs, analyze_diff_complexity

# Setup logging
logger = get_logger(__name__)

def load_labeled_prs(input_path: Path) -> list:
    """Load labeled PRs from the processed CSV file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Labeled PRs file not found: {input_path}")
    
    prs = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prs.append(row)
    
    logger.info(f"Loaded {len(prs)} PRs from {input_path}")
    return prs

def extract_pr_diff(pr_data: dict) -> str:
    """Extract the diff content from PR data for complexity analysis."""
    # The diff might be stored in various fields depending on fetch_github.py output
    # Common fields: 'diff', 'patch', 'changes'
    diff_content = None
    
    # Try common field names
    for field in ['diff', 'patch', 'changes', 'body']:
        if field in pr_data and pr_data[field]:
            diff_content = pr_data[field]
            break
    
    # If no diff found, try to reconstruct from files
    if not diff_content and 'files' in pr_data:
        files = pr_data['files']
        if isinstance(files, list) and len(files) > 0:
            # Concatenate all file changes
            diff_parts = []
            for file_info in files:
                if isinstance(file_info, dict) and 'patch' in file_info:
                    diff_parts.append(file_info['patch'])
            diff_content = '\n'.join(diff_parts) if diff_parts else ""
    
    return diff_content or ""

def calculate_complexity_score(diff_content: str) -> float:
    """
    Calculate a normalized complexity score for a PR diff.
    
    Uses cyclomatic complexity and lines of code to produce a single score.
    Returns a float representing the complexity score.
    """
    if not diff_content.strip():
        return 0.0
    
    try:
        # Use the existing complexity analysis functions
        cc_metrics = analyze_diff_complexity(diff_content)
        
        # Extract cyclomatic complexity and LOC
        cc = cc_metrics.get('cyclomatic_complexity', 0)
        loc = cc_metrics.get('lines_of_code', 0)
        
        # Normalize: CC is typically 1-10 for most functions, LOC varies widely
        # Use a weighted combination: 70% CC, 30% LOC (normalized)
        # Normalize LOC by assuming typical PR is 100 lines
        normalized_loc = min(loc / 100.0, 10.0)  # Cap at 10 for very large PRs
        
        # Combined score: higher values mean more complex
        complexity_score = (0.7 * cc) + (0.3 * normalized_loc)
        
        return round(complexity_score, 4)
        
    except Exception as e:
        logger.warning(f"Complexity calculation failed: {e}")
        return 0.0

def save_complexity_scores(prs: list, output_path: Path):
    """Save complexity scores to CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['pr_id', 'complexity_score'])
        writer.writeheader()
        
        for pr in prs:
            pr_id = pr.get('pr_id', pr.get('id', 'unknown'))
            diff_content = extract_pr_diff(pr)
            score = calculate_complexity_score(diff_content)
            
            writer.writerow({
                'pr_id': str(pr_id),
                'complexity_score': score
            })
    
    logger.info(f"Saved complexity scores to {output_path}")

def main():
    """Main entry point for the complexity scores generation."""
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    input_file = project_root / 'data' / 'processed' / 'prs_labeled.csv'
    output_file = project_root / 'data' / 'processed' / 'complexity_scores.csv'
    
    logger.info("Starting complexity scores generation...")
    logger.info(f"Input: {input_file}")
    logger.info(f"Output: {output_file}")
    
    # Load labeled PRs
    prs = load_labeled_prs(input_file)
    
    if not prs:
        logger.warning("No PRs found in input file. Creating empty output.")
        save_complexity_scores([], output_file)
        return
    
    # Calculate and save complexity scores
    save_complexity_scores(prs, output_file)
    
    logger.info("Complexity scores generation completed successfully.")

if __name__ == '__main__':
    setup_logging()
    main()