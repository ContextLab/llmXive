"""
Task T022a: Calculate Match Success Rate (SC-001)

Computes the match success rate as defined by SC-001:
(count_matched_pre_exclusion / count_total_original_valid_location) * 100

Reads counts from results/logs/counts.json (produced by T017-run and T019a)
and writes the percentage to results/logs/match_success_rate.json.
"""

import json
import logging
import sys
from pathlib import Path

# Configure logging to stderr and file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler("results/logs/match_success_rate.log")
    ]
)
logger = logging.getLogger("T022a_MatchSuccessRate")

def ensure_directories():
    """Ensure the output directory exists."""
    output_dir = Path("results/logs")
    output_dir.mkdir(parents=True, exist_ok=True)

def load_counts():
    """
    Load counts from results/logs/counts.json.
    Expects keys: 'count_total_original_valid_location' and 'count_matched_pre_exclusion'.
    """
    counts_path = Path("results/logs/counts.json")
    if not counts_path.exists():
        raise FileNotFoundError(
            f"Required counts file not found: {counts_path}. "
            "Ensure T017-run and T019a have completed successfully."
        )
    
    with open(counts_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def calculate_success_rate(counts):
    """
    Calculate SC-001: (count_matched_pre_exclusion / count_total_original_valid_location) * 100.
    """
    total_valid = counts.get("count_total_original_valid_location")
    matched_pre_exclusion = counts.get("count_matched_pre_exclusion")

    if total_valid is None:
        raise ValueError("Missing 'count_total_original_valid_location' in counts file.")
    if matched_pre_exclusion is None:
        raise ValueError("Missing 'count_matched_pre_exclusion' in counts file.")
    
    if total_valid == 0:
        logger.warning("Total valid location count is 0. Success rate is undefined (0/0). Setting to 0.0.")
        return 0.0

    rate = (matched_pre_exclusion / total_valid) * 100
    return rate

def save_success_rate(rate, output_path):
    """Save the calculated rate to the specified JSON file."""
    result = {
        "match_success_rate_percent": round(rate, 4),
        "formula": "(count_matched_pre_exclusion / count_total_original_valid_location) * 100",
        "sc_id": "SC-001"
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Successfully saved match success rate ({rate:.4f}%) to {output_path}")

def main():
    logger.info("Starting T022a: Calculate Match Success Rate")
    
    try:
        ensure_directories()
        counts = load_counts()
        
        logger.info(f"Loaded counts: {counts}")
        
        rate = calculate_success_rate(counts)
        
        output_file = Path("results/logs/match_success_rate.json")
        save_success_rate(rate, output_file)
        
        logger.info("T022a completed successfully.")
        return 0
    
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
