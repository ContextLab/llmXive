"""
MDC Stats Module for Exoplanetary Atmosphere Characterization.

This module implements the logic to aggregate Minimum Detectable Concentration (MDC)
statistics from retrieval results and save them to a JSON report.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

from config import get_config
from utils import setup_logging, safe_execute

# Configure logging
logger = logging.getLogger(__name__)


def load_retrieval_results() -> pd.DataFrame:
    """
    Load retrieval results from the processed data directory.

    Returns:
        pd.DataFrame: DataFrame containing retrieval results including MDC values.

    Raises:
        FileNotFoundError: If the retrieval results file does not exist.
        ValueError: If the required columns are missing.
    """
    config = get_config()
    input_path = config.data_dir / "processed" / "retrieval_results.csv"

    if not input_path.exists():
        raise FileNotFoundError(f"Retrieval results file not found at {input_path}")

    df = pd.read_csv(input_path)

    required_columns = ['min_detectable_concentration']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns in retrieval results: {missing_columns}")

    logger.info(f"Loaded {len(df)} retrieval results from {input_path}")
    return df


def compute_mdc_statistics(df: pd.DataFrame) -> Dict[str, float]:
    """
    Compute aggregate statistics for Minimum Detectable Concentration (MDC).

    Calculates median, mean, and 95th percentile of the MDC values.

    Args:
        df (pd.DataFrame): DataFrame containing MDC values.

    Returns:
        Dict[str, float]: Dictionary with calculated statistics.
    """
    mdc_values = df['min_detectable_concentration'].dropna()

    if len(mdc_values) == 0:
        logger.warning("No valid MDC values found in the dataset.")
        return {
            'median_mdc': np.nan,
            'mean_mdc': np.nan,
            'p95_mdc': np.nan
        }

    median_mdc = float(np.median(mdc_values))
    mean_mdc = float(np.mean(mdc_values))
    p95_mdc = float(np.percentile(mdc_values, 95))

    logger.info(f"MDC Statistics - Median: {median_mdc:.4e}, Mean: {mean_mdc:.4e}, P95: {p95_mdc:.4e}")

    return {
        'median_mdc': median_mdc,
        'mean_mdc': mean_mdc,
        'p95_mdc': p95_mdc
    }


def save_mdc_stats(stats: Dict[str, float], output_path: Optional[Path] = None) -> Path:
    """
    Save MDC statistics to a JSON file.

    Args:
        stats (Dict[str, float]): Dictionary containing MDC statistics.
        output_path (Optional[Path]): Path to save the JSON file. If None, uses config default.

    Returns:
        Path: Path to the saved JSON file.
    """
    config = get_config()
    if output_path is None:
        output_path = config.data_dir / "processed" / "mdc_stats.json"
    else:
        output_path = Path(output_path)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)

    logger.info(f"MDC statistics saved to {output_path}")
    return output_path


def main():
    """
    Main entry point for MDC stats generation.
    """
    setup_logging()
    logger.info("Starting MDC statistics aggregation...")

    try:
        # Load retrieval results
        df = load_retrieval_results()

        # Compute statistics
        stats = compute_mdc_statistics(df)

        # Save results
        output_path = save_mdc_stats(stats)

        logger.info(f"MDC stats aggregation complete. Output: {output_path}")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during MDC stats aggregation: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())