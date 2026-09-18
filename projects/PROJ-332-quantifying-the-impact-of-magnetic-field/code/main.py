import argparse
import sys
import logging
import traceback
import signal
from pathlib import Path
from utils.logger import setup_logging, get_logger
from utils.limits import timeout_guard
from data.preprocessing import process_multiple_discharges, validate_parsed_data, save_unified_dataset
from data.retrieval import fetch_data_for_discharge

logger = get_logger(__name__)

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='Quantifying the Impact of Magnetic Field Topology on Plasma Confinement'
    )
    parser.add_argument(
        '--discharges',
        nargs='+',
        type=int,
        required=True,
        help='List of discharge IDs to process'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/processed',
        help='Output directory for processed data'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=3600,
        help='Execution timeout in seconds'
    )
    return parser.parse_args()

def validate_discharge_list(discharge_ids: list) -> bool:
    """
    Validate the list of discharge IDs.
    
    Args:
        discharge_ids: List of discharge IDs
    
    Returns:
        True if valid, False otherwise
    """
    if not discharge_ids:
        logger.error("No discharge IDs provided.")
        return False
    
    if len(discharge_ids) > 10:
        logger.warning("More than 10 discharges requested. Limiting to 10.")
        discharge_ids = discharge_ids[:10]
    
    return True

def check_minimum_discharges(valid_discharges: list, min_count: int = 5) -> bool:
    """
    Check if the number of valid discharges meets the minimum requirement.
    
    Args:
        valid_discharges: List of valid discharge data
        min_count: Minimum required count
    
    Returns:
        True if minimum met, False otherwise
    """
    if len(valid_discharges) < min_count:
        logger.error(f"Insufficient valid discharges: {len(valid_discharges)} < {min_count}")
        return False
    return True

@timeout_guard
def run_pipeline(discharge_ids: list, output_dir: str, timeout: int):
    """
    Run the data processing pipeline.
    
    Args:
        discharge_ids: List of discharge IDs to process
        output_dir: Output directory for results
        timeout: Execution timeout
    
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Starting pipeline for discharges: {discharge_ids}")
    
    # Fetch data for each discharge
    parsed_data_list = []
    for discharge_id in discharge_ids:
        try:
            logger.info(f"Fetching data for discharge {discharge_id}")
            raw_data = fetch_data_for_discharge(discharge_id)
            if raw_data:
                from data.preprocessing import parse_discharge_data
                parsed = parse_discharge_data(raw_data, discharge_id)
                parsed_data_list.append(parsed)
        except Exception as e:
            logger.error(f"Failed to process discharge {discharge_id}: {e}")
            continue
    
    # Process multiple discharges into a DataFrame
    df = process_multiple_discharges(parsed_data_list)
    
    if not validate_parsed_data(df):
        logger.error("Validation failed for parsed data.")
        return False
    
    # Check minimum discharges
    if not check_minimum_discharges(parsed_data_list):
        return False
    
    # Save unified dataset
    output_path = Path(output_dir) / "unified_analysis.csv"
    file_path, checksum = save_unified_dataset(df, str(output_path))
    
    logger.info(f"Pipeline completed successfully. Output: {file_path}, Checksum: {checksum}")
    return True

def main():
    """
    Main entry point for the application.
    """
    args = parse_arguments()
    
    # Setup logging
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(log_level=log_level)
    
    # Validate inputs
    if not validate_discharge_list(args.discharges):
        logger.error("Invalid discharge list.")
        sys.exit(1)
    
    try:
        success = run_pipeline(
            discharge_ids=args.discharges,
            output_dir=args.output_dir,
            timeout=args.timeout
        )
        
        if not success:
            logger.error("Pipeline execution failed.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Pipeline failed with exception: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()