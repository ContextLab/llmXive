"""
Analysis runner script for User Story 2.
Loads dependencies_raw.csv, runs Spearman correlation analysis,
and saves results to data/processed/results_correlation.json.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path to ensure imports work when run from CLI
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.correlation import load_dependencies_data, run_correlation_analysis
from src.utils.checksum import generate_checksum, write_checksum_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the analysis runner.
    1. Loads raw dependency data from data/processed/dependencies_raw.csv
    2. Runs Spearman correlation analysis between age and vulnerability count
    3. Saves results to data/processed/results_correlation.json
    4. Generates a checksum for the output file
    """
    logger.info("Starting correlation analysis pipeline...")

    # Define paths
    input_path = project_root / "data" / "processed" / "dependencies_raw.csv"
    output_path = project_root / "data" / "processed" / "results_correlation.json"
    checksum_path = project_root / "data" / "processed" / "results_correlation.sha256"

    # Validate input file exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T018 (export_data) has been run successfully first.")
        sys.exit(1)

    try:
        # Step 1: Load data
        logger.info(f"Loading data from {input_path}...")
        df = load_dependencies_data(input_path)
        
        if df is None or df.empty:
            logger.error("Loaded data is empty. Cannot perform analysis.")
            sys.exit(1)
        
        logger.info(f"Loaded {len(df)} records.")

        # Step 2: Run correlation analysis
        logger.info("Running Spearman correlation analysis...")
        results = run_correlation_analysis(df)

        if results is None:
            logger.error("Analysis failed to produce results.")
            sys.exit(1)

        # Step 3: Prepare output payload
        output_payload = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "input_file": str(input_path.name),
                "record_count": len(df)
            },
            "results": results
        }

        # Step 4: Write output JSON
        logger.info(f"Writing results to {output_path}...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_payload, f, indent=2, default=str)

        logger.info(f"Results saved to {output_path}")

        # Step 5: Generate checksum
        logger.info(f"Generating checksum for {output_path}...")
        checksum = generate_checksum(output_path)
        write_checksum_file(output_path, checksum)
        logger.info(f"Checksum saved to {checksum_path}")

        logger.info("Analysis pipeline completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Critical error during analysis: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())