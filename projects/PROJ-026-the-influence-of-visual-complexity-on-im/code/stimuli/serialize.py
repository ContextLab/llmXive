import os
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_project_root, get_data_path
from utils.logging import get_logger
from stimuli.process import categorize_complexity

logger = get_logger(__name__)


def load_raw_complexity_scores(
    raw_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Load raw complexity scores from CSV.

    Args:
        raw_path: Path to raw CSV file

    Returns:
        DataFrame with raw complexity scores
    """
    if raw_path is None:
        root = get_project_root()
        raw_path = root / "data" / "processed" / "complexity_scores_raw.csv"

    if not raw_path.exists():
        raise FileNotFoundError(f"Raw complexity scores not found: {raw_path}")

    logger.info(f"Loading raw complexity scores from {raw_path}")
    return pd.read_csv(raw_path)


def apply_categorization(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Apply complexity categorization to DataFrame.

    Args:
        df: DataFrame with complexity metrics

    Returns:
        DataFrame with complexity_category column added
    """
    categorized_df, thresholds = categorize_complexity(df)
    return categorized_df


def save_final_csv(
    df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> None:
    """
    Save final complexity scores to CSV.

    Args:
        df: DataFrame with categorized complexity scores
        output_path: Path to save final CSV
    """
    if output_path is None:
        root = get_project_root()
        output_path = root / "data" / "processed" / "complexity_scores.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved final complexity scores to {output_path}")


def main() -> None:
    """Main entry point for serialization."""
    root = get_project_root()

    raw_path = root / "data" / "processed" / "complexity_scores_raw.csv"
    final_path = root / "data" / "processed" / "complexity_scores.csv"

    if not raw_path.exists():
        logger.error(f"Raw complexity scores not found: {raw_path}")
        return

    # Load raw scores
    df_raw = load_raw_complexity_scores(raw_path)

    # Apply categorization
    df_final = apply_categorization(df_raw)

    # Save final CSV
    save_final_csv(df_final, final_path)

    logger.info("Serialization complete.")


if __name__ == "__main__":
    main()
