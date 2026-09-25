"""
Task T030: Calculate Cross-Cohort Replication Rate.

This module aggregates replication status counts from the validation results
and calculates the percentage of significant taxa that are 'replicated'.
"""
import argparse
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

# Import logger utility from the project's shared utils
try:
    from src.utils.logger import get_logger
except ImportError:
    # Fallback for direct execution if src is not in path during local dev
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.utils.logger import get_logger


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parents[3]


def load_replication_status(input_path: Path) -> pd.DataFrame:
    """
    Load the replication status TSV file.

    Args:
        input_path: Path to the replication_status.tsv file.

    Returns:
        DataFrame containing replication status data.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or lacks required columns.
    """
    logger = get_logger(__name__)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading replication status from {input_path}")
    
    try:
        df = pd.read_csv(input_path, sep='\t')
    except Exception as e:
        raise ValueError(f"Failed to read TSV file: {e}")
    
    if df.empty:
        raise ValueError("Replication status file is empty.")
    
    required_cols = ['replication_status']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    return df


def calculate_replication_rate(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate the replication rate based on significant taxa.

    Logic:
    1. Filter for significant taxa (q < 0.05). The input file from T029
       is expected to only contain significant taxa (q < 0.05) as per the
       task description: "Aggregate replication_status counts. Calculate the
       percentage of significant taxa (q < 0.05) that are 'replicated'..."
       However, to be robust, we assume the input file contains the relevant
       significant taxa. If the input file contains non-significant taxa,
       we would need a 'q_value' column to filter. The T029 schema description
       says "filtered for q < 0.05" for the input diff_abundance files, and
       the output schema for T029 includes 'agp_q_value' and 'ukbb_q_value'.
       We will assume the input T029 output is already filtered as per T029
       description: "Flag consistent directionality... Output: ... containing ...
       (filtered for q < 0.05)".
       Wait, T029 description says: "Compare ... for significant taxa ... Output:
       ... (filtered for q < 0.05)". So the input to T030 should already be filtered.
       We will proceed with the assumption that all rows in the input are significant.

    2. Count total rows (total_significant_taxa).
    3. Count rows where replication_status == 'replicated'.
    4. Calculate rate = (replicated_count / total) * 100.

    Args:
        df: DataFrame with 'replication_status' column.

    Returns:
        Dictionary with counts and rate.
    """
    logger = get_logger(__name__)

    total_significant = len(df)
    
    if total_significant == 0:
        logger.warning("No significant taxa found in input. Rate is 0.")
        return {
            'total_significant_taxa': 0,
            'replicated_count': 0,
            'replication_rate': 0.0
        }

    replicated_count = len(df[df['replication_status'] == 'replicated'])
    replication_rate = (replicated_count / total_significant) * 100.0

    logger.info(f"Total significant taxa: {total_significant}")
    logger.info(f"Replicated count: {replicated_count}")
    logger.info(f"Replication rate: {replication_rate:.2f}%")

    return {
        'total_significant_taxa': total_significant,
        'replicated_count': replicated_count,
        'replication_rate': replication_rate
    }


def write_replication_rate_report(metrics: Dict[str, Any], output_path: Path) -> None:
    """
    Write the replication rate metrics to a TSV file.

    Args:
        metrics: Dictionary containing the calculated metrics.
        output_path: Path to the output file.
    """
    logger = get_logger(__name__)
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df_output = pd.DataFrame([metrics])
    
    logger.info(f"Writing replication rate report to {output_path}")
    df_output.to_csv(output_path, sep='\t', index=False)


def run_replication_rate_analysis(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> None:
    """
    Main execution function for T030.

    Args:
        input_path: Path to replication_status.tsv. Defaults to project standard.
        output_path: Path to replication_rate.tsv. Defaults to project standard.
    """
    project_root = get_project_root()
    
    if input_path is None:
        input_path = project_root / "data" / "processed" / "results" / "replication_status.tsv"
    
    if output_path is None:
        output_path = project_root / "data" / "processed" / "results" / "replication_rate.tsv"

    logger = get_logger(__name__)
    logger.info("Starting T030: Calculate Cross-Cohort Replication Rate")
    
    try:
        # 1. Load data
        df = load_replication_status(input_path)
        
        # 2. Calculate metrics
        metrics = calculate_replication_rate(df)
        
        # 3. Write output
        write_replication_rate_report(metrics, output_path)
        
        logger.info("T030 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        raise


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the argument parser for CLI execution."""
    parser = argparse.ArgumentParser(
        description="Calculate Cross-Cohort Replication Rate (T030)"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to replication_status.tsv (default: data/processed/results/replication_status.tsv)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to replication_rate.tsv (default: data/processed/results/replication_rate.tsv)"
    )
    return parser


def main() -> int:
    """Entry point for CLI execution."""
    parser = build_arg_parser()
    args = parser.parse_args()
    
    # Configure logging
    logger = get_logger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        run_replication_rate_analysis(
            input_path=args.input,
            output_path=args.output
        )
        return 0
    except Exception as e:
        logging.error(f"Task failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
