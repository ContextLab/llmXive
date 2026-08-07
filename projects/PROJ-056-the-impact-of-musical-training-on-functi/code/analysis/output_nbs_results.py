"""
Output module for Network-Based Statistic (NBS) results.

This module handles the loading of NBS analysis results and writing them
to the specified CSV output file as per Task T031.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger
from utils.memory_monitor import check_memory_limit

logger = get_logger(__name__)

# Output path definition as per task requirements
OUTPUT_PATH = Path("data/processed/nbs_results.csv")

def load_nbs_results(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load NBS results from a temporary or specified input file.

    The run_nbs.py script is expected to write intermediate results to a
    temporary location or standard output that can be captured here.
    For this implementation, we assume the run_nbs module has already
    executed and produced a standard CSV structure, or we load from
    a known intermediate file if the pipeline is sequential.

    In a strict pipeline, this might read from a temporary file generated
    by `run_nbs_analysis` before finalizing.
    """
    if input_path:
        path = Path(input_path)
    else:
        # Default intermediate path if not specified
        # In a real pipeline, this might be passed via a queue or temp file
        path = Path("data/processed/nbs_intermediate.csv")

    if not path.exists():
        raise FileNotFoundError(f"NBS intermediate results not found at {path}. "
                                "Ensure run_nbs.py has been executed successfully.")

    logger.info(f"Loading NBS results from {path}")
    df = pd.read_csv(path)

    # Validate expected columns
    required_cols = ['component_id', 'size_edges', 'p_value_fwer']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"NBS results missing required columns: {missing}")

    check_memory_limit()
    return df

def write_nbs_results(df: pd.DataFrame, output_path: Optional[str] = None) -> None:
    """
    Write the NBS results to the final output CSV.

    Args:
        df: DataFrame containing NBS results with columns:
            component_id, size_edges, p_value_fwer
        output_path: Optional path to write to. Defaults to task requirement.
    """
    target = Path(output_path) if output_path else OUTPUT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing NBS results to {target}")
    df.to_csv(target, index=False)
    logger.info(f"Successfully wrote {len(df)} components to {target}")

def main():
    """
    Entry point for the NBS output module.

    This script is designed to be run after the NBS analysis (T029a)
    has completed and generated intermediate results. It loads those
    results, performs a final validation, and writes the final
    `data/processed/nbs_results.csv`.
    """
    try:
        # Check memory before processing
        check_memory_limit()

        # Load results (assumes run_nbs.py wrote to intermediate or we read from a temp file)
        # Since run_nbs.py is a separate module, we assume it leaves a file or we
        # can import its result if called programmatically.
        # For this standalone script, we expect the intermediate file to exist.
        df = load_nbs_results()

        # Ensure data types are correct
        df['component_id'] = df['component_id'].astype(int)
        df['size_edges'] = df['size_edges'].astype(int)
        df['p_value_fwer'] = df['p_value_fwer'].astype(float)

        # Write final output
        write_nbs_results(df)

        logger.info("NBS results output task completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        logger.error("Did you run code/analysis/run_nbs.py first?")
        raise
    except Exception as e:
        logger.error(f"Error processing NBS results: {e}")
        raise

if __name__ == "__main__":
    main()