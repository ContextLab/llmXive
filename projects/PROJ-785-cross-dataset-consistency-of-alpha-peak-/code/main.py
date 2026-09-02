"""
Main orchestration script for the Cross-Dataset APF Consistency pipeline.
Handles memory management, sequential processing of datasets, and pipeline coordination.
"""
import os
import sys
import gc
import shutil
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional

# Local imports
from config import get_project_root, get_data_path, ensure_directories_exist
from download import download_dataset, download_all_datasets
from preprocessing import preprocess_and_verify, verify_no_nans
from environment_config import get_dataset_ids, get_processing_params, get_random_seed
from exceptions import DataIntegrityError, PipelineFailureError
from logger import get_logger, log_structured_event, log_pipeline_failure

# Constants
MEMORY_THRESHOLD_GB = 6.0  # Trigger sequential mode if available memory < 6GB
PROCESS_BUFFER_GB = 2.0   # Buffer to ensure we don't OOM during processing

logger = get_logger(__name__)

def get_available_memory_gb() -> float:
    """
    Get the currently available system memory in GB.
    Uses psutil to query virtual memory statistics.
    """
    mem = psutil.virtual_memory()
    available_bytes = mem.available
    return available_bytes / (1024 ** 3)

def detect_memory_pressure() -> bool:
    """
    Detect if the system is under memory pressure.
    Returns True if available memory is below the threshold + buffer.
    """
    available = get_available_memory_gb()
    threshold = MEMORY_THRESHOLD_GB + PROCESS_BUFFER_GB
    is_pressure = available < threshold
    
    if is_pressure:
        logger.warning(
            "Memory pressure detected",
            extra={
                "event_type": "memory_pressure",
                "available_gb": available,
                "threshold_gb": threshold
            }
        )
    else:
        logger.info(
            "Memory check passed",
            extra={
                "event_type": "memory_check",
                "available_gb": available,
                "threshold_gb": threshold
            }
        )
    
    return is_pressure

def delete_raw_data(dataset_id: str, raw_dir: Path) -> None:
    """
    Delete raw data for a specific dataset to free up memory.
    This is a critical step in the sequential processing strategy.
    
    Args:
        dataset_id: The ID of the dataset (e.g., 'ds003775')
        raw_dir: Path to the raw data directory
    """
    try:
        if raw_dir.exists():
            # Log before deletion
            size_before = sum(f.stat().st_size for f in raw_dir.rglob('*') if f.is_file())
            logger.info(
                "Deleting raw data to free memory",
                extra={
                    "event_type": "cleanup_start",
                    "dataset_id": dataset_id,
                    "size_bytes": size_before
                }
            )
            
            shutil.rmtree(raw_dir)
            
            # Force garbage collection
            gc.collect()
            
            logger.info(
                "Raw data deleted successfully",
                extra={
                    "event_type": "cleanup_complete",
                    "dataset_id": dataset_id
                }
            )
        else:
            logger.warning(
                "Raw directory not found, skipping deletion",
                extra={
                    "event_type": "cleanup_skip",
                    "dataset_id": dataset_id,
                    "path": str(raw_dir)
                }
            )
    except Exception as e:
        logger.error(
            "Failed to delete raw data",
            extra={
                "event_type": "cleanup_error",
                "dataset_id": dataset_id,
                "error": str(e)
            }
        )
        # Do not raise here; we want to continue processing even if cleanup fails

