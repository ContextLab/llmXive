import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from utils import validate_json_schema

class DataQualityError(Exception):
    """Raised when data quality thresholds are not met."""
    pass

def calculate_success_rate(processed_count: int, total_count: int) -> float:
    """
    Calculate the data quality success rate.
    
    Args:
        processed_count: Number of PRs successfully processed.
        total_count: Total number of PRs attempted.
    
    Returns:
        Success rate as a float between 0.0 and 1.0.
    """
    if total_count == 0:
        return 0.0
    return processed_count / total_count

def validate_and_check_quality(
    processed_file: str,
    raw_file: str,
    output_dir: str,
    threshold: float = 0.95
) -> Dict[str, Any]:
    """
    Validate data quality by comparing raw and processed counts.
    
    This function:
    1. Counts total PRs in the raw data file.
    2. Counts processed PRs in the processed data file.
    3. Calculates the success rate.
    4. If rate < threshold, logs a warning and saves error logs.
    5. Saves a quality status artifact.
    
    Args:
        processed_file: Path to processed CSV (pr_turnaround.csv).
        raw_file: Path to raw JSON (pr_data.json).
        output_dir: Directory for output artifacts.
        threshold: Minimum acceptable success rate (default 0.95).
    
    Returns:
        Dictionary containing quality status details.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    processed_path = Path(processed_file)
    raw_path = Path(raw_file)
    output_path = Path(output_dir)

    if not processed_path.exists():
        raise FileNotFoundError(f"Processed data file not found: {processed_file}")
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_file}")

    # Count total PRs in raw data
    with open(raw_path, 'r') as f:
        raw_data = json.load(f)
    total_count = len(raw_data)

    # Count processed PRs in CSV
    processed_count = 0
    with open(processed_path, 'r') as f:
        # Skip header if exists
        first_line = True
        for line in f:
            if first_line:
                first_line = False
                continue
            if line.strip():
                processed_count += 1

    success_rate = calculate_success_rate(processed_count, total_count)

    logger.info(f"Data Quality Check: {processed_count}/{total_count} PRs processed ({success_rate:.2%})")

    quality_status = {
        "total_prs": total_count,
        "processed_prs": processed_count,
        "success_rate": success_rate,
        "threshold": threshold,
        "status": "warning" if success_rate < threshold else "ok"
    }

    if success_rate < threshold:
        logger.warning(f"Data quality rate {success_rate:.2%} is below threshold {threshold:.2%}")
        
        # Save detailed error log
        error_log_path = output_path / "data_quality_warning.log"
        with open(error_log_path, 'w') as log_file:
            log_file.write(f"Data Quality Warning Log\n")
            log_file.write(f"==========================\n")
            log_file.write(f"Timestamp: {logging.root.handlers[0].formatter.formatTime(logging.root.handlers[0].records[-1] if logging.root.handlers[0].records else None)}\n")
            log_file.write(f"Total PRs: {total_count}\n")
            log_file.write(f"Processed PRs: {processed_count}\n")
            log_file.write(f"Success Rate: {success_rate:.2%}\n")
            log_file.write(f"Threshold: {threshold:.2%}\n")
            log_file.write(f"Status: WARNING - Rate below threshold.\n")
            log_file.write(f"\nNote: Pipeline will proceed but final report will include a limitation statement.\n")
        
        logger.info(f"Saved warning log to: {error_log_path}")

    # Save quality status artifact
    quality_status_path = output_path / "quality_status.json"
    with open(quality_status_path, 'w') as f:
        json.dump(quality_status, f, indent=2)
    logger.info(f"Saved quality status to: {quality_status_path}")

    return quality_status

def main():
    """Main entry point for data quality check."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    processed_file = project_root / "data" / "processed" / "pr_turnaround.csv"
    raw_file = project_root / "data" / "raw" / "pr_data.json"
    output_dir = project_root / "data" / "processed"

    try:
        result = validate_and_check_quality(
            processed_file=str(processed_file),
            raw_file=str(raw_file),
            output_dir=str(output_dir),
            threshold=0.95
        )
        print(f"Quality check completed. Status: {result['status']}")
        print(f"Success rate: {result['success_rate']:.2%}")
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        raise
    except Exception as e:
        logging.error(f"Error during quality check: {e}")
        raise

if __name__ == "__main__":
    main()
