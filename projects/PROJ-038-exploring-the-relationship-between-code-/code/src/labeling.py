"""
Labeling module for Defects4J bug prediction research.

This module implements logic to cross-reference file paths with bug-introduction
commit metadata to assign binary 'is_buggy' labels to Java files.

Input: Defects4J commit JSON (schema: {"commit_hash": "str", "files": ["str"]})
Output: Binary label (1 if file in commit diff, 0 otherwise)

Dependencies:
- pandas for DataFrame manipulation
- json for parsing commit metadata
- pathlib for path handling
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LabelingError(Exception):
    """Custom exception for labeling-related errors."""
    pass


def load_commit_metadata(metadata_path: str) -> List[Dict[str, Any]]:
    """
    Load Defects4J commit metadata from a JSON file.

    Args:
        metadata_path: Path to the JSON file containing commit metadata.
                       Expected schema: [{"commit_hash": "str", "files": ["str"]}, ...]

    Returns:
        List of commit metadata dictionaries.

    Raises:
        LabelingError: If the file cannot be read or parsed.
    """
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise LabelingError(f"Expected a list of commits, got {type(data).__name__}")

        # Validate structure
        for i, commit in enumerate(data):
            if not isinstance(commit, dict):
                raise LabelingError(f"Commit {i} is not a dictionary")
            if 'commit_hash' not in commit:
                raise LabelingError(f"Commit {i} missing 'commit_hash'")
            if 'files' not in commit:
                raise LabelingError(f"Commit {i} missing 'files' list")
            if not isinstance(commit['files'], list):
                raise LabelingError(f"Commit {i} 'files' is not a list")

        logger.info(f"Loaded {len(data)} commit records from {metadata_path}")
        return data

    except FileNotFoundError:
        raise LabelingError(f"Commit metadata file not found: {metadata_path}")
    except json.JSONDecodeError as e:
        raise LabelingError(f"Failed to parse JSON in {metadata_path}: {e}")


def build_file_to_commit_map(commit_metadata: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
    """
    Build a mapping from file paths to the set of commit hashes that modified them.

    Args:
        commit_metadata: List of commit metadata dictionaries.

    Returns:
        Dictionary mapping file paths to sets of commit hashes.
    """
    file_to_commits: Dict[str, Set[str]] = {}

    for commit in commit_metadata:
        commit_hash = commit['commit_hash']
        files = commit['files']

        for file_path in files:
            # Normalize path separators for cross-platform consistency
            normalized_path = str(Path(file_path))
            if normalized_path not in file_to_commits:
                file_to_commits[normalized_path] = set()
            file_to_commits[normalized_path].add(commit_hash)

    logger.info(f"Built file-to-commit map with {len(file_to_commits)} unique files")
    return file_to_commits


def label_file(file_path: str, file_to_commit_map: Dict[str, Set[str]]) -> int:
    """
    Determine if a file is buggy based on whether it appears in any bug-introduction commit.

    Args:
        file_path: Path to the Java file.
        file_to_commit_map: Mapping from file paths to commit hashes.

    Returns:
        1 if the file was modified in a bug-introduction commit, 0 otherwise.
    """
    # Normalize path for comparison
    normalized_path = str(Path(file_path))

    if normalized_path in file_to_commit_map:
        return 1
    else:
        return 0


def label_dataframe(
    df: pd.DataFrame,
    commit_metadata: List[Dict[str, Any]],
    file_path_column: str = 'file_path'
) -> pd.DataFrame:
    """
    Add 'is_buggy' column to a DataFrame based on commit metadata.

    Args:
        df: DataFrame containing file paths (must have 'file_path' column).
        commit_metadata: List of commit metadata dictionaries.
        file_path_column: Name of the column containing file paths.

    Returns:
        DataFrame with added 'is_buggy' column.

    Raises:
        LabelingError: If required columns are missing.
    """
    if file_path_column not in df.columns:
        raise LabelingError(f"DataFrame missing required column: {file_path_column}")

    # Build the file-to-commit map
    file_to_commit_map = build_file_to_commit_map(commit_metadata)

    # Apply labeling
    logger.info(f"Labeling {len(df)} files based on {len(commit_metadata)} commits")
    df['is_buggy'] = df[file_path_column].apply(
        lambda path: label_file(path, file_to_commit_map)
    )

    # Log statistics
    buggy_count = df['is_buggy'].sum()
    clean_count = len(df) - buggy_count
    logger.info(f"Labeling complete: {buggy_count} buggy files, {clean_count} clean files")

    return df


def merge_metrics_and_labels(
    metrics_df: pd.DataFrame,
    commit_metadata_path: str,
    output_path: str
) -> pd.DataFrame:
    """
    Merge metrics DataFrame with bug labels and save to CSV.

    Args:
        metrics_df: DataFrame with computed metrics (LOC, CC, Halstead).
        commit_metadata_path: Path to the commit metadata JSON file.
        output_path: Path where the labeled DataFrame will be saved.

    Returns:
        The labeled DataFrame.

    Raises:
        LabelingError: If merging fails or output cannot be written.
    """
    # Load commit metadata
    commit_metadata = load_commit_metadata(commit_metadata_path)

    # Label the metrics DataFrame
    labeled_df = label_dataframe(metrics_df, commit_metadata)

    # Ensure 'is_buggy' is integer type
    labeled_df['is_buggy'] = labeled_df['is_buggy'].astype(int)

    # Save to CSV
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    labeled_df.to_csv(output_path, index=False)
    logger.info(f"Saved labeled features to {output_path}")

    return labeled_df


def main():
    """
    Main entry point for the labeling script.

    Expected environment:
    - FEATURES_CSV: Path to the metrics CSV file (default: code/data/processed/features_metrics.csv)
    - COMMIT_METADATA: Path to the commit metadata JSON (default: code/data/raw/defects4j_commits.json)
    - OUTPUT_CSV: Path for the labeled output (default: code/data/processed/features.csv)

    This script is designed to be called from the pipeline orchestration.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Label Java files with bug indicators based on Defects4J commit metadata.'
    )
    parser.add_argument(
        '--metrics-csv',
        type=str,
        default='code/data/processed/features_metrics.csv',
        help='Path to the metrics CSV file'
    )
    parser.add_argument(
        '--commit-metadata',
        type=str,
        default='code/data/raw/defects4j_commits.json',
        help='Path to the commit metadata JSON file'
    )
    parser.add_argument(
        '--output-csv',
        type=str,
        default='code/data/processed/features.csv',
        help='Path for the labeled output CSV'
    )

    args = parser.parse_args()

    try:
        # Load metrics
        logger.info(f"Loading metrics from {args.metrics_csv}")
        if not os.path.exists(args.metrics_csv):
            raise LabelingError(f"Metrics file not found: {args.metrics_csv}")

        metrics_df = pd.read_csv(args.metrics_csv)
        logger.info(f"Loaded {len(metrics_df)} rows from metrics CSV")

        # Check for required columns
        required_cols = ['file_path', 'cc', 'halstead', 'loc']
        missing_cols = [col for col in required_cols if col not in metrics_df.columns]
        if missing_cols:
            raise LabelingError(f"Metrics CSV missing required columns: {missing_cols}")

        # Perform labeling
        labeled_df = merge_metrics_and_labels(
            metrics_df,
            args.commit_metadata,
            args.output_csv
        )

        # Print summary
        print(f"Labeling complete. Output saved to: {args.output_csv}")
        print(f"Total files: {len(labeled_df)}")
        print(f"Buggy files (is_buggy=1): {labeled_df['is_buggy'].sum()}")
        print(f"Clean files (is_buggy=0): {len(labeled_df) - labeled_df['is_buggy'].sum()}")

        return 0

    except LabelingError as e:
        logger.error(f"Labeling error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during labeling: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
