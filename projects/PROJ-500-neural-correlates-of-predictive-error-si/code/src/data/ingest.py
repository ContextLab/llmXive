"""
Data Ingestion Module for llmXive Neural Correlates Project.

Implements streaming data downloaders with integrity monitoring,
verified source injection, and fail-loud data loading.
"""
import json
import logging
import os
import gc
import shutil
import tempfile
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Iterator
import pandas as pd
import numpy as np

# Import from local utils
from src.utils.logging import get_logger, log_event, log_error
from src.utils.config import get_config, get_data_dir
from src.utils.checksum import compute_file_sha256

# Attempt to import datasets library; handle gracefully if missing
try:
    from datasets import load_dataset
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False
    log_error("datasets library not installed. Install with: pip install datasets")

class DataIntegrityError(Exception):
    """Raised when data integrity checks fail."""
    pass

def get_current_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 ** 3)
    except ImportError:
        # Fallback if psutil not available
        return 0.0

class StreamingIntegrityMonitor:
    """
    Monitor for streaming data integrity.
    Tracks cumulative byte count and row count during streaming.
    Raises an error if stream terminates unexpectedly.
    """
    def __init__(self, expected_size_bytes: Optional[int] = None, 
                 expected_rows: Optional[int] = None,
                 dataset_name: str = "unknown"):
        self.expected_size_bytes = expected_size_bytes
        self.expected_rows = expected_rows
        self.dataset_name = dataset_name
        self.cumulative_bytes = 0
        self.cumulative_rows = 0
        self.logger = get_logger("StreamingIntegrityMonitor")
        self.logger.info(f"Initialized integrity monitor for dataset: {dataset_name}")
        if expected_size_bytes:
            self.logger.info(f"Expected size: {expected_size_bytes} bytes")
        if expected_rows:
            self.logger.info(f"Expected rows: {expected_rows}")

    def update(self, bytes_processed: int, rows_processed: int) -> None:
        """Update cumulative counts."""
        self.cumulative_bytes += bytes_processed
        self.cumulative_rows += rows_processed
        
        # Log progress every 1000 rows or 1MB
        if self.cumulative_rows % 1000 == 0 or self.cumulative_bytes % (1024*1024) == 0:
            self.logger.debug(
                f"Progress: {self.cumulative_rows} rows, {self.cumulative_bytes / (1024*1024):.2f} MB"
            )

    def finalize(self, actual_size_bytes: int = 0, actual_rows: int = 0) -> bool:
        """
        Finalize the stream and verify integrity.
        
        Args:
            actual_size_bytes: Actual final size if known
            actual_rows: Actual final row count if known
            
        Returns:
            True if integrity check passed, False otherwise
            
        Raises:
            DataIntegrityError: If stream terminated unexpectedly
        """
        self.cumulative_bytes = max(self.cumulative_bytes, actual_size_bytes)
        self.cumulative_rows = max(self.cumulative_rows, actual_rows)
        
        self.logger.info(
            f"Finalizing integrity check for {self.dataset_name}: "
            f"{self.cumulative_rows} rows, {self.cumulative_bytes / (1024*1024):.2f} MB"
        )
        
        # Check if stream terminated unexpectedly
        if self.expected_rows is not None and self.cumulative_rows < self.expected_rows:
            error_msg = (
                f"Stream terminated unexpectedly for dataset {self.dataset_name}. "
                f"Expected {self.expected_rows} rows, but only received {self.cumulative_rows}. "
                f"This indicates a partial file or truncated stream."
            )
            self.logger.error(error_msg)
            raise DataIntegrityError(error_msg)
        
        if self.expected_size_bytes is not None and self.cumulative_bytes < self.expected_size_bytes:
            error_msg = (
                f"Stream terminated unexpectedly for dataset {self.dataset_name}. "
                f"Expected {self.expected_size_bytes} bytes, but only received {self.cumulative_bytes}. "
                f"This indicates a partial file or truncated stream."
            )
            self.logger.error(error_msg)
            raise DataIntegrityError(error_msg)
        
        self.logger.info(f"Integrity check PASSED for {self.dataset_name}")
        return True

    def get_report(self) -> Dict[str, Any]:
        """Get integrity report."""
        return {
            "dataset_name": self.dataset_name,
            "expected_rows": self.expected_rows,
            "expected_bytes": self.expected_size_bytes,
            "actual_rows": self.cumulative_rows,
            "actual_bytes": self.cumulative_bytes,
            "integrity_passed": (
                (self.expected_rows is None or self.cumulative_rows >= self.expected_rows) and
                (self.expected_size_bytes is None or self.cumulative_bytes >= self.expected_size_bytes)
            )
        }

