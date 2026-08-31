"""
Data loader module for fetching datasets from verified sources.
Implements strict error handling with custom exception classes.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
import hashlib
import logging

from datasets import load_dataset

# Configure logger
logger = logging.getLogger(__name__)


class IngestionError(Exception):
    """Base exception for all ingestion-related errors."""
    pass


class DownloadError(IngestionError):
    """Raised when dataset download fails."""
    def __init__(self, message: str, source: Optional[str] = None):
        super().__init__(message)
        self.source = source
        self.message = message

class ValidationError(IngestionError):
    """Raised when downloaded data fails validation checks."""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field
        self.message = message


def _compute_file_hash(filepath: Path) -> str:
    """Compute MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def download_dataset(
    dataset_name: str,
    output_dir: str,
    source_url: Optional[str] = None,
    expected_hash: Optional[str] = None,
    streaming: bool = True,
) -> Path:
    """
    Download a dataset from a verified source (HuggingFace/UCI).

    Args:
        dataset_name: Name of the dataset (used for local filename).
        output_dir: Directory to save the dataset.
        source_url: URL or dataset identifier for load_dataset.
        expected_hash: Optional MD5 hash for validation.
        streaming: If True, use streaming mode for large datasets.

    Returns:
        Path to the downloaded dataset directory or file.

    Raises:
        DownloadError: If download fails or source is unreachable.
        ValidationError: If downloaded data fails hash validation.
    """
    if not source_url:
        raise DownloadError(
            f"Source URL or dataset identifier required for '{dataset_name}'",
            source=dataset_name
        )

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f"Downloading dataset '{dataset_name}' from '{source_url}'...")

        if streaming:
            # For streaming, we process chunks and save to a temp location
            # For simplicity in this implementation, we load the dataset
            # and save to parquet if it's a HuggingFace dataset
            ds = load_dataset(source_url, split="train", streaming=True)
            
            # Create a local parquet file for the dataset
            local_file = output_path / f"{dataset_name}.parquet"
            
            # Convert streaming dataset to parquet
            # Note: This requires materializing the dataset in memory/chunks
            # For very large datasets, this would need chunked writing
            df = ds.to_pandas()
            df.to_parquet(local_file)
            
            logger.info(f"Dataset saved to {local_file}")
            
            # Validate hash if provided
            if expected_hash:
                actual_hash = _compute_file_hash(local_file)
                if actual_hash != expected_hash:
                    raise ValidationError(
                        f"Hash mismatch for '{dataset_name}'. "
                        f"Expected: {expected_hash}, Got: {actual_hash}",
                        field="md5_hash"
                    )
            
            return local_file
        else:
            # Non-streaming download
            ds = load_dataset(source_url, split="train")
            local_file = output_path / f"{dataset_name}.parquet"
            df = ds.to_pandas()
            df.to_parquet(local_file)
            
            logger.info(f"Dataset saved to {local_file}")
            
            # Validate hash if provided
            if expected_hash:
                actual_hash = _compute_file_hash(local_file)
                if actual_hash != expected_hash:
                    raise ValidationError(
                        f"Hash mismatch for '{dataset_name}'. "
                        f"Expected: {expected_hash}, Got: {actual_hash}",
                        field="md5_hash"
                    )
            
            return local_file

    except Exception as e:
        logger.error(f"Failed to download dataset '{dataset_name}': {str(e)}")
        raise DownloadError(
            f"Failed to download dataset '{dataset_name}': {str(e)}",
            source=source_url
        ) from e


def ingest_and_profile(
    dataset_name: str,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    High-level function to download and profile a dataset.

    Args:
        dataset_name: Name of the dataset to ingest.
        config: Configuration dictionary containing source_url, output_dir, etc.

    Returns:
        Dictionary containing dataset profile information.

    Raises:
        IngestionError: If any step in the ingestion process fails.
    """
    from .profiler import DatasetProfiler

    try:
        source_url = config.get("source_url")
        output_dir = config.get("output_dir", "data/raw")
        expected_hash = config.get("expected_hash")

        dataset_path = download_dataset(
            dataset_name=dataset_name,
            output_dir=output_dir,
            source_url=source_url,
            expected_hash=expected_hash,
        )

        profiler = DatasetProfiler()
        profile = profiler.profile_dataset(dataset_path)

        return profile

    except (DownloadError, ValidationError) as e:
        logger.error(f"Ingestion failed for '{dataset_name}': {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during ingestion of '{dataset_name}': {str(e)}")
        raise IngestionError(f"Unexpected error during ingestion: {str(e)}") from e
