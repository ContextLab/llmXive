import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MIN_WORD_THRESHOLD = 5
RATING_COLUMN = 'authenticity_score'
TEXT_COLUMN = 'text_content'


def detect_empty_or_short_texts(df: pd.DataFrame, min_words: int = MIN_WORD_THRESHOLD) -> Tuple[pd.DataFrame, List[int]]:
    """
    Detect rows where the text content is empty or has fewer than `min_words`.

    Args:
        df: Input DataFrame containing text data.
        min_words: Minimum number of words required for a text to be considered valid.

    Returns:
        Tuple of (DataFrame with valid texts, list of indices of excluded rows).
    """
    if TEXT_COLUMN not in df.columns:
        logger.warning(f"Column '{TEXT_COLUMN}' not found in DataFrame. Skipping text length check.")
        return df, []

    def count_words(text):
        if pd.isna(text) or not isinstance(text, str):
            return 0
        return len(str(text).split())

    word_counts = df[TEXT_COLUMN].apply(count_words)
    excluded_indices = df.index[word_counts < min_words].tolist()
    valid_df = df.drop(index=excluded_indices)

    logger.info(f"Detected {len(excluded_indices)} rows with text length < {min_words} words.")
    return valid_df, excluded_indices


def detect_missing_ratings(df: pd.DataFrame, rating_col: str = RATING_COLUMN) -> Tuple[pd.DataFrame, List[int]]:
    """
    Detect rows where the rating column has missing (NaN) values.

    Args:
        df: Input DataFrame containing rating data.
        rating_col: Name of the column containing authenticity scores.

    Returns:
        Tuple of (DataFrame with valid ratings, list of indices of excluded rows).
    """
    if rating_col not in df.columns:
        logger.warning(f"Column '{rating_col}' not found in DataFrame. Skipping missing rating check.")
        return df, []

    missing_mask = df[rating_col].isna()
    excluded_indices = df.index[missing_mask].tolist()
    valid_df = df.drop(index=excluded_indices)

    logger.info(f"Detected {len(excluded_indices)} rows with missing '{rating_col}'.")
    return valid_df, excluded_indices


def log_exclusions(exclusions: Dict[str, List[int]], log_path: Optional[Path] = None) -> None:
    """
    Log exclusion details to a file and the console.

    Args:
        exclusions: Dictionary mapping exclusion reasons to lists of row indices.
        log_path: Optional path to write the log file. If None, logs to console only.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_content = [
        f"Edge Case Exclusion Log - {timestamp}",
        "=" * 50
    ]

    for reason, indices in exclusions.items():
        log_content.append(f"\n{reason}:")
        log_content.append(f"  Count: {len(indices)}")
        if indices:
            log_content.append(f"  Indices: {indices[:10]}{'...' if len(indices) > 10 else ''}")

    log_text = "\n".join(log_content)
    logger.info(log_text)

    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(log_text)
        logger.info(f"Exclusion log written to: {log_path}")


def handle_edge_cases(
    df: pd.DataFrame,
    min_words: int = MIN_WORD_THRESHOLD,
    rating_col: str = RATING_COLUMN,
    log_path: Optional[Path] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Main entry point to handle edge cases:
    1. Detect and remove empty/short texts.
    2. Detect and remove rows with missing ratings (listwise deletion).
    3. Log all exclusions.

    Args:
        df: Input DataFrame.
        min_words: Minimum word count threshold.
        rating_col: Column name for ratings.
        log_path: Optional path to write exclusion log.

    Returns:
        Tuple of (cleaned DataFrame, summary statistics dictionary).
    """
    initial_count = len(df)
    exclusions = {}

    # Step 1: Handle short texts
    df_filtered, short_indices = detect_empty_or_short_texts(df, min_words)
    if short_indices:
        exclusions['short_text'] = short_indices
        df = df_filtered

    # Step 2: Handle missing ratings (Listwise Deletion)
    df_clean, missing_indices = detect_missing_ratings(df, rating_col)
    if missing_indices:
        exclusions['missing_ratings'] = missing_indices
        df = df_clean

    # Log exclusions
    if exclusions:
        log_exclusions(exclusions, log_path)
    else:
        logger.info("No edge cases detected. All rows passed validation.")

    # Summary
    summary = {
        'initial_rows': initial_count,
        'final_rows': len(df),
        'rows_dropped': initial_count - len(df),
        'exclusions': {k: len(v) for k, v in exclusions.items()},
        'exclusion_details': exclusions
    }

    logger.info(f"Edge case handling complete. Dropped {summary['rows_dropped']} rows. Final sample size: {summary['final_rows']}")
    return df, summary


def get_exclusion_summary(summary: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary string of the edge case handling.

    Args:
        summary: The summary dictionary returned by handle_edge_cases.

    Returns:
        Formatted summary string.
    """
    lines = [
        "=== Edge Case Handling Summary ===",
        f"Initial Sample Size: {summary['initial_rows']}",
        f"Final Sample Size: {summary['final_rows']}",
        f"Total Rows Dropped: {summary['rows_dropped']}",
        "Breakdown of Exclusions:"
    ]
    for reason, count in summary['exclusions'].items():
        lines.append(f"  - {reason}: {count}")
    return "\n".join(lines)


def main():
    """
    CLI entry point for testing the edge case handler.
    Expects a CSV file path as the first argument.
    """
    if len(sys.argv) < 2:
        print("Usage: python edge_case_handler.py <path_to_csv> [--log <path>]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    log_path = None
    if len(sys.argv) >= 4 and sys.argv[2] == '--log':
        log_path = Path(sys.argv[3])

    if not input_path.exists():
        logger.error(f"File not found: {input_path}")
        sys.exit(1)

    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")

        cleaned_df, summary = handle_edge_cases(df, log_path=log_path)
        print(get_exclusion_summary(summary))

        if len(cleaned_df) == 0:
            logger.warning("Resulting dataset is empty after edge case handling.")
        else:
            # Optional: save cleaned data if needed
            # output_path = input_path.with_name(f"{input_path.stem}_cleaned.csv")
            # cleaned_df.to_csv(output_path, index=False)
            pass

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()