"""
Streaming loader for large datasets (T060).

Implements memory-safe processing of large datasets using the HuggingFace
`datasets` library in streaming mode. Accumulates statistics online (running
mean, variance, count) without loading the full dataset into memory.

Constraints:
- Uses `datasets.load_dataset(..., streaming=True)`
- Accumulates statistics online (Welford's algorithm for variance)
- Logs sample size and streaming strategy
- Fails loudly if the real source is unreachable (no synthetic fallback)
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import from project config
from code.config import get_path, DATA_MODE, load_yaml_config

# Import real data verification logic
from code.data.verify_data_source import check_huggingface_reachability, check_osf_reachability

# Setup logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Constants
HF_DATASET_ID = "moral-foundations/mfq-v1"  # As defined in T050
OSF_BASE_URL = "https://osf.io/api/v1"       # As defined in T050
STREAMING_OUTPUT_PATH = "data/processed/streaming_stats.json"
STREAMING_LOG_PATH = "data/logs/streaming_run.log"


class StreamingStats:
    """
    Online statistics accumulator using Welford's algorithm.
    
    Computes running mean, variance, min, max, and count for numeric columns
    without storing all values in memory.
    """
    def __init__(self, columns: List[str]):
        self.columns = columns
        self.count = 0
        self.mean: Dict[str, float] = {col: 0.0 for col in columns}
        self.M2: Dict[str, float] = {col: 0.0 for col in columns}
        self.min_val: Dict[str, float] = {col: float('inf') for col in columns}
        self.max_val: Dict[str, float] = {col: float('-inf') for col in columns}
        self.total_rows_processed = 0

    def update(self, row: Dict[str, Any]) -> None:
        """Update statistics with a single row."""
        self.total_rows_processed += 1
        for col in self.columns:
            if col not in row:
                continue
            val = row[col]
            if not isinstance(val, (int, float)) or val is None:
                continue
            
            val = float(val)
            self.count += 1
            
            # Welford's algorithm for online mean/variance
            delta = val - self.mean[col]
            self.mean[col] += delta / self.count
            delta2 = val - self.mean[col]
            self.M2[col] += delta * delta2
            
            # Min/Max
            if val < self.min_val[col]:
                self.min_val[col] = val
            if val > self.max_val[col]:
                self.max_val[col] = val

    def get_variance(self) -> Dict[str, float]:
        """Calculate variance from M2."""
        if self.count < 2:
            return {col: 0.0 for col in self.columns}
        return {col: self.M2[col] / (self.count - 1) for col in self.columns}

    def get_std(self) -> Dict[str, float]:
        """Calculate standard deviation."""
        variance = self.get_variance()
        return {col: variance[col] ** 0.5 for col in self.columns}

    def to_dict(self) -> Dict[str, Any]:
        """Serialize statistics to a dictionary."""
        return {
            "total_rows_processed": self.total_rows_processed,
            "numeric_count": self.count,
            "mean": self.mean,
            "std": self.get_std(),
            "min": self.min_val,
            "max": self.max_val,
            "timestamp": datetime.utcnow().isoformat(),
            "strategy": "streaming_online_accumulation"
        }


def load_streaming_dataset(dataset_id: str, streaming: bool = True) -> Any:
    """
    Load a dataset in streaming mode.
    
    Args:
        dataset_id: HuggingFace dataset ID
        streaming: If True, use streaming mode
        
    Returns:
        StreamingDataset object
        
    Raises:
        ConnectionError: If the dataset source is unreachable
        ImportError: If the datasets library is not installed
    """
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("The 'datasets' library is not installed. Please run: pip install datasets")
        raise

    # Verify source reachability before attempting load
    if "hf://" in dataset_id or dataset_id.startswith("moral-foundations"):
        if not check_huggingface_reachability():
            raise ConnectionError(
                f"HuggingFace source for '{dataset_id}' is unreachable. "
                "Cannot proceed with real data loading."
            )
    
    logger.info(f"Loading dataset '{dataset_id}' in streaming mode...")
    
    try:
        dataset = load_dataset(dataset_id, streaming=streaming)
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset '{dataset_id}': {e}")
        raise ConnectionError(
            f"Failed to load real dataset '{dataset_id}'. "
            "This is a real data failure. No synthetic fallback allowed."
        ) from e


def process_streaming_data(
    dataset: Any, 
    columns_to_analyze: List[str],
    max_samples: Optional[int] = None
) -> StreamingStats:
    """
    Process streaming data and accumulate statistics.
    
    Args:
        dataset: Streaming dataset object
        columns_to_analyze: List of column names to compute stats for
        max_samples: Optional limit on number of samples to process
        
    Returns:
        StreamingStats object with accumulated statistics
    """
    stats = StreamingStats(columns_to_analyze)
    
    logger.info(f"Starting streaming processing for columns: {columns_to_analyze}")
    
    processed_count = 0
    for batch_idx, batch in enumerate(dataset):
        if max_samples and processed_count >= max_samples:
            break
        
        # Handle batched data (list of dicts) or single dict
        if isinstance(batch, dict) and any(isinstance(v, list) for v in batch.values()):
            # It's a batched dataset
            length = len(next(iter(batch.values())))
            for i in range(length):
                if max_samples and processed_count >= max_samples:
                    break
                row = {k: v[i] for k, v in batch.items()}
                stats.update(row)
                processed_count += 1
        else:
            # Single row
            stats.update(batch)
            processed_count += 1
        
        if batch_idx % 100 == 0:
            logger.debug(f"Processed {processed_count} rows...")

    logger.info(f"Finished processing {processed_count} rows.")
    return stats


def write_streaming_report(stats: StreamingStats, output_path: str) -> None:
    """
    Write streaming statistics to a JSON report.
    
    Args:
        stats: StreamingStats object
        output_path: Path to write the report
    """
    report = stats.to_dict()
    report["dataset_id"] = HF_DATASET_ID
    report["mode"] = DATA_MODE
    
    full_path = get_path(output_path)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Streaming report written to {full_path}")


def run_streaming_pipeline(
    dataset_id: str = HF_DATASET_ID,
    columns: Optional[List[str]] = None,
    max_samples: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run the full streaming pipeline.
    
    Args:
        dataset_id: Dataset ID to load
        columns: Columns to analyze (defaults to common MFQ columns)
        max_samples: Max samples to process (None = all)
        
    Returns:
        Dictionary of results
    """
    if columns is None:
        # Default columns for MFQ analysis
        columns = ["care", "fairness", "loyalty", "authority", "purity", "total_score"]
    
    # 1. Load dataset in streaming mode
    dataset = load_streaming_dataset(dataset_id)
    
    # 2. Process streaming data
    stats = process_streaming_data(dataset, columns, max_samples)
    
    # 3. Write report
    write_streaming_report(stats, STREAMING_OUTPUT_PATH)
    
    return stats.to_dict()