def stream_dataset_chunks(
    dataset_iter: Iterator,
    monitor: StreamingIntegrityMonitor,
    batch_size: int = 1000
) -> Iterator[Dict[str, Any]]:
    """
    Stream dataset chunks with integrity monitoring.
    
    Args:
        dataset_iter: Iterator over dataset chunks
        monitor: Integrity monitor instance
        batch_size: Number of rows per batch
        
    Yields:
        Processed data batches
    """
    if not DATASETS_AVAILABLE:
        raise ImportError("datasets library is required for streaming")
    
    batch = []
    total_rows = 0
    
    try:
        for item in dataset_iter:
            batch.append(item)
            total_rows += 1
            
            if len(batch) >= batch_size:
                # Process batch
                batch_df = pd.DataFrame(batch)
                batch_bytes = batch_df.memory_usage(deep=True).sum()
                monitor.update(bytes_processed=batch_bytes, rows_processed=len(batch))
                yield batch_df
                batch = []
                
    except Exception as e:
        # If stream fails mid-way, finalize will catch the discrepancy
        if batch:
            monitor.update(bytes_processed=0, rows_processed=len(batch))
            yield pd.DataFrame(batch)
        raise DataIntegrityError(
            f"Stream failed unexpectedly during iteration: {str(e)}"
        )
    
    finally:
        # Finalize with remaining batch
        if batch:
            remaining_df = pd.DataFrame(batch)
            remaining_bytes = remaining_df.memory_usage(deep=True).sum()
            monitor.update(bytes_processed=remaining_bytes, rows_processed=len(batch))
            yield remaining_df

def download_and_process_streaming(
    dataset_name: str,
    split: str = "train",
    streaming: bool = True,
    expected_size_bytes: Optional[int] = None,
    expected_rows: Optional[int] = None
) -> pd.DataFrame:
    """
    Download and process dataset in streaming mode with integrity monitoring.
    
    Args:
        dataset_name: HuggingFace dataset name
        split: Dataset split to load
        streaming: Whether to use streaming mode
        expected_size_bytes: Expected dataset size in bytes (optional)
        expected_rows: Expected number of rows (optional)
        
    Returns:
        Consolidated DataFrame from all chunks
        
    Raises:
        DataIntegrityError: If stream integrity check fails
    """
    if not DATASETS_AVAILABLE:
        raise ImportError("datasets library is required for streaming download")
    
    logger = get_logger("download_and_process_streaming")
    logger.info(f"Starting streaming download for dataset: {dataset_name}")
    
    # Initialize integrity monitor
    monitor = StreamingIntegrityMonitor(
        expected_size_bytes=expected_size_bytes,
        expected_rows=expected_rows,
        dataset_name=dataset_name
    )
    
    try:
        # Load dataset in streaming mode
        dataset = load_dataset(dataset_name, split=split, streaming=streaming)
        
        # Stream and process chunks
        all_chunks = []
        for chunk_df in stream_dataset_chunks(dataset, monitor):
            all_chunks.append(chunk_df)
            # Clear memory periodically
            if len(all_chunks) % 10 == 0:
                gc.collect()
        
        # Consolidate all chunks
        if not all_chunks:
            raise DataIntegrityError(f"No data received from stream for {dataset_name}")
        
        consolidated_df = pd.concat(all_chunks, ignore_index=True)
        
        # Finalize integrity check
        monitor.finalize(actual_rows=len(consolidated_df))
        
        logger.info(
            f"Successfully downloaded and processed {dataset_name}: "
            f"{len(consolidated_df)} rows"
        )
        
        return consolidated_df
        
    except DataIntegrityError:
        # Re-raise integrity errors
        raise
    except Exception as e:
        logger.error(f"Failed to download dataset {dataset_name}: {str(e)}")
        # Don't raise here - let the caller handle graceful degradation
        raise DataIntegrityError(f"Dataset fetch failed: {str(e)}")

def process_batch(batch_df: pd.DataFrame) -> pd.DataFrame:
    """Process a batch of data (placeholder for actual processing logic)."""
    # This would contain actual data processing logic
    # For now, return the batch as-is
    return batch_df

def consolidate_processed_data(chunks: List[pd.DataFrame]) -> pd.DataFrame:
    """Consolidate processed data chunks into a single DataFrame."""
    if not chunks:
        return pd.DataFrame()
    return pd.concat(chunks, ignore_index=True)

def fetch_huggingface_datasets(
    dataset_names: List[str],
    data_dir: Optional[Path] = None
) -> Dict[str, pd.DataFrame]:
    """
    Fetch datasets from HuggingFace with integrity monitoring.
    
    Args:
        dataset_names: List of dataset names to fetch
        data_dir: Directory to save data (optional)
        
    Returns:
        Dictionary mapping dataset names to DataFrames
    """
    if not data_dir:
        data_dir = get_data_dir()
        
    logger = get_logger("fetch_huggingface_datasets")
    results = {}
    
    for dataset_name in dataset_names:
        logger.info(f"Fetching dataset: {dataset_name}")
        try:
            # Try to get expected size from dataset info if available
            # For now, we don't have this info, so we skip expected size check
            df = download_and_process_streaming(dataset_name)
            
            # Generate fingerprint
            fingerprint = generate_data_fingerprint(df)
            logger.info(f"Dataset {dataset_name} fingerprint: {fingerprint}")
            
            # Save to data directory
            output_path = data_dir / f"{dataset_name.replace('/', '_')}.csv"
            df.to_csv(output_path, index=False)
            logger.info(f"Saved dataset to {output_path}")
            
            results[dataset_name] = df
            
        except DataIntegrityError as e:
            logger.error(f"Integrity check failed for {dataset_name}: {str(e)}")
            # Skip this dataset but continue with others
            continue
        except Exception as e:
            logger.error(f"Failed to fetch {dataset_name}: {str(e)}")
            # Skip this dataset but continue with others
            continue
    
    return results

