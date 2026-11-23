"""
T014f: Log Event Count
Reads the filtered dataset and writes the total event count to a log file.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
import pandas as pd

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.preprocess import load_config
from utils.config import set_seed

# Constants
FILTERED_DATA_PATH = Path("data/processed/filtered.parquet")
EVENT_COUNTS_LOG_PATH = Path("data/logs/event_counts.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def count_events(input_path: Path) -> int:
    """
    Reads the parquet file and returns the total number of rows (events).
    
    Args:
        input_path: Path to the filtered parquet file.
        
    Returns:
        Total count of events (rows).
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}...")
    df = pd.read_parquet(input_path)
    count = len(df)
    logger.info(f"Loaded {count} events.")
    return count


def write_event_count(count: int, output_path: Path) -> None:
    """
    Writes the event count to the log file as a single integer followed by a newline.
    
    Args:
        count: The integer count to write.
        output_path: Path to the output log file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing event count ({count}) to {output_path}...")
    with open(output_path, 'w') as f:
        f.write(f"{count}\n")
    
    logger.info("Successfully wrote event count.")


def main() -> None:
    """Main entry point for T014f."""
    parser = argparse.ArgumentParser(description="Log the total number of events from the filtered dataset.")
    parser.add_argument(
        "--input", 
        type=Path, 
        default=FILTERED_DATA_PATH, 
        help=f"Path to the filtered parquet file (default: {FILTERED_DATA_PATH})"
    )
    parser.add_argument(
        "--output", 
        type=Path, 
        default=EVENT_COUNTS_LOG_PATH, 
        help=f"Path to the output log file (default: {EVENT_COUNTS_LOG_PATH})"
    )
    parser.add_argument(
        "--seed", 
        type=int, 
        default=42, 
        help="Random seed for reproducibility (default: 42)"
    )
    
    args = parser.parse_args()
    
    set_seed(args.seed)
    
    try:
        count = count_events(args.input)
        write_event_count(count, args.output)
        logger.info(f"Task T014f completed successfully. Count: {count}")
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        logger.error("Ensure T014d (Data Filtering) has run successfully to generate data/processed/filtered.parquet")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during event counting: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()