def main() -> None:
    """Main entry point for T060 streaming loader."""
    logger.info("Starting T060: Streaming Loader Pipeline")
    logger.info(f"Data Mode: {DATA_MODE}")
    
    # Verify we are in a mode that allows real data processing
    # T095/T096 gates should have run before this, but double-check
    if DATA_MODE == 'real':
        logger.info("Running in REAL mode. Verifying data source...")
        # The load_streaming_dataset function will raise if source is unreachable
    
    try:
        results = run_streaming_pipeline(
            dataset_id=HF_DATASET_ID,
            columns=["care", "fairness", "loyalty", "authority", "purity", "total_score"],
            max_samples=None  # Process full dataset (or as much as streaming allows)
        )
        
        logger.info("Streaming pipeline completed successfully.")
        logger.info(f"Total rows processed: {results['total_rows_processed']}")
        logger.info(f"Numeric values processed: {results['numeric_count']}")
        
        # Log the strategy used for reproducibility
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": "T060",
            "dataset_id": HF_DATASET_ID,
            "strategy": "streaming_online_accumulation",
            "rows_processed": results['total_rows_processed'],
            "columns_analyzed": ["care", "fairness", "loyalty", "authority", "purity", "total_score"]
        }
        
        log_path = get_path(STREAMING_LOG_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
            
        logger.info(f"Execution log written to {log_path}")
        
    except ConnectionError as e:
        logger.error(f"CRITICAL: Real data source unreachable. {e}")
        logger.error("Failing loudly as per constraint: no synthetic fallback allowed.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()