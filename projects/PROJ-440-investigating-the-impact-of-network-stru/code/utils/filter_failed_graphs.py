"""
Module to filter out failed graphs from datasets based on error logs.

This module provides functionality to read failed graph IDs from a log file
and filter them out from dataframes or CSV files.
"""

import logging
import argparse
from pathlib import Path
from typing import Set, List, Optional
import pandas as pd

logger = logging.getLogger(__name__)


def read_failed_graph_ids(log_path: str) -> Set[str]:
    """
    Read failed graph IDs from a log file.

    Args:
        log_path: Path to the log file containing failed graph entries.

    Returns:
        Set of graph IDs that failed.

    The log file format is expected to be:
        GRAPH_ID|ISO8601_TIMESTAMP|ERROR_TYPE|MESSAGE
    """
    failed_ids = set()
    log_file = Path(log_path)

    if not log_file.exists():
        logger.info(f"No failed graphs log found at {log_path}. Proceeding without filtering.")
        return failed_ids

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                parts = line.split('|')
                if len(parts) < 1:
                    logger.warning(f"Skipping malformed log entry at line {line_num}: {line}")
                    continue

                graph_id = parts[0].strip()
                if graph_id:
                    failed_ids.add(graph_id)

        logger.info(f"Read {len(failed_ids)} failed graph IDs from {log_path}")
        return failed_ids

    except Exception as e:
        logger.error(f"Error reading failed graphs log: {e}")
        raise


def filter_dataframe_by_ids(df: pd.DataFrame, failed_ids: Set[str], id_column: str = 'id') -> pd.DataFrame:
    """
    Filter a DataFrame to remove rows with failed graph IDs.

    Args:
        df: Input DataFrame.
        failed_ids: Set of graph IDs to filter out.
        id_column: Name of the column containing graph IDs (default: 'id').

    Returns:
        Filtered DataFrame without failed graph IDs.
    """
    if not failed_ids:
        return df

    if id_column not in df.columns:
        raise ValueError(f"Column '{id_column}' not found in DataFrame. Available columns: {list(df.columns)}")

    initial_count = len(df)
    filtered_df = df[~df[id_column].isin(failed_ids)]
    removed_count = initial_count - len(filtered_df)

    if removed_count > 0:
        logger.info(f"Filtered out {removed_count} rows with failed graph IDs")
    else:
        logger.info("No matching failed graph IDs found in DataFrame")

    return filtered_df


def apply_filter_to_csv(
    input_path: str,
    output_path: str,
    log_path: str,
    id_column: str = 'id'
) -> int:
    """
    Apply filtering to a CSV file based on failed graph IDs from a log.

    Args:
        input_path: Path to input CSV file.
        output_path: Path to write filtered CSV file.
        log_path: Path to log file containing failed graph IDs.
        id_column: Name of the column containing graph IDs (default: 'id').

    Returns:
        Number of rows removed.
    """
    # Read failed graph IDs
    failed_ids = read_failed_graph_ids(log_path)

    if not failed_ids:
        # No failed graphs, just copy the file
        logger.info("No failed graphs to filter. Copying input to output.")
        df = pd.read_csv(input_path)
        df.to_csv(output_path, index=False)
        return 0

    # Read input CSV
    df = pd.read_csv(input_path)
    logger.info(f"Read {len(df)} rows from {input_path}")

    # Filter out failed graphs
    filtered_df = filter_dataframe_by_ids(df, failed_ids, id_column)

    # Write filtered CSV
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(filtered_df)} rows to {output_path}")

    return len(df) - len(filtered_df)


def main():
    """Main entry point for filtering failed graphs."""
    parser = argparse.ArgumentParser(
        description='Filter failed graphs from a CSV based on error logs.'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to input CSV file'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Path to output filtered CSV file'
    )
    parser.add_argument(
        '--log',
        type=str,
        default='state/failedGraphs.log',
        help='Path to failed graphs log file (default: state/failedGraphs.log)'
    )
    parser.add_argument(
        '--id-column',
        type=str,
        default='id',
        help='Name of the column containing graph IDs (default: id)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    try:
        removed_count = apply_filter_to_csv(
            args.input,
            args.output,
            args.log,
            args.id_column
        )
        logger.info(f"Filtering complete. Removed {removed_count} rows.")
        return 0
    except Exception as e:
        logger.error(f"Filtering failed: {e}")
        return 1


if __name__ == '__main__':
    exit(main())