"""
Script to execute Task T022: Generate results/permanova_summary.csv and results/db_rda_variance.csv.

This script assumes that the prerequisite analysis steps (T018, T019) have been run
and the intermediate results files exist at their expected locations.

It invokes the reporting pipeline to apply FDR correction if missing and save the final CSVs.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.pipelines.report import run_report_pipeline_with_null_handling

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Define paths relative to project root
    base_dir = project_root
    results_dir = base_dir / "results"
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)

    # Input paths (Assuming T018 and T019 outputs exist)
    permanova_input = results_dir / "permanova_raw_results.csv"
    varpart_input = results_dir / "varpart_summary.csv"
    
    # Output paths (T022 requirements)
    permanova_output = results_dir / "permanova_summary.csv"
    varpart_output = results_dir / "db_rda_variance.csv"

    # Check if input files exist
    if not permanova_input.exists():
        logger.error(f"Input file not found: {permanova_input}")
        logger.error("Prerequisite T018 (PERMANOVA analysis) must be run first.")
        sys.exit(1)

    if not varpart_input.exists():
        logger.warning(f"Input file not found: {varpart_input}")
        logger.warning("Prerequisite T019 (Varpart) not found. Generating empty db-RDA variance summary.")
        # We proceed, but the varpart step might generate an empty file or fail if data is strictly required
        # The report module handles missing inputs gracefully by creating empty schemas if needed.

    logger.info(f"Starting T022 analysis pipeline...")
    logger.info(f"Input PERMANOVA: {permanova_input}")
    logger.info(f"Input Varpart: {varpart_input}")
    logger.info(f"Output PERMANOVA: {permanova_output}")
    logger.info(f"Output Varpart: {varpart_output}")

    try:
        results = run_report_pipeline_with_null_handling(
            permanova_path=str(permanova_input),
            varpart_path=str(varpart_input),
            output_permanova=str(permanova_output),
            output_varpart=str(varpart_output)
        )
        logger.info("T022 Analysis completed successfully.")
        logger.info(f"Generated files: {results}")
        
        # Verify outputs exist
        if not permanova_output.exists():
            raise FileNotFoundError(f"Output file {permanova_output} was not created.")
        if not varpart_output.exists():
            raise FileNotFoundError(f"Output file {varpart_output} was not created.")
        
        print(f"SUCCESS: {permanova_output} and {varpart_output} generated.")
        
    except Exception as e:
        logger.error(f"T022 analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
