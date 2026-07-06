"""
Integration test for T036: FR-002 Verification.
Verifies that extracted fields exist for > 95% of valid pages.
"""
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.src.utils.logger import get_default_logger, AuditLogger

logger = get_default_logger()

REQUIRED_FIELDS = [
    "url",
    "domain",
    "outcome_type",
    "n_control",
    "n_treatment",
    "metric_control",
    "metric_treatment",
    "p_value",
    "effect_size",
    "test_type"
]

def load_extracted_summaries(path: Path) -> List[Dict[str, Any]]:
    """Load the extracted summaries JSON file."""
    if not path.exists():
        logger.error(f"Extracted summaries file not found: {path}")
        return []
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and dict with 'summaries' key
    if isinstance(data, dict) and "summaries" in data:
        return data["summaries"]
    elif isinstance(data, list):
        return data
    else:
        logger.error(f"Unexpected data format in {path}")
        return []

def calculate_field_coverage(summaries: List[Dict[str, Any]]) -> float:
    """Calculate the percentage of valid pages that have all required fields."""
    if not summaries:
        return 0.0
    
    valid_count = 0
    for summary in summaries:
        if not isinstance(summary, dict):
            continue
        
        has_all_fields = all(field in summary and summary[field] is not None 
                           for field in REQUIRED_FIELDS)
        
        if has_all_fields:
            valid_count += 1
    
    return (valid_count / len(summaries)) * 100.0

def main() -> int:
    """Run the extraction accuracy verification test."""
    logger.info("Starting T036: FR-002 Verification - Extracted fields coverage check")
    
    # Determine paths
    summaries_path = project_root / "output" / "extracted_summaries.json"
    
    # Load data
    summaries = load_extracted_summaries(summaries_path)
    
    if not summaries:
        logger.error("No extracted summaries found. Pipeline may not have run successfully.")
        print("FAIL: No extracted summaries found")
        return 1
    
    logger.info(f"Loaded {len(summaries)} extracted summaries")
    
    # Calculate coverage
    coverage = calculate_field_coverage(summaries)
    logger.info(f"Field coverage: {coverage:.2f}%")
    
    # Check threshold (> 95%)
    threshold = 95.0
    if coverage > threshold:
        logger.info(f"SUCCESS: Coverage {coverage:.2f}% exceeds threshold {threshold}%")
        print(f"PASS: Extracted fields exist for {coverage:.2f}% of valid pages (> {threshold}% required)")
        return 0
    else:
        logger.error(f"FAIL: Coverage {coverage:.2f}% is below threshold {threshold}%")
        print(f"FAIL: Extracted fields exist for only {coverage:.2f}% of valid pages (need > {threshold}%)")
        return 1

if __name__ == "__main__":
    sys.exit(main())
