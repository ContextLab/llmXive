"""Data loading module with network interruption handling.

This module streams code samples from HuggingFace datasets with robust
error handling for network interruptions, rate limiting, and other
connectivity issues.

Per Constitution Principle III (Data Hygiene), all data loading failures
are logged and handled gracefully.
"""
import csv
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

# Import from datasets library - will be in requirements.txt
try:
    from datasets import load_dataset
except ImportError:
    load_dataset = None

# Module-level logger
_logger = None

def _get_logger() -> logging.Logger:
    """Get or create the module logger."""
    global _logger
    if _logger is None:
        _logger = logging.getLogger("data_loader")
        _logger.setLevel(logging.INFO)
        if not _logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            _logger.addHandler(handler)
    return _logger

def load_raw_data(
    subset_size_mb: float = 500.0,
    streaming: bool = True,
    output_path: Optional[Path] = None,
    max_retries: int = 3,
    retry_delay_seconds: float = 5.0
) -> Generator[Dict[str, Any], None, None]:
    """Stream code samples from HuggingFace codeparrot/github-code dataset.

    This function implements robust error handling for:
    - Network interruptions (with automatic retry)
    - Rate limiting from HuggingFace API
    - Connection timeouts
    - Dataset loading failures

    Args:
        subset_size_mb: Target subset size in megabytes
        streaming: If True, use streaming mode (recommended for large datasets)
        output_path: Optional path to save downloaded data as CSV
        max_retries: Maximum number of retry attempts for network errors
        retry_delay_seconds: Delay between retry attempts in seconds

    Yields:
        Dictionary with code samples and metadata

    Raises:
        RuntimeError: If dataset cannot be loaded after max retries
    """
    logger = _get_logger()

    if load_dataset is None:
        raise RuntimeError(
            "datasets library not installed. Please install with: "
            "pip install datasets"
        )

    dataset_name = "codeparrot/github-code"
    language = "python"
    logger.info(f"Loading dataset: {dataset_name} (language={language})")

    attempt = 0
    last_error = None

    while attempt < max_retries:
        try:
            if streaming:
                logger.info("Using streaming mode for dataset loading")
                dataset = load_dataset(
                    dataset_name,
                    language=language,
                    split="train",
                    streaming=True
                )
            else:
                dataset = load_dataset(
                    dataset_name,
                    language=language,
                    split="train"
                )

            # Verify dataset loaded
            if dataset is None:
                raise RuntimeError("Dataset loading returned None")

            logger.info(f"Dataset loaded successfully (streaming={streaming})")
            break

        except Exception as e:
            attempt += 1
            last_error = e
            error_type = type(e).__name__
            error_msg = str(e)

            logger.warning(
                f"Attempt {attempt}/{max_retries} failed: {error_type}: {error_msg}"
            )

            # Check for retryable errors
            retryable_errors = [
                "ConnectionError",
                "Timeout",
                "ReadTimeout",
                "RateLimitError",
                "HTTPError",
                "RetryError",
                "network",
                "connection",
                "timeout",
                "rate limit"
            ]

            should_retry = any(
                err.lower() in error_msg.lower() or err.lower() in error_type.lower()
                for err in retryable_errors
            )

            if should_retry and attempt < max_retries:
                logger.info(f"Retrying in {retry_delay_seconds} seconds...")
                time.sleep(retry_delay_seconds * attempt)  # Exponential backoff
            else:
                raise RuntimeError(
                    f"Failed to load dataset after {max_retries} attempts: {error_msg}"
                ) from e

    if last_error is None:
        logger.info("Dataset loaded successfully on first attempt")

    # Stream the data
    sample_count = 0
    byte_count = 0
    target_bytes = int(subset_size_mb * 1024 * 1024)

    try:
        for item in dataset:
            sample_count += 1
            code = item.get("content", "")

            if not code or not code.strip():
                continue

            byte_count += len(code.encode("utf-8"))

            # Create result dictionary
            result = {
                "id": f"sample_{sample_count:08d}",
                "code": code,
                "timestamp": datetime.now().isoformat(),
                "byte_size": len(code.encode("utf-8"))
            }

            yield result

            # Check if we've reached target size
            if byte_count >= target_bytes:
                logger.info(
                    f"Reached target size: {byte_count / (1024*1024):.2f} MB "
                    f"from {sample_count} samples"
                )
                break

    except KeyboardInterrupt:
        logger.info("Download interrupted by user")
        raise
    except Exception as e:
        logger.error(f"Error during data streaming: {type(e).__name__}: {str(e)}")
        raise

    logger.info(
        f"Data loading complete: {sample_count} samples, "
        f"{byte_count / (1024*1024):.2f} MB"
    )

def save_streamed_data_to_csv(
    data_generator: Generator[Dict[str, Any], None, None],
    output_path: Path,
    max_samples: Optional[int] = None
) -> int:
    """Save streamed data to a CSV file with error handling.

    Args:
        data_generator: Generator yielding data dictionaries
        output_path: Path to save CSV file
        max_samples: Optional maximum number of samples to save

    Returns:
        Number of samples saved

    Raises:
        IOError: If file cannot be written
    """
    logger = _get_logger()
    saved_count = 0

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["id", "code", "timestamp", "byte_size"]

    try:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for sample in data_generator:
                writer.writerow(sample)
                saved_count += 1

                if max_samples and saved_count >= max_samples:
                    logger.info(f"Reached max_samples limit: {max_samples}")
                    break

    except PermissionError as e:
        logger.error(f"Permission denied writing to {output_path}: {e}")
        raise
    except UnicodeEncodeError as e:
        logger.error(f"Unicode encoding error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error saving data to CSV: {type(e).__name__}: {e}")
        raise

    logger.info(f"Saved {saved_count} samples to {output_path}")
    return saved_count

def load_raw_data_to_csv(
    subset_size_mb: float = 500.0,
    streaming: bool = True,
    output_path: Optional[Path] = None,
    max_samples: Optional[int] = None
) -> Path:
    """Load raw data and save to CSV file with comprehensive error handling.

    This is a convenience function that combines loading and saving.

    Args:
        subset_size_mb: Target subset size in megabytes
        streaming: If True, use streaming mode
        output_path: Path for output CSV (defaults to data/raw/github-code-sample.csv)
        max_samples: Optional maximum number of samples

    Returns:
        Path to the saved CSV file
    """
    logger = _get_logger()

    if output_path is None:
        output_path = Path("data/raw/github-code-sample.csv")

    output_path = Path(output_path)

    logger.info(f"Loading and saving data to {output_path}")

    data_gen = load_raw_data(
        subset_size_mb=subset_size_mb,
        streaming=streaming,
        max_retries=3,
        retry_delay_seconds=5.0
    )

    saved_count = save_streamed_data_to_csv(
        data_gen,
        output_path,
        max_samples=max_samples
    )

    logger.info(f"Data loading complete: {saved_count} samples saved")
    return output_path
