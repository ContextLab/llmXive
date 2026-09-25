"""
Keyword-based classification for code generation detection.

Implements FR-002 and FR-015:
- Loads keywords from code/labeling/keywords.yaml
- Applies case-insensitive matching
- Uses >= 2 threshold rule for classification
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import yaml

from code.utils.logger import get_logger

logger = get_logger(__name__)


def load_keywords(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load keyword configuration from YAML file.

    Args:
        config_path: Path to keywords.yaml. Defaults to code/labeling/keywords.yaml.

    Returns:
        Dictionary containing keywords list, threshold, and case_insensitive flag.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If configuration is malformed.
    """
    if config_path is None:
        config_path = "code/labeling/keywords.yaml"

    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Keyword config not found at {config_path}")

    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Validate required fields
    if 'keywords' not in config:
        raise ValueError("Configuration must contain 'keywords' list")
    if 'classification_threshold' not in config:
        raise ValueError("Configuration must contain 'classification_threshold'")
    if 'case_insensitive' not in config:
        raise ValueError("Configuration must contain 'case_insensitive' flag")

    return config


def count_keyword_matches(text: str, keywords: List[str], case_insensitive: bool = True) -> int:
    """
    Count occurrences of keywords in text.

    Args:
        text: The text to search (e.g., commit message).
        keywords: List of keywords to match.
        case_insensitive: Whether to ignore case when matching.

    Returns:
        Total count of keyword occurrences in the text.
    """
    if not text or not isinstance(text, str):
        return 0

    search_text = text.lower() if case_insensitive else text
    count = 0

    for keyword in keywords:
        search_keyword = keyword.lower() if case_insensitive else keyword
        # Count all occurrences of the keyword in the text
        count += search_text.count(search_keyword)

    return count


def classify_pr(
    row: pd.Series,
    keywords: List[str],
    threshold: int,
    case_insensitive: bool = True,
    message_column: str = "commit_message"
) -> Tuple[bool, int]:
    """
    Classify a single PR/commit as LLM-generated based on keyword matching.

    FR-002: A commit is classified as LLM-generated if the commit message
    contains at least `threshold` occurrences of keywords from the list.

    Args:
        row: A pandas Series representing a single record.
        keywords: List of LLM-associated keywords.
        threshold: Minimum number of keyword matches required.
        case_insensitive: Whether matching should be case-insensitive.
        message_column: Name of the column containing commit message.

    Returns:
        Tuple of (is_llm_generated: bool, match_count: int).
    """
    if message_column not in row.index:
        logger.warning(f"Column '{message_column}' not found in row, assuming no match")
        return False, 0

    message = row[message_column]
    match_count = count_keyword_matches(message, keywords, case_insensitive)
    is_llm_generated = match_count >= threshold

    return is_llm_generated, match_count


def classify_dataset(
    df: pd.DataFrame,
    config: Optional[Dict[str, Any]] = None,
    config_path: Optional[str] = None,
    message_column: str = "commit_message"
) -> pd.DataFrame:
    """
    Apply keyword-based classification to an entire dataset.

    Args:
        df: DataFrame containing PR/commit data with message_column.
        config: Optional pre-loaded configuration dict.
        config_path: Path to keywords.yaml if config not provided.
        message_column: Name of the column containing commit messages.

    Returns:
        DataFrame with two new columns:
        - 'is_llm_generated': Boolean indicating classification result.
        - 'keyword_match_count': Number of keyword matches found.

    Raises:
        FileNotFoundError: If config file not found and config not provided.
        ValueError: If configuration is invalid.
    """
    if config is None:
        config = load_keywords(config_path)

    keywords = config['keywords']
    threshold = config['classification_threshold']
    case_insensitive = config['case_insensitive']

    logger.info(f"Classifying dataset using {len(keywords)} keywords with threshold={threshold}")

    # Apply classification to each row
    results = df.apply(
        lambda row: classify_pr(
            row,
            keywords=keywords,
            threshold=threshold,
            case_insensitive=case_insensitive,
            message_column=message_column
        ),
        axis=1
    )

    # Unpack results into separate columns
    df['is_llm_generated'] = results.apply(lambda x: x[0])
    df['keyword_match_count'] = results.apply(lambda x: x[1])

    # Log classification summary
    llm_count = df['is_llm_generated'].sum()
    total_count = len(df)
    percentage = (llm_count / total_count * 100) if total_count > 0 else 0

    logger.info(f"Classification complete: {llm_count}/{total_count} ({percentage:.2f}%) classified as LLM-generated")

    return df


def main() -> None:
    """
    Main entry point for standalone execution.

    This function demonstrates the classification pipeline by:
    1. Loading a sample dataset (or using the one from fetch.py)
    2. Loading keywords from configuration
    3. Running classification
    4. Writing results to data/

    For integration, use classify_dataset() directly.
    """
    from code.data.fetch import fetch_dataset
    from code.utils.config import set_global_seed

    set_global_seed(42)

    logger.info("Starting keyword classification pipeline")

    # Load configuration
    config = load_keywords()
    logger.info(f"Loaded {len(config['keywords'])} keywords with threshold {config['classification_threshold']}")

    # Fetch dataset
    logger.info("Fetching dataset from HuggingFace...")
    df = fetch_dataset()

    if df is None or df.empty:
        logger.error("Dataset is empty, cannot proceed with classification")
        return

    # Run classification
    classified_df = classify_dataset(df, config)

    # Save results
    output_path = Path("data/classified_prs.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    classified_df.to_csv(output_path, index=False)
    logger.info(f"Classification results saved to {output_path}")

    # Print summary statistics
    logger.info(f"Total records: {len(classified_df)}")
    logger.info(f"LLM-generated: {classified_df['is_llm_generated'].sum()}")
    logger.info(f"Non-LLM: {len(classified_df) - classified_df['is_llm_generated'].sum()}")


if __name__ == "__main__":
    main()
