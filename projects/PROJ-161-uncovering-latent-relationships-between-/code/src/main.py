"""
Main orchestration script for the llmXive research pipeline.
Implements logging infrastructure to track data versions and pipeline execution.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.schema import DataVersion


def ensure_data_directory() -> str:
    """Ensure the data directory exists and return its path."""
    data_dir = os.path.join(project_root, 'data')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_data_version_path() -> str:
    """Return the path to the data_version.json file."""
    data_dir = ensure_data_directory()
    return os.path.join(data_dir, 'data_version.json')


def load_data_version() -> Dict[str, Any]:
    """
    Load existing data version records from data_version.json.
    Returns an empty dict if the file doesn't exist or is empty.
    """
    path = get_data_version_path()
    if not os.path.exists(path):
        return {}

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load {path}: {e}. Starting fresh.")
        return {}


def save_data_version(data_version: Dict[str, Any]) -> None:
    """
    Save data version records to data_version.json.
    Ensures the file is written atomically and formatted nicely.
    """
    path = get_data_version_path()
    # Write to a temp file first, then rename (atomic on most systems)
    temp_path = path + '.tmp'
    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data_version, f, indent=2, default=str)
        os.replace(temp_path, path)
    except IOError as e:
        # Clean up temp file if it exists
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise IOError(f"Failed to write {path}: {e}") from e


def log_data_version(
    source_url: str,
    checksum_sha256: str,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Log a new data version entry to data_version.json.

    Args:
        source_url: The URL or identifier of the data source.
        checksum_sha256: SHA256 checksum of the data file.
        description: Optional description of the data version.

    Returns:
        The full updated data version dictionary.
    """
    existing = load_data_version()

    # Create a unique key based on source_url and checksum
    version_key = f"{source_url}:{checksum_sha256}"

    # If this exact version already exists, just return it
    if version_key in existing:
        print(f"Data version already logged: {version_key}")
        return existing

    # Create new entry
    timestamp = datetime.now(timezone.utc).isoformat()
    new_entry = {
        "source_url": source_url,
        "checksum_sha256": checksum_sha256,
        "timestamp": timestamp
    }

    if description:
        new_entry["description"] = description

    existing[version_key] = new_entry

    save_data_version(existing)
    print(f"Logged data version: {version_key}")
    return existing


def log_pipeline_start(pipeline_name: str) -> str:
    """
    Log the start of a pipeline run.

    Args:
        pipeline_name: Name/identifier for the pipeline run.

    Returns:
        A unique run ID for this execution.
    """
    run_id = f"{pipeline_name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    print(f"Pipeline '{pipeline_name}' started at {datetime.now(timezone.utc).isoformat()}")
    return run_id


def log_pipeline_end(run_id: str, success: bool, duration_seconds: float) -> None:
    """
    Log the end of a pipeline run.

    Args:
        run_id: The run ID returned by log_pipeline_start.
        success: Whether the pipeline completed successfully.
        duration_seconds: Total execution time in seconds.
    """
    status = "SUCCESS" if success else "FAILED"
    print(f"Pipeline '{run_id}' ended at {datetime.now(timezone.utc).isoformat()}")
    print(f"Status: {status}, Duration: {duration_seconds:.2f}s")


def main() -> int:
    """
    Main entry point for the pipeline.
    Demonstrates the logging infrastructure.
    """
    start_time = time.time()
    run_id = log_pipeline_start("llmXive_pipeline")

    try:
        # Example: Log a data version (this would normally be called after data download)
        # For demonstration, we'll log a placeholder that shows the infrastructure works
        # In real usage, this would be called with actual data from T013/T017
        log_data_version(
            source_url="https://example.com/mock_data",
            checksum_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            description="Example data version logging"
        )

        # Simulate some work
        time.sleep(0.1)

        duration = time.time() - start_time
        log_pipeline_end(run_id, True, duration)
        return 0

    except Exception as e:
        duration = time.time() - start_time
        log_pipeline_end(run_id, False, duration)
        print(f"Pipeline failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
