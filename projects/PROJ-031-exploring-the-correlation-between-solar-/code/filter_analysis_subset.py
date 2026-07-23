"""
Module to filter the primary aligned events dataset to create an analysis subset.

This task implements the logic to filter non-recurrent storms from the primary
dataset (`data/processed/aligned_events.csv`) to create a derived dataset
(`data/processed/analysis_subset.csv`) for use in correlation analysis (US2).

This satisfies the 'no exclusion' rule for the primary dataset while enabling
the analysis requirement for US2.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "aligned_events.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "analysis_subset.csv"

def filter_non_recurrent_storms(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    force: bool = False
) -> Dict[str, Any]:
    """
    Filter non-recurrent storms from the primary aligned events dataset.
    
    This function reads the primary aligned events dataset, filters out events
    marked as recurrent (is_recurrent=True), and writes the result to a new
    analysis subset file.
    
    Args:
        input_path: Path to the input aligned events CSV. Defaults to
                   PROJECT_ROOT/data/processed/aligned_events.csv.
        output_path: Path to the output analysis subset CSV. Defaults to
                    PROJECT_ROOT/data/processed/analysis_subset.csv.
        force: If True, overwrite the output file if it exists.
    
    Returns:
        A dictionary with statistics about the filtering operation:
        - total_input: Number of rows in the input file
        - recurrent_count: Number of recurrent events filtered out
        - non_recurrent_count: Number of non-recurrent events in the output
        - output_path: Path to the created output file
    
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input file does not contain the 'is_recurrent' column.
        RuntimeError: If the output file exists and force is False.
    """
    input_path = input_path or INPUT_FILE
    output_path = output_path or OUTPUT_FILE
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if input file exists
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Check if output file exists and force is False
    if output_path.exists() and not force:
        raise RuntimeError(
            f"Output file already exists: {output_path}. "
            "Use force=True to overwrite."
        )
    
    logger.info(f"Reading input file: {input_path}")
    df = pd.read_csv(input_path)
    
    # Validate required column exists
    if 'is_recurrent' not in df.columns:
        raise ValueError(
            f"Input file does not contain the 'is_recurrent' column. "
            f"Available columns: {list(df.columns)}"
        )
    
    total_input = len(df)
    
    # Filter non-recurrent events (is_recurrent == False or is_recurrent is null/NaN)
    # The task requires filtering OUT recurrent storms, keeping only non-recurrent ones
    non_recurrent_df = df[~df['is_recurrent'].astype(bool)]
    
    recurrent_count = total_input - len(non_recurrent_df)
    non_recurrent_count = len(non_recurrent_df)
    
    logger.info(f"Input dataset: {total_input} events")
    logger.info(f"Recurrent events filtered out: {recurrent_count}")
    logger.info(f"Non-recurrent events in output: {non_recurrent_count}")
    
    if non_recurrent_count == 0:
        logger.warning("No non-recurrent events found in the input dataset!")
    
    # Write the filtered dataset
    logger.info(f"Writing output file: {output_path}")
    non_recurrent_df.to_csv(output_path, index=False)
    
    # Compute and log a simple checksum for verification
    import hashlib
    with open(output_path, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    logger.info(f"Output file checksum (SHA-256): {file_hash}")
    
    return {
        "total_input": total_input,
        "recurrent_count": recurrent_count,
        "non_recurrent_count": non_recurrent_count,
        "output_path": str(output_path),
        "checksum": file_hash
    }

def main():
    """
    Command-line interface for filtering non-recurrent storms.
    
    Usage:
        python code/filter_analysis_subset.py [--input PATH] [--output PATH] [--force]
    """
    parser = argparse.ArgumentParser(
        description="Filter non-recurrent storms from the primary aligned events dataset "
                    "to create an analysis subset for correlation analysis."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=str(INPUT_FILE),
        help=f"Path to the input aligned events CSV (default: {INPUT_FILE})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_FILE),
        help=f"Path to the output analysis subset CSV (default: {OUTPUT_FILE})"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the output file if it exists"
    )
    
    args = parser.parse_args()
    
    try:
        result = filter_non_recurrent_storms(
            input_path=Path(args.input),
            output_path=Path(args.output),
            force=args.force
        )
        
        logger.info("Filtering completed successfully!")
        logger.info(f"Statistics: {result}")
        
        # Print summary to stdout for pipeline consumption
        print(f"SUCCESS: Created analysis subset with {result['non_recurrent_count']} non-recurrent events.")
        print(f"Output file: {result['output_path']}")
        print(f"Checksum: {result['checksum']}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 2
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        return 3
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 99

if __name__ == "__main__":
    sys.exit(main())