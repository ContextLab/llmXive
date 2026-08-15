import os
import sys
import json
import logging
import pandas as pd
from datetime import datetime
from utils.logging import get_logger

logger = get_logger(__name__)

def calculate_completeness(df: pd.DataFrame) -> float:
    """
    Calculate the percentage of non-null values in the dataset.
    
    Args:
        df: DataFrame containing the time-series data.
        
    Returns:
        Float representing the completeness percentage (0.0 to 100.0).
    """
    if df.empty:
        return 0.0
    
    # Count total cells and non-null cells
    total_cells = df.size
    non_null_cells = df.count().sum()
    
    if total_cells == 0:
        return 0.0
        
    completeness = (non_null_cells / total_cells) * 100
    return completeness

def check_post_interpolation_completeness(
    input_path: str,
    output_path: str,
    threshold: float = 95.0
) -> bool:
    """
    Verify that the processed time-series data meets the minimum completeness threshold.
    
    Args:
        input_path: Path to the aligned timeseries CSV.
        output_path: Path to write the validation_status.json.
        threshold: Minimum required completeness percentage (default 95.0%).
        
    Returns:
        True if completeness meets threshold, False otherwise.
        
    Raises:
        FileNotFoundError: If input file does not exist.
        ValueError: If file is empty or invalid.
    """
    logger.info(f"Checking post-interpolation completeness for {input_path}")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        raise
    
    if df.empty:
        logger.error("Input DataFrame is empty")
        raise ValueError("Input DataFrame is empty")
    
    completeness = calculate_completeness(df)
    logger.info(f"Calculated completeness: {completeness:.2f}%")
    
    passed = completeness >= threshold
    status = "PASSED" if passed else "FAILED"
    
    validation_result = {
        "timestamp": datetime.utcnow().isoformat(),
        "input_file": input_path,
        "completeness_percentage": completeness,
        "threshold_percentage": threshold,
        "status": status,
        "passed": passed
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(validation_result, f, indent=2)
    
    logger.info(f"Validation result written to {output_path}")
    
    if not passed:
        logger.error(f"Completeness check FAILED: {completeness:.2f}% < {threshold}%")
    
    return passed

def main():
    """Main entry point for the post-interpolation check."""
    # Define paths relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    input_path = os.path.join(project_root, "data", "processed", "aligned_timeseries.csv")
    output_path = os.path.join(project_root, "data", "processed", "validation_status.json")
    
    # Setup logging
    setup_logging = False
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    try:
        success = check_post_interpolation_completeness(input_path, output_path)
        if success:
            logger.info("Post-interpolation completeness check PASSED")
            sys.exit(0)
        else:
            logger.error("Post-interpolation completeness check FAILED")
            sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
