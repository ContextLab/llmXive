"""
Task T021g: ANCOVA Covariate Preparation

This script aggregates LOC, CC, and Doc Quality scores into a single covariate dataset.
It performs normalization/centering to prepare data for ANCOVA.

Output: data/raw/repo_covariates.json
"""
import json
import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports if run as script
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from validation import generate_covariates_json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for T021g.
    Aggregates metrics and doc quality into covariates, centers them, and saves.
    """
    logger.info("Starting ANCOVA Covariate Preparation (T021g)...")

    # Define paths
    metrics_path = project_root / "data" / "raw" / "repo_metrics.json"
    doc_quality_path = project_root / "data" / "raw" / "doc_quality_scores.json"
    output_path = project_root / "data" / "raw" / "repo_covariates.json"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Check dependencies
    if not metrics_path.exists():
        logger.error(f"Required input missing: {metrics_path}. Run T021c first.")
        sys.exit(1)
    
    if not doc_quality_path.exists():
        logger.error(f"Required input missing: {doc_quality_path}. Run T021f first.")
        sys.exit(1)

    logger.info(f"Loading metrics from {metrics_path}")
    with open(metrics_path, 'r') as f:
        metrics_data = json.load(f)

    logger.info(f"Loading doc quality scores from {doc_quality_path}")
    with open(doc_quality_path, 'r') as f:
        doc_quality_data = json.load(f)

    # Call the core logic from validation module
    # This function aggregates the data and performs centering
    covariates = generate_covariates_json(metrics_data, doc_quality_data)

    # Write output
    logger.info(f"Writing covariates to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(covariates, f, indent=2)

    logger.info("T021g completed successfully.")
    print(f"Output written to: {output_path}")

if __name__ == "__main__":
    main()
