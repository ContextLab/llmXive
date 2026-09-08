"""
Main entry point for the plasma confinement analysis pipeline.
Implements global timeout and memory guards as per FR-007.
"""
import argparse
import sys
import logging
import traceback
import signal
from pathlib import Path
from typing import List, Optional

# Import logger setup first
from utils.logger import get_logger, setup_logging
# Import limits utilities
from utils.limits import (
    timeout_guard, 
    timeout_context, 
    memory_guard, 
    TimeoutError as LimitsTimeoutError, 
    MemoryLimitError
)

# Import pipeline components
from data.retrieval import fetch_data_for_discharge
from data.preprocessing import process_multiple_discharges
from data.validator import validate_input_schema, validate_output_schema
from analysis.metrics import process_metrics_for_discharges
from analysis.correlation import run_correlation_analysis

logger = get_logger(__name__)

# Configuration constants
PIPELINE_TIMEOUT_SECONDS = 3600  # 1 hour default
PIPELINE_MEMORY_LIMIT_MB = 7000  # ~7GB limit

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze DIII-D discharge data for magnetic topology impact."
    )
    parser.add_argument(
        "--discharges", 
        type=str, 
        required=True,
        help="Comma-separated list of discharge IDs (e.g., 167001,167002)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory for output files"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=PIPELINE_TIMEOUT_SECONDS,
        help=f"Pipeline timeout in seconds (default: {PIPELINE_TIMEOUT_SECONDS})"
    )
    parser.add_argument(
        "--memory-limit",
        type=int,
        default=PIPELINE_MEMORY_LIMIT_MB,
        help=f"Memory limit in MB (default: {PIPELINE_MEMORY_LIMIT_MB})"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    return parser.parse_args()

def validate_discharge_list(discharge_str: str) -> List[int]:
    """Validate and parse discharge list."""
    try:
        ids = [int(x.strip()) for x in discharge_str.split(",")]
        if not ids:
            raise ValueError("Discharge list cannot be empty")
        if len(ids) > 10:
            logger.warning("More than 10 discharges requested. Limiting to first 10.")
            ids = ids[:10]
        return ids
    except ValueError as e:
        raise ValueError(f"Invalid discharge list format: {e}")

@timeout_guard(PIPELINE_TIMEOUT_SECONDS)
@memory_guard(PIPELINE_MEMORY_LIMIT_MB)
def run_pipeline(discharge_ids: List[int], output_dir: str) -> bool:
    """
    Execute the full analysis pipeline with resource guards.
    
    Args:
        discharge_ids: List of discharge IDs to process
        output_dir: Directory to save outputs
        
    Returns:
        True if pipeline completed successfully
        
    Raises:
        LimitsTimeoutError: If pipeline exceeds time limit
        MemoryLimitError: If pipeline exceeds memory limit
    """
    logger.info(f"Starting pipeline for discharges: {discharge_ids}")
    
    try:
        # 1. Data Retrieval
        logger.info("Step 1: Retrieving data from MDSplus...")
        raw_data = {}
        for dis_id in discharge_ids:
            try:
                data = fetch_data_for_discharge(dis_id)
                if data:
                    raw_data[dis_id] = data
                    logger.info(f"Retrieved data for discharge {dis_id}")
                else:
                    logger.warning(f"No data retrieved for discharge {dis_id}")
            except Exception as e:
                logger.error(f"Failed to retrieve data for discharge {dis_id}: {e}")
                continue

        if len(raw_data) < 5:
            raise RuntimeError(
                f"Insufficient valid discharges: {len(raw_data)} < 5 required."
            )

        # 2. Preprocessing
        logger.info("Step 2: Preprocessing data...")
        processed_data = process_multiple_discharges(raw_data)
        
        # 3. Validation
        logger.info("Step 3: Validating schema...")
        if not validate_output_schema(processed_data):
            raise RuntimeError("Output schema validation failed")

        # 4. Metrics Calculation
        logger.info("Step 4: Calculating metrics...")
        metrics_data = process_metrics_for_discharges(processed_data)

        # 5. Correlation Analysis
        logger.info("Step 5: Running correlation analysis...")
        analysis_results = run_correlation_analysis(processed_data, metrics_data)

        # 6. Save Outputs
        logger.info("Step 6: Saving results...")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save unified dataset
        processed_data.to_csv(output_path / "unified_analysis.csv", index=False)
        logger.info(f"Saved unified dataset to {output_path / 'unified_analysis.csv'}")
        
        # Save metrics
        if metrics_data is not None:
            metrics_data.to_csv(output_path / "metrics.csv", index=False)
            logger.info(f"Saved metrics to {output_path / 'metrics.csv'}")

        logger.info("Pipeline completed successfully.")
        return True

    except LimitsTimeoutError:
        logger.error("Pipeline timed out.")
        raise
    except MemoryLimitError:
        logger.error("Pipeline exceeded memory limit.")
        raise
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        traceback.print_exc()
        return False

def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(level=args.log_level)
    
    logger.info("Initializing Plasma Confinement Analysis Pipeline")
    
    try:
        # Validate inputs
        discharge_ids = validate_discharge_list(args.discharges)
        
        # Run pipeline with guards
        success = run_pipeline(
            discharge_ids=discharge_ids,
            output_dir=args.output_dir
        )
        
        if not success:
            logger.error("Pipeline execution failed.")
            sys.exit(1)
            
    except LimitsTimeoutError:
        logger.critical("Pipeline execution aborted due to timeout.")
        sys.exit(124)  # Standard timeout exit code
    except MemoryLimitError:
        logger.critical("Pipeline execution aborted due to memory limit.")
        sys.exit(137)  # Standard OOM exit code (128+9)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
