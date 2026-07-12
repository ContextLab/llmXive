"""
Demo script to run the validator on test data and generate audit_report.json.

This script:
1. Loads test summaries from data/synthetic/test_summaries.json
2. Loads test reconstruction results from data/synthetic/test_reconstruction_results.json
3. Runs the validator
4. Writes output/audit_report.json
"""

import json
import sys
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.audit.validator import run_validator
from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_default_logger

logger = get_default_logger(__name__)

def main():
    """Run the validator demo."""
    # Paths
    summaries_path = Path("data/synthetic/test_summaries.json")
    reconstruction_path = Path("data/synthetic/test_reconstruction_results.json")
    output_path = Path("output/audit_report.json")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load summaries
    if not summaries_path.exists():
        logger.error(f"Summaries file not found: {summaries_path}")
        return 1
    
    with open(summaries_path, 'r', encoding='utf-8') as f:
        summaries_data = json.load(f)
    
    summaries = [ABTestSummary(**item) for item in summaries_data]
    logger.info(f"Loaded {len(summaries)} summaries")
    
    # Load reconstruction results
    if not reconstruction_path.exists():
        logger.error(f"Reconstruction results file not found: {reconstruction_path}")
        return 1
    
    with open(reconstruction_path, 'r', encoding='utf-8') as f:
        reconstructed_results = json.load(f)
    
    logger.info(f"Loaded {len(reconstructed_results)} reconstruction results")
    
    # Run validation
    logger.info("Running validation...")
    summary = run_validator(summaries, reconstructed_results, output_path)
    
    # Print summary
    print("\n=== Validation Summary ===")
    print(json.dumps(summary, indent=2))
    
    print(f"\nAudit report written to: {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())