"""
OpenNeuro Dataset Downloader.

Implements Task T012: Fetch datasets from OpenNeuro using openneuro-py.
Constraint: Must fail loudly on API error (no synthetic fallback).
"""
import os
import sys
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project imports
from config import get_project_root, get_data_path, ensure_directories_exist
from environment_config import get_dataset_ids, load_environment_config
from exceptions import DataIntegrityError, PipelineFailureError
from logger import get_logger, log_structured_event, log_data_integrity_error

# Import openneuro-py dynamically to handle missing dependency gracefully
try:
    from openneuro import download as openneuro_download
except ImportError:
    raise ImportError(
        "Missing required dependency 'openneuro-py'. "
        "Please install it via: pip install openneuro-py"
    )

logger = get_logger(__name__)


def download_dataset(
    dataset_id: str,
    output_dir: Optional[Path] = None,
    version: str = "latest",
    include_derivatives: bool = True,
) -> Path:
    """
    Download a specific dataset from OpenNeuro.

    Args:
        dataset_id: The OpenNeuro dataset ID (e.g., 'ds003865').
        output_dir: Target directory for download. Defaults to data/raw/{dataset_id}.
        version: Dataset version (default: 'latest').
        include_derivatives: Whether to include derivatives (default: True).

    Returns:
        Path to the downloaded dataset directory.

    Raises:
        DataIntegrityError: If the dataset ID is invalid or not found.
        PipelineFailureError: If the download fails due to network/API issues.
    """
    if output_dir is None:
        raw_path = get_data_path("raw")
        output_dir = raw_path / dataset_id

    # Ensure target directory exists and is clean
    if output_dir.exists():
        logger.warning(f"Output directory {output_dir} exists. Removing and re-downloading.")
        shutil.rmtree(output_dir)
    
    ensure_directories_exist([output_dir])

    logger.info(f"Starting download for dataset: {dataset_id} (version: {version})")
    log_structured_event(
        event="download_start",
        dataset_id=dataset_id,
        version=version,
        target_path=str(output_dir)
    )

    try:
        # Use openneuro-py CLI-style download function
        # openneuro download --dataset dsXXXXXX --output-dir path --version ver
        # The library exposes a download function that mimics this behavior.
        
        # Note: openneuro-py's main entry point is often a CLI, but it exposes
        # a download function in the module. We call it directly.
        # If the API signature changes, this is the place to adapt, but we rely
        # on the library's public API.
        
        # Attempt download
        # The openneuro library's download function signature:
        # download(dataset, output_dir, version, ...kwargs)
        openneuro_download(
            dataset=dataset_id,
            output_dir=str(output_dir),
            version=version,
            include_derivatives=include_derivatives,
            # Force overwrite if directory exists (handled above, but safe guard)
            force_overwrite=True 
        )

        if not output_dir.exists():
            raise PipelineFailureError(
                f"Download reported success but directory {output_dir} does not exist."
            )

        logger.info(f"Successfully downloaded {dataset_id} to {output_dir}")
        log_structured_event(
            event="download_success",
            dataset_id=dataset_id,
            file_count=len(list(output_dir.rglob("*"))),
            target_path=str(output_dir)
        )

        return output_dir

    except Exception as e:
        # Fail loudly: No synthetic fallback
        error_msg = f"Failed to download dataset {dataset_id}: {str(e)}"
        logger.error(error_msg)
        log_data_integrity_error(error_msg)
        
        # Clean up partial downloads if any
        if output_dir.exists():
            shutil.rmtree(output_dir)
        
        raise PipelineFailureError(error_msg) from e


def download_all_datasets() -> Dict[str, Path]:
    """
    Download all datasets configured in environment_config.py.

    Returns:
        Dictionary mapping dataset_id to its local Path.

    Raises:
        PipelineFailureError: If any download fails.
    """
    dataset_ids = get_dataset_ids()
    
    if not dataset_ids:
        raise DataIntegrityError(
            "No dataset IDs found in configuration. "
            "Please update environment_config.py or set OPENNEURO_DATASET_IDS."
        )

    logger.info(f"Found {len(dataset_ids)} datasets to download: {dataset_ids}")
    results = {}

    for ds_id in dataset_ids:
        try:
            path = download_dataset(ds_id)
            results[ds_id] = path
        except PipelineFailureError as e:
            # Stop immediately on first failure (fail loudly)
            raise PipelineFailureError(
                f"Aborting pipeline due to download failure of {ds_id}. "
                f"Reason: {e}"
            ) from e

    return results


def main():
    """Entry point for the download script."""
    logger.info("Starting OpenNeuro Data Acquisition (Task T012)")
    
    try:
        config = load_environment_config()
        logger.info(f"Loaded config: {config.get('dataset_ids', [])}")
        
        results = download_all_datasets()
        
        logger.info("All downloads completed successfully.")
        log_structured_event(
            event="pipeline_complete",
            stage="download",
            datasets_downloaded=list(results.keys())
        )
        
        return 0

    except (DataIntegrityError, PipelineFailureError) as e:
        logger.critical(f"Pipeline failed: {e}")
        return 1
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())