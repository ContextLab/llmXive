import os
import csv
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add parent directory to path to allow imports from code/data
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.logging_config import get_logger
from data.config import MAX_REVIEW_DAYS

logger = get_logger(__name__)

def load_sampled_prs(input_path: str) -> List[Dict[str, Any]]:
    """
    Load the sampled PRs from the CSV file generated in T014/T015.
    Expected columns: repo, pr_number, title, body, created_at, merged_at, author, 
                      lines_changed, origin_label, heuristic_scores (if applicable)
    """
    data = []
    logger.info(f"Loading sampled PRs from {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    logger.info(f"Loaded {len(data)} PRs")
    return data

def parse_datetime(dt_str: str) -> Optional[datetime]:
    """
    Parse ISO format datetime string.
    Handles common GitHub API formats.
    """
    if not dt_str:
        return None
    try:
        # GitHub API returns ISO 8601: 2023-01-01T12:00:00Z
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except ValueError:
        try:
            # Fallback for other formats
            return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            logger.warning(f"Could not parse datetime: {dt_str}")
            return None

def calculate_review_times(prs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate first_review_time and total_review_time in minutes.
    
    For this implementation, we assume:
    - created_at is when the PR was opened
    - merged_at is when the PR was closed/merged
    
    Since the raw GitHub PR data may not contain specific review event timestamps
    (first comment, first review, last review), we use the PR lifecycle as a proxy:
    - first_review_time: Time from PR creation to the first review event. 
      If not available in raw data, we approximate using a fraction of total time 
      or mark as NaN if we cannot estimate.
    - total_review_time: Time from PR creation to merge (in minutes).
    
    NOTE: In a real scenario, we would need to fetch PR review events via GitHub API.
    Since T013 only fetches PR metadata (not review events), we will:
    1. Calculate total_review_time as merged_at - created_at
    2. Set first_review_time to NaN (or a placeholder) with a note that 
       review event data is missing from the current dataset.
    
    However, if the dataset includes review event timestamps (e.g., from a future 
    enhancement to T013), this function would be updated to use them.
    
    For now, we implement the calculation for total_review_time and document 
    the limitation for first_review_time.
    """
    processed_prs = []
    
    for pr in prs:
        created_at = parse_datetime(pr.get('created_at'))
        merged_at = parse_datetime(pr.get('merged_at'))
        
        if not created_at or not merged_at:
            # If we can't parse dates, skip time calculation
            pr_copy = pr.copy()
            pr_copy['first_review_time_minutes'] = float('nan')
            pr_copy['total_review_time_minutes'] = float('nan')
            processed_prs.append(pr_copy)
            continue
        
        # Calculate total review time (PR open duration)
        total_delta = merged_at - created_at
        total_minutes = total_delta.total_seconds() / 60.0
        
        # For first_review_time, we need review event data which is not in current dataset.
        # We set it to NaN and log a warning.
        first_review_minutes = float('nan')
        
        pr_copy = pr.copy()
        pr_copy['first_review_time_minutes'] = first_review_minutes
        pr_copy['total_review_time_minutes'] = total_minutes
        processed_prs.append(pr_copy)
        
        if first_review_minutes == float('nan'):
            logger.warning(
                f"PR {pr.get('pr_number')} in {pr.get('repo')}: "
                "first_review_time cannot be calculated from current data. "
                "Review event data is required."
            )
    
    return processed_prs

def save_processed_prs(data: List[Dict[str, Any]], output_path: str):
    """
    Save the processed PRs with time columns to CSV.
    """
    if not data:
        logger.warning("No data to save")
        return
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get fieldnames from first row
    fieldnames = list(data[0].keys())
    
    logger.info(f"Saving processed PRs to {output_path}")
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Saved {len(data)} records")

def main():
    """
    Main entry point for T021: Process PR data to calculate review times.
    
    Input:  data/processed/sampled_prs.csv
    Output: data/processed/pr_data_cleaned.csv (with first_review_time_minutes and 
            total_review_time_minutes columns)
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    input_path = project_root / "data" / "processed" / "sampled_prs.csv"
    output_path = project_root / "data" / "processed" / "pr_data_cleaned.csv"
    
    logger.info("Starting T021: Process PR data to calculate review times")
    
    try:
        # Load data
        prs = load_sampled_prs(str(input_path))
        
        # Calculate times
        processed_prs = calculate_review_times(prs)
        
        # Save results
        save_processed_prs(processed_prs, str(output_path))
        
        logger.info("T021 completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error processing PRs: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