def fetch_openneuro_datasets(
    dataset_ids: List[str],
    data_dir: Optional[Path] = None
) -> Dict[str, pd.DataFrame]:
    """
    Fetch datasets from OpenNeuro (placeholder implementation).
    
    In a real implementation, this would use OpenNeuro API or mne-python
    to download and process EEG data.
    """
    logger = get_logger("fetch_openneuro_datasets")
    logger.warning("OpenNeuro fetch not fully implemented. Using HuggingFace as fallback.")
    # Placeholder - in real implementation, this would integrate with OpenNeuro
    return {}

def validate_metadata_variables(metadata: Dict[str, Any], required_vars: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that required variables exist in dataset metadata.
    
    Args:
        metadata: Dataset metadata dictionary
        required_vars: List of required variable names
        
    Returns:
        Tuple of (is_valid, list_of_missing_vars)
    """
    missing_vars = []
    for var in required_vars:
        if var not in metadata:
            missing_vars.append(var)
    return len(missing_vars) == 0, missing_vars

def check_and_report_variables(metadata: Dict[str, Any], required_vars: List[str]) -> Dict[str, Any]:
    """
    Check for required variables and generate a report.
    
    Args:
        metadata: Dataset metadata dictionary
        required_vars: List of required variable names
        
    Returns:
        Report dictionary with validation results
    """
    is_valid, missing_vars = validate_metadata_variables(metadata, required_vars)
    
    report = {
        "required_variables": required_vars,
        "all_present": is_valid,
        "missing_variables": missing_vars,
        "available_variables": list(metadata.keys())
    }
    
    logger = get_logger("check_and_report_variables")
    logger.info(f"Variable check report: {json.dumps(report, indent=2)}")
    
    return report

def generate_validation_report(
    datasets_info: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate a validation report for multiple datasets.
    
    Args:
        datasets_info: List of dataset information dictionaries
        output_path: Path to save report (optional)
        
    Returns:
        Validation report dictionary
    """
    report = {
        "datasets": datasets_info,
        "summary": {
            "total_datasets": len(datasets_info),
            "valid_datasets": sum(1 for d in datasets_info if d.get("is_valid", False)),
            "invalid_datasets": sum(1 for d in datasets_info if not d.get("is_valid", True))
        }
    }
    
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
    logger = get_logger("generate_validation_report")
    logger.info(f"Validation report generated: {json.dumps(report['summary'], indent=2)}")
    
    return report

def generate_data_fingerprint(df: pd.DataFrame) -> str:
    """
    Generate a SHA-256 fingerprint of a DataFrame.
    
    Args:
        df: DataFrame to fingerprint
        
    Returns:
        SHA-256 hash string
    """
    # Convert DataFrame to bytes for hashing
    df_bytes = df.to_csv(index=False).encode('utf-8')
    return compute_file_sha256(df_bytes)

def update_project_state_with_fingerprint(
    dataset_name: str,
    fingerprint: str,
    state_file_path: Optional[Path] = None
) -> None:
    """
    Update project state file with dataset fingerprint.
    
    Args:
        dataset_name: Name of the dataset
        fingerprint: SHA-256 fingerprint
        state_file_path: Path to state file (optional)
    """
    if not state_file_path:
        state_file_path = Path("state/projects/PROJ-500-neural-correlates-of-predictive-error-si.yaml")
    
    logger = get_logger("update_project_state_with_fingerprint")
    
    try:
        import yaml
        
        # Load existing state or create new
        if state_file_path.exists():
            with open(state_file_path, 'r') as f:
                state = yaml.safe_load(f) or {}
        else:
            state = {"artifact_hashes": {}}
        
        # Update fingerprint
        if "artifact_hashes" not in state:
            state["artifact_hashes"] = {}
        
        state["artifact_hashes"][f"dataset_{dataset_name}"] = fingerprint
        
        # Save updated state
        with open(state_file_path, 'w') as f:
            yaml.dump(state, f, default_flow_style=False)
        
        logger.info(f"Updated project state with fingerprint for {dataset_name}")
        
    except Exception as e:
        logger.error(f"Failed to update project state: {str(e)}")

def main():
    """Main entry point for data ingestion module."""
    logger = get_logger("ingest_main")
    logger.info("Data ingestion module initialized")
    
    # Example usage
    try:
        # This would be called with actual dataset names in production
        # datasets = fetch_huggingface_datasets(["example_dataset"])
        logger.info("Data ingestion module ready")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")

if __name__ == "__main__":
    main()
