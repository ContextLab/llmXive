"""
Task T022a: Calculate Match Success Rate (SC-001)

Computes the match success rate as:
(count_matched_pre_exclusion / count_total_original_valid_location) * 100

Reads counts from results/logs/counts.json and writes the result to
results/logs/match_success_rate.json.
"""
import json
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('results/logs/match_success_rate.log')
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure the output directory exists."""
    output_path = Path('results/logs')
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {output_path}")

def load_counts(counts_file_path: str) -> dict:
    """Load the counts dictionary from a JSON file."""
    path = Path(counts_file_path)
    if not path.exists():
        raise FileNotFoundError(f"Counts file not found: {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded counts from {path}")
    return data

def calculate_success_rate(counts: dict) -> float:
    """
    Calculate the match success rate.
    
    Formula: (count_matched_pre_exclusion / count_total_original_valid_location) * 100
    """
    total_valid = counts.get('count_total_original_valid_location')
    matched_pre = counts.get('count_matched_pre_exclusion')
    
    if total_valid is None:
        raise ValueError("Missing 'count_total_original_valid_location' in counts data")
    if matched_pre is None:
        raise ValueError("Missing 'count_matched_pre_exclusion' in counts data")
    
    if total_valid == 0:
        logger.warning("Total valid location count is 0. Cannot calculate success rate.")
        return 0.0
    
    rate = (matched_pre / total_valid) * 100
    logger.info(f"Calculated success rate: {rate:.2f}% ({matched_pre}/{total_valid})")
    return rate

def save_success_rate(rate: float, output_file_path: str):
    """Save the success rate to a JSON file."""
    path = Path(output_file_path)
    result = {
        "match_success_rate": rate,
        "count_matched_pre_exclusion": int((rate / 100) * (Path(output_file_path).parent / Path('counts.json').name).parent.parent), # Placeholder logic, will fix below
        "formula": "(count_matched_pre_exclusion / count_total_original_valid_location) * 100"
    }
    
    # Re-load to get exact integers for the report
    counts_path = Path(output_file_path).parent / 'counts.json'
    with open(counts_path, 'r') as f:
        counts = json.load(f)
    
    result["count_matched_pre_exclusion"] = counts.get("count_matched_pre_exclusion")
    result["count_total_original_valid_location"] = counts.get("count_total_original_valid_location")
    
    with open(path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Saved success rate to {path}")

def main():
    """Main entry point for Task T022a."""
    ensure_directories()
    
    counts_file = 'results/logs/counts.json'
    output_file = 'results/logs/match_success_rate.json'
    
    try:
        counts = load_counts(counts_file)
        rate = calculate_success_rate(counts)
        save_success_rate(rate, output_file)
        logger.info("Task T022a completed successfully.")
    except Exception as e:
        logger.error(f"Task T022a failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
