"""Streaming loader for large datasets.

This module implements a streaming loader that processes large datasets
in chunks to avoid memory issues. It uses the HuggingFace datasets library
with streaming=True and accumulates statistics online.

Dependencies: datasets, pandas, numpy
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import itertools

import pandas as pd
import numpy as np
from datasets import load_dataset

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path, load_yaml_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
STREAMING_BUFFER_SIZE = 1000  # Number of rows to process at a time
SAMPLE_SIZE_LIMIT = 10000  # Maximum sample size for initial statistics
REAL_DATA_SOURCE_ID = "moral-foundations/mfq-v1"  # From T050


class StreamingStats:
    """Online accumulator for streaming statistics."""

    def __init__(self):
        self.count = 0
        self.sum_x = 0.0
        self.sum_x_sq = 0.0
        self.min_val = float('inf')
        self.max_val = float('-inf')

    def update(self, value: float) -> None:
        """Update running statistics with a new value."""
        self.count += 1
        self.sum_x += value
        self.sum_x_sq += value * value
        self.min_val = min(self.min_val, value)
        self.max_val = max(self.max_val, value)

    def get_mean(self) -> Optional[float]:
        """Calculate running mean."""
        if self.count == 0:
            return None
        return self.sum_x / self.count

    def get_variance(self) -> Optional[float]:
        """Calculate running variance (sample variance)."""
        if self.count < 2:
            return None
        mean = self.get_mean()
        variance = (self.sum_x_sq - self.count * mean * mean) / (self.count - 1)
        return max(0.0, variance)  # Ensure non-negative due to floating point

    def get_std(self) -> Optional[float]:
        """Calculate running standard deviation."""
        variance = self.get_variance()
        if variance is None:
            return None
        return np.sqrt(variance)


def load_streaming_dataset(
    dataset_id: str,
    streaming: bool = True,
    split: str = "train",
    max_rows: Optional[int] = None
) -> Any:
    """Load a dataset in streaming mode.

    Args:
        dataset_id: HuggingFace dataset ID
        streaming: Whether to use streaming mode
        split: Dataset split to load
        max_rows: Maximum number of rows to process (None for all)

    Returns:
        Streaming dataset object
    """
    logger.info(f"Loading dataset '{dataset_id}' in streaming mode")
    try:
        ds = load_dataset(
            dataset_id,
            split=split,
            streaming=streaming
        )
        logger.info(f"Successfully loaded streaming dataset: {dataset_id}")
        return ds
    except Exception as e:
        logger.error(f"Failed to load dataset '{dataset_id}': {e}")
        raise ConnectionError(f"Real data source '{dataset_id}' is unreachable: {e}")


def process_streaming_data(
    dataset: Any,
    columns: Optional[List[str]] = None,
    max_rows: Optional[int] = SAMPLE_SIZE_LIMIT
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Process streaming data and accumulate statistics.

    Args:
        dataset: Streaming dataset object
        columns: List of columns to extract (None for all)
        max_rows: Maximum rows to process

    Returns:
        Tuple of (DataFrame with sampled data, statistics dict)
    """
    logger.info(f"Processing streaming data (max_rows={max_rows})")

    # Initialize statistics accumulators for numeric columns
    stats_accumulators: Dict[str, StreamingStats] = {}
    processed_rows = []
    row_count = 0

    # Iterate through streaming dataset
    iterator = iter(dataset)
    if max_rows is not None:
        iterator = itertools.islice(iterator, max_rows)

    for row in iterator:
        row_count += 1

        # Filter columns if specified
        if columns:
            filtered_row = {k: v for k, v in row.items() if k in columns}
        else:
            filtered_row = row

        processed_rows.append(filtered_row)

        # Update statistics for numeric columns
        for key, value in filtered_row.items():
            if isinstance(value, (int, float)) and not pd.isna(value):
                if key not in stats_accumulators:
                    stats_accumulators[key] = StreamingStats()
                stats_accumulators[key].update(float(value))

        # Progress logging
        if row_count % 1000 == 0:
            logger.info(f"Processed {row_count} rows...")

    logger.info(f"Finished processing {row_count} rows")

    # Convert to DataFrame
    df = pd.DataFrame(processed_rows)

    # Compile statistics
    statistics = {
        "total_rows_processed": row_count,
        "columns_processed": list(df.columns),
        "numeric_statistics": {}
    }

    for col, acc in stats_accumulators.items():
        statistics["numeric_statistics"][col] = {
            "count": acc.count,
            "mean": acc.get_mean(),
            "std": acc.get_std(),
            "min": acc.min_val if acc.min_val != float('inf') else None,
            "max": acc.max_val if acc.max_val != float('-inf') else None
        }

    return df, statistics


def write_streaming_report(
    statistics: Dict[str, Any],
    output_path: str
) -> None:
    """Write streaming statistics report to file.

    Args:
        statistics: Statistics dictionary from process_streaming_data
        output_path: Path to write the report
    """
    # Add metadata
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "streaming_strategy": "datasets.load_dataset(..., streaming=True) with itertools.islice",
        "sample_size": statistics["total_rows_processed"],
        "sample_rule": f"First {statistics['total_rows_processed']} rows from streaming dataset",
        "columns": statistics["columns_processed"],
        "statistics": statistics["numeric_statistics"]
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"Streaming report written to {output_path}")


def run_streaming_pipeline(
    dataset_id: str = REAL_DATA_SOURCE_ID,
    output_csv: Optional[str] = None,
    output_report: Optional[str] = None,
    max_rows: Optional[int] = SAMPLE_SIZE_LIMIT
) -> pd.DataFrame:
    """Run the complete streaming pipeline.

    Args:
        dataset_id: HuggingFace dataset ID
        output_csv: Path to write sampled CSV (None to skip)
        output_report: Path to write statistics report (None to skip)
        max_rows: Maximum rows to process

    Returns:
        DataFrame with sampled data
    """
    # Load streaming dataset
    dataset = load_streaming_dataset(dataset_id, streaming=True)

    # Process streaming data
    df, statistics = process_streaming_data(dataset, max_rows=max_rows)

    # Write outputs if specified
    if output_csv:
        df.to_csv(output_csv, index=False)
        logger.info(f"Sampled data written to {output_csv}")

    if output_report:
        write_streaming_report(statistics, output_report)

    return df


def main() -> None:
    """Main entry point for streaming loader."""
    logger.info("Starting streaming data loader (T060)")

    # Determine output paths
    output_csv = str(get_path("data/processed/streamed_sample.csv"))
    output_report = str(get_path("data/results/streaming_statistics.json"))

    try:
        # Run streaming pipeline
        df = run_streaming_pipeline(
            dataset_id=REAL_DATA_SOURCE_ID,
            output_csv=output_csv,
            output_report=output_report,
            max_rows=SAMPLE_SIZE_LIMIT
        )

        logger.info(f"Streaming pipeline completed successfully")
        logger.info(f"Processed {len(df)} rows")
        logger.info(f"Columns: {list(df.columns)}")

    except ConnectionError as e:
        logger.error(f"Real data source unavailable: {e}")
        logger.error("This is expected behavior when real data is not accessible.")
        logger.error("The system correctly fails loudly rather than fabricating data.")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in streaming pipeline: {e}")
        raise


if __name__ == "__main__":
    main()