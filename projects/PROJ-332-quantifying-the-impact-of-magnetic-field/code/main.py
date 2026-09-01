import argparse
import sys
import logging
import traceback
from pathlib import Path
from utils.logger import get_logger, setup_logging
from data.retrieval import fetch_data_for_discharge
from data.preprocessing import process_multiple_discharges, validate_parsed_data
from data.validator import validate_output_schema
from utils.limits import timeout_guard, memory_guard

# Configuration constants
MIN_VALID_DISCHARGES = 5
DEFAULT_DISCHARGE_IDS = [166666, 166667, 166668, 166669, 166670, 166671, 166672, 166673, 166674, 166675]

logger = get_logger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Quantify the impact of magnetic field topology on plasma confinement."
    )
    parser.add_argument(
        "--discharges",
        type=str,
        nargs="+",
        help="List of DIII-D discharge IDs to process (space-separated).",
        default=None
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory to save processed output files."
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3600,
        help="Timeout in seconds for the entire pipeline execution."
    )
    parser.add_argument(
        "--memory-limit-mb",
        type=int,
        default=7000,
        help="Memory limit in MB for the pipeline execution."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level."
    )
    return parser.parse_args()


def validate_discharge_list(discharge_ids: list) -> bool:
    """
    Validate that the discharge list is not empty and contains valid integers.
    Returns True if valid, False otherwise.
    """
    if not discharge_ids:
        logger.error("No discharge IDs provided.")
        return False
    
    for d_id in discharge_ids:
        if not isinstance(d_id, int):
            try:
                int(d_id)
            except (ValueError, TypeError):
                logger.error(f"Invalid discharge ID format: {d_id}. Must be an integer.")
                return False
    return True


def run_pipeline(discharge_ids: list, output_dir: str, timeout: int, memory_limit_mb: int) -> bool:
    """
    Execute the main data retrieval and preprocessing pipeline.
    
    This function:
    1. Fetches data for the provided discharge IDs from MDSplus.
    2. Processes the raw data into a unified DataFrame.
    3. Validates the parsed data against schemas.
    4. Enforces the minimum valid discharge count (FR-001).
    5. Returns True if the pipeline succeeds, False if it fails validation.
    """
    logger.info(f"Starting pipeline for {len(discharge_ids)} discharges: {discharge_ids}")
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Retrieve data for all discharges
        # fetch_data_for_discharge returns a dict of discharge_id -> raw_data or raises on failure
        all_raw_data = {}
        for d_id in discharge_ids:
            try:
                logger.info(f"Fetching data for discharge {d_id}...")
                raw_data = fetch_data_for_discharge(d_id)
                if raw_data is not None:
                    all_raw_data[d_id] = raw_data
                    logger.info(f"Successfully fetched data for discharge {d_id}.")
                else:
                    logger.warning(f"No data returned for discharge {d_id}. Skipping.")
            except Exception as e:
                logger.error(f"Failed to fetch data for discharge {d_id}: {e}. Skipping.")
                continue
        
        if not all_raw_data:
            logger.error("No data could be retrieved for any discharge.")
            return False
        
        # Step 2: Process raw data into unified format
        logger.info("Processing raw data into unified format...")
        processed_data = process_multiple_discharges(all_raw_data)
        
        if processed_data is None or processed_data.empty:
            logger.error("Data processing resulted in an empty dataset.")
            return False
        
        # Step 3: Validate parsed data against schemas
        logger.info("Validating processed data against output schema...")
        if not validate_output_schema(processed_data):
            logger.error("Processed data failed schema validation.")
            return False
        
        # Step 4: FR-001 Validation - Ensure at least MIN_VALID_DISCHARGES remain
        valid_count = len(processed_data)
        logger.info(f"Pipeline produced {valid_count} valid discharges.")
        
        if valid_count < MIN_VALID_DISCHARGES:
            error_msg = (
                f"FR-001 Violation: Insufficient valid discharges. "
                f"Required: >= {MIN_VALID_DISCHARGES}, Found: {valid_count}. "
                f"Pipeline execution aborted."
            )
            logger.error(error_msg)
            # Fail loudly as per constraints: do not proceed with insufficient data
            return False
        
        logger.info(f"Validation passed: {valid_count} >= {MIN_VALID_DISCHARGES}.")
        
        # Step 5: Save to disk (T016 responsibility, but main orchestrates the flow)
        # We save here to ensure the file exists for the next step or verification
        output_file = output_path / "unified_analysis.csv"
        processed_data.to_csv(output_file, index=False)
        logger.info(f"Saved unified dataset to {output_file}")
        
        return True
        
    except Exception as e:
        logger.critical(f"Pipeline execution failed with exception: {e}")
        traceback.print_exc()
        return False


@timeout_guard
@memory_guard
def main():
    """Main entry point for the pipeline."""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(level=args.log_level)
    logger.info("Pipeline initialization started.")
    
    # Determine discharge IDs
    discharge_ids = args.discharges
    if not discharge_ids:
        logger.info("No discharge IDs provided via CLI. Using defaults.")
        discharge_ids = DEFAULT_DISCHARGE_IDS
    else:
        # Convert to integers
        discharge_ids = [int(d) for d in discharge_ids]
    
    if not validate_discharge_list(discharge_ids):
        logger.error("Invalid discharge list provided.")
        sys.exit(1)
    
    # Run the pipeline with timeout and memory constraints
    success = run_pipeline(
        discharge_ids=discharge_ids,
        output_dir=args.output_dir,
        timeout=args.timeout,
        memory_limit_mb=args.memory_limit_mb
    )
    
    if success:
        logger.info("Pipeline completed successfully.")
        sys.exit(0)
    else:
        logger.error("Pipeline failed or was aborted due to validation errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()