"""
T033b Implementation: Save complexity scores to CSV.

Reads prs_labeled.csv, computes complexity for each PR diff using the
existing complexity module, and writes pr_id, complexity_score to
data/processed/complexity_scores.csv.

Dependencies:
    - T033a (code/analysis/complexity.py) for complexity calculation
    - T017 (data/processed/prs_labeled.csv) as input
"""
import os
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any

# Import from project modules (matching API surface)
from utils.logging import get_logger, setup_logging
from utils.config import get_path
from utils.seeds import set_global_seed
from analysis.complexity import analyze_diff_complexity

logger = get_logger(__name__)

def setup_logging_and_config():
    """Initialize logging for this script."""
    # setup_logging() is called without arguments to match tolerant signature
    setup_logging()
    return get_path("processed", "complexity_scores.csv")

def load_labeled_prs() -> List[Dict[str, Any]]:
    """Load the labeled PRs dataset from data/processed/prs_labeled.csv."""
    input_path = get_path("processed", "prs_labeled.csv")
    if not input_path.exists():
        logger.error(f"Labeled PRs file not found: {input_path}")
        raise FileNotFoundError(f"Labeled PRs file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        logger.warning("Labeled PRs file is empty.")
    
    return rows

def extract_pr_diff(pr: Dict[str, Any]) -> str:
    """Extract the diff text from a PR object."""
    # Priority 1: Direct 'diff' field
    if pr.get('diff'):
        return str(pr['diff'])
    
    # Priority 2: Nested 'raw' -> 'diff'
    if pr.get('raw') and isinstance(pr['raw'], dict):
        diff_data = pr['raw'].get('diff')
        if diff_data:
            return str(diff_data)
    
    # Priority 3: Check for 'body' or 'patch' as fallback if diff is missing
    if pr.get('patch'):
        return str(pr['patch'])
    
    return ""

def calculate_complexity_score(diff_text: str) -> float:
    """
    Calculate complexity score for a PR diff using cyclomatic complexity.
    
    Uses the complexity analysis module (T033a).
    
    Returns:
        float: The complexity score (0.0 if diff is empty or calculation fails).
    """
    if not diff_text or not diff_text.strip():
        return 0.0
    
    try:
        # Call the complexity module function
        complexity = analyze_diff_complexity(diff_text)
        
        # Ensure we return a float
        if complexity is None:
            return 0.0
        
        score = float(complexity)
        
        # Clamp to non-negative
        if score < 0:
            score = 0.0
            
        return score
    except Exception as e:
        # Log warning but do not crash; return 0.0 for this PR
        logger.warning(f"Failed to calculate complexity for diff (error: {e}). Returning 0.0.")
        return 0.0

def save_complexity_scores(prs: List[Dict[str, Any]], output_path: Path):
    """
    Save complexity scores to CSV with pr_id and complexity_score columns.
    
    Implements T033b requirement:
    - Output: data/processed/complexity_scores.csv
    - Columns: pr_id (int), complexity_score (float)
    - Join on pr_id from prs_labeled.csv
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['pr_id', 'complexity_score']
    
    processed_count = 0
    skipped_count = 0
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for pr in prs:
            pr_id_raw = pr.get('pr_id')
            
            # Handle potential string IDs
            try:
                pr_id = int(pr_id_raw) if pr_id_raw is not None else 0
            except (ValueError, TypeError):
                logger.warning(f"Invalid pr_id '{pr_id_raw}', skipping row.")
                skipped_count += 1
                continue
            
            diff_text = extract_pr_diff(pr)
            complexity_score = calculate_complexity_score(diff_text)
            
            row = {
                'pr_id': pr_id,
                'complexity_score': f"{complexity_score:.6f}"
            }
            writer.writerow(row)
            processed_count += 1
    
    logger.info(f"Saved complexity scores for {processed_count} PRs to {output_path} (skipped {skipped_count}).")

def main():
    """Main entry point for saving complexity scores."""
    setup_logging_and_config()
    
    # Set seed for reproducibility
    set_global_seed(42)
    
    try:
        # Load labeled PRs
        logger.info("Loading labeled PRs from data/processed/prs_labeled.csv...")
        labeled_prs = load_labeled_prs()
        logger.info(f"Loaded {len(labeled_prs)} labeled PRs")
        
        if not labeled_prs:
            logger.warning("No PRs found to process. Creating empty output file.")
        
        # Save complexity scores
        output_path = get_path("processed", "complexity_scores.csv")
        save_complexity_scores(labeled_prs, output_path)
        
        logger.info("Complexity scores saving completed successfully")
    except FileNotFoundError as fnf:
        logger.error(f"Required input file missing: {fnf}")
        raise
    except Exception as e:
        logger.error(f"Failed to save complexity scores: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