def process_dataset_sequential(
    dataset_id: str,
    pipeline_types: List[str],
    force_sequential: bool = False
) -> bool:
    """
    Process a single dataset through all specified pipelines.
    Implements the sequential processing logic to handle RAM constraints.
    
    Args:
        dataset_id: The OpenNeuro dataset ID (e.g., 'ds003775')
        pipeline_types: List of pipeline identifiers (e.g., ['A', 'B'])
        force_sequential: If True, force sequential processing even if memory is sufficient
    
    Returns:
        True if processing succeeded, False otherwise
    """
    project_root = get_project_root()
    data_path = get_data_path()
    
    raw_dir = data_path / "raw" / dataset_id
    deriv_dir = data_path / "derivatives" / dataset_id
    
    logger.info(
        "Starting sequential processing for dataset",
        extra={
            "event_type": "process_start",
            "dataset_id": dataset_id,
            "pipelines": pipeline_types
        }
    )
    
    try:
        # Step 1: Download dataset (if not already present)
        if not raw_dir.exists():
            logger.info("Downloading dataset", extra={"event_type": "download_start", "dataset_id": dataset_id})
            download_dataset(dataset_id, str(raw_dir))
            logger.info("Download complete", extra={"event_type": "download_complete", "dataset_id": dataset_id})
        else:
            logger.info("Dataset already exists, skipping download", extra={"event_type": "download_skip", "dataset_id": dataset_id})
        
        # Step 2: Process each pipeline sequentially
        for pipeline in pipeline_types:
            logger.info(
                "Processing pipeline",
                extra={
                    "event_type": "pipeline_start",
                    "dataset_id": dataset_id,
                    "pipeline": pipeline
                }
            )
            
            # Run the preprocessing and verification
            success = preprocess_and_verify(dataset_id, pipeline)
            
            if not success:
                raise PipelineFailureError(f"Pipeline {pipeline} failed for dataset {dataset_id}")
            
            logger.info(
                "Pipeline processing complete",
                extra={
                    "event_type": "pipeline_complete",
                    "dataset_id": dataset_id,
                    "pipeline": pipeline
                }
            )
        
        # Step 3: Delete raw data to free memory
        delete_raw_data(dataset_id, raw_dir)
        
        # Step 4: Force garbage collection
        gc.collect()
        
        logger.info(
            "Dataset processing fully complete",
            extra={
                "event_type": "process_complete",
                "dataset_id": dataset_id
            }
        )
        return True
        
    except Exception as e:
        logger.error(
            "Failed to process dataset",
            extra={
                "event_type": "process_error",
                "dataset_id": dataset_id,
                "error": str(e)
            }
        )
        log_pipeline_failure(dataset_id, str(e))
        return False

def main() -> int:
    """
    Main entry point for the pipeline orchestration.
    Implements the sequential processing strategy for memory-constrained environments.
    
    Returns:
        0 on success, 1 on failure
    """
    logger.info("Pipeline orchestration started", extra={"event_type": "orchestration_start"})
    
    try:
        # Load configuration
        dataset_ids = get_dataset_ids()
        params = get_processing_params()
        pipelines = params.get("pipelines", ["A", "B"])
        
        logger.info(
            "Configuration loaded",
            extra={
                "event_type": "config_loaded",
                "datasets": dataset_ids,
                "pipelines": pipelines
            }
        )
        
        # Check memory pressure
        is_pressure = detect_memory_pressure()
        
        if is_pressure:
            logger.info("Memory pressure detected. Enforcing sequential processing.", extra={"event_type": "memory_force"})
        
        # Process datasets sequentially
        all_success = True
        for dataset_id in dataset_ids:
            logger.info(
                "Processing next dataset in sequence",
                extra={
                    "event_type": "sequence_step",
                    "dataset_id": dataset_id,
                    "remaining": len(dataset_ids) - 1
                }
            )
            
            success = process_dataset_sequential(
                dataset_id=dataset_id,
                pipeline_types=pipelines,
                force_sequential=is_pressure
            )
            
            if not success:
                logger.error(
                    "Sequential processing failed for dataset",
                    extra={
                        "event_type": "sequence_fail",
                        "dataset_id": dataset_id
                    }
                )
                all_success = False
                # Continue to next dataset to ensure we process as much as possible
                # but mark overall as failed
            else:
                logger.info(
                    "Sequential processing succeeded for dataset",
                    extra={
                        "event_type": "sequence_success",
                        "dataset_id": dataset_id
                    }
                )
        
        if all_success:
            logger.info("All datasets processed successfully", extra={"event_type": "orchestration_complete"})
            return 0
        else:
            logger.warning("Some datasets failed processing", extra={"event_type": "orchestration_partial"})
            return 1
            
    except Exception as e:
        logger.critical(
            "Fatal error in orchestration",
            extra={
                "event_type": "orchestration_fatal",
                "error": str(e)
            }
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())