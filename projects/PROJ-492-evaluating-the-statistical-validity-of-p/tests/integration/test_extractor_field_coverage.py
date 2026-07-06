"""
Integration test for T036: FR-002 Verification.
Verifies that extracted fields exist for > 95% of valid pages.
"""
import json
import csv
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Set

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.src.utils.logger import get_default_logger, get_error_message
from code.src.models.data_models import ABTestSummary

logger = get_default_logger()

# Define the required fields based on the ABTestSummary model and FR-002
# These are the core fields that must be present for a "valid" extraction
REQUIRED_FIELDS: Set[str] = {
    "url",
    "domain",
    "baseline_n",
    "treatment_n",
    "baseline_successes",
    "treatment_successes",
    "p_value",
    "outcome_type",
    "test_type"
}

def load_extracted_summaries(path: Path) -> List[Dict[str, Any]]:
    """Load extracted summaries from the JSON file produced by T020."""
    if not path.exists():
        raise FileNotFoundError(f"Extracted summaries file not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Handle both list and dict with 'summaries' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "summaries" in data:
        return data["summaries"]
    else:
        raise ValueError("Invalid format in extracted summaries file")

def calculate_field_coverage(summaries: List[Dict[str, Any]], required_fields: Set[str]) -> float:
    """
    Calculate the percentage of valid pages where all required fields exist.
    A page is 'valid' if it has at least one of the required fields (not empty/null).
    A page is 'complete' if it has ALL required fields.
    """
    if not summaries:
        return 0.0

    valid_count = 0
    complete_count = 0

    for item in summaries:
        # Check if the record has any meaningful data (is it a valid extraction attempt?)
        # We consider it valid if it has a URL and at least one metric
        has_url = item.get("url")
        has_metrics = any(
            item.get(k) is not None 
            for k in ["baseline_n", "treatment_n", "p_value"]
        )
        
        if has_url and has_metrics:
            valid_count += 1
            
            # Check if ALL required fields are present and not None
            has_all_fields = all(
                item.get(field) is not None 
                for field in required_fields
            )
            
            if has_all_fields:
                complete_count += 1

    if valid_count == 0:
        return 0.0

    return (complete_count / valid_count) * 100.0

def main():
    """
    Main entry point for the test.
    Verifies that extracted fields exist for > 95% of valid pages.
    """
    logger.info("Starting FR-002 Verification (T036): Extracted fields coverage check")
    
    # Define paths
    extracted_summaries_path = project_root / "output" / "extracted_summaries.json"
    
    try:
        # Load data
        summaries = load_extracted_summaries(extracted_summaries_path)
        logger.info(f"Loaded {len(summaries)} extracted summaries")
        
        # Calculate coverage
        coverage_pct = calculate_field_coverage(summaries, REQUIRED_FIELDS)
        logger.info(f"Field coverage: {coverage_pct:.2f}%")
        
        # Threshold defined in FR-002
        threshold = 95.0
        
        if coverage_pct >= threshold:
            logger.info(f"SUCCESS: Coverage ({coverage_pct:.2f}%) meets threshold ({threshold}%)")
            return 0
        else:
            error_msg = get_error_message("ERR-802") # Reusing ERR-802 for validation failures
            logger.error(f"FAILURE: Coverage ({coverage_pct:.2f}%) is below threshold ({threshold}%). {error_msg}")
            return 1

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        logger.error("Cannot run T036 verification without extracted_summaries.json. Run T020 first.")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
