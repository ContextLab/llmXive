"""
Data Ingestion Module for Neural Correlates of Predictive Error Signals.

Implements streaming data download and metadata validation with strict
memory management to ensure peak RAM usage remains under 7 GB.
"""
import json
import logging
import os
import gc
from pathlib import Path
from typing import Dict, Any, Optional, List, Iterator, Tuple
import io
import hashlib
import shutil

# Import from local utils
from ..utils.logging import get_logger, log_event, log_error
from ..utils.checksum import compute_file_sha256

# Try to import datasets library, but fail loudly if not available
try:
    from datasets import load_dataset, DownloadConfig
except ImportError:
    raise ImportError(
        "The 'datasets' library is required for streaming ingestion. "
        "Install it via: pip install datasets"
    )

# Memory limit configuration (in GB)
RAM_LIMIT_GB = 7.0
BUFFER_SIZE_MB = 50  # Buffer size for streaming chunks

# Initialize logger
logger = get_logger(__name__)


def get_current_memory_usage_gb() -> float:
    """
    Estimate current memory usage in GB.
    
    Returns:
        float: Estimated memory usage in GB.
    """
    try:
        import resource
        # Get RSS (Resident Set Size) in bytes
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On macOS, ru_maxrss is in bytes; on Linux, it's in KB
        # We'll assume bytes for safety and convert
        if os.name == 'posix' and sys.platform != 'darwin':
            usage *= 1024  # Linux reports in KB
        
        return usage / (1024 ** 3)  # Convert to GB
    except Exception as e:
        logger.warning(f"Could not determine memory usage: {e}")
        return 0.0


def validate_metadata_variables(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that required metadata variables are present.
    
    Args:
        metadata: Dictionary containing dataset metadata.
        
    Returns:
        Tuple of (is_valid, list_of_missing_variables)
    """
    required_vars = ['stimulus_type', 'response_correctness']
    missing = []
    
    for var in required_vars:
        if var not in metadata:
            missing.append(var)
    
    is_valid = len(missing) == 0
    return is_valid, missing


def check_and_report_variables(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check for variable presence and report status.
    
    Args:
        metadata: Dataset metadata dictionary.
        
    Returns:
        Dictionary with validation results.
    """
    is_valid, missing = validate_metadata_variables(metadata)
    
    report = {
        'is_valid': is_valid,
        'missing_variables': missing,
        'present_variables': [k for k in metadata.keys() if k in ['stimulus_type', 'response_correctness']]
    }
    
    return report


def generate_validation_report(
    dataset_id: str,
    metadata: Dict[str, Any],
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate a validation report for a dataset and save it to disk.
    
    Args:
        dataset_id: The ID of the dataset being validated.
        metadata: The dataset metadata.
        output_path: Path where the report will be saved.
        
    Returns:
        The validation report dictionary.
    """
    report = {
        'dataset_id': dataset_id,
        'validation_status': 'passed' if metadata else 'failed',
        'variables': check_and_report_variables(metadata),
        'analysis_mode': 'error_signal' if metadata.get('response_correctness') else 'stimulus_driven'
    }
    
    # Determine analysis mode based on variable availability
    if 'response_correctness' in metadata:
        report['analysis_mode'] = 'error_signal'
    elif 'stimulus_type' in metadata:
        report['analysis_mode'] = 'stimulus_driven'
        logger.warning(f"Dataset {dataset_id}: Missing 'response_correctness', falling back to stimulus-driven mode")
    else:
        report['analysis_mode'] = 'unknown'
        logger.error(f"Dataset {dataset_id}: Missing both required variables")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write report to disk
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    log_event("validation_report_generated", {
        'dataset_id': dataset_id,
        'output_path': str(output_path),
        'analysis_mode': report['analysis_mode']
    })
    
    return report


def stream_dataset_chunks(
    dataset_id: str,
    split: str = 'train',
    streaming: bool = True
) -> Iterator[Dict[str, Any]]:
    """
    Stream dataset chunks with memory management.
    
    This function uses Hugging Face's streaming API to download data
    in chunks, ensuring that peak RAM usage stays below the limit.
    
    Args:
        dataset_id: The Hugging Face dataset ID.
        split: The split to load (e.g., 'train', 'test').
        streaming: Whether to use streaming mode.
        
    Yields:
        Individual data samples from the dataset.
    """
    if not streaming:
        raise ValueError("This function only supports streaming mode")
    
    log_event("streaming_dataset_start", {
        'dataset_id': dataset_id,
        'split': split
    })
    
    try:
        # Configure download to use temporary cache that we can clean up
        download_config = DownloadConfig(cache_dir=os.environ.get('HF_DATASETS_CACHE', '/tmp/hf_cache'))
        
        dataset = load_dataset(
            dataset_id,
            split=split,
            streaming=True,
            download_config=download_config
        )
        
        for sample in dataset:
            # Check memory usage before yielding
            current_ram = get_current_memory_usage_gb()
            if current_ram > RAM_LIMIT_GB:
                log_error("memory_limit_exceeded", {
                    'current_ram_gb': current_ram,
                    'limit_gb': RAM_LIMIT_GB
                })
                # Force garbage collection
                gc.collect()
                
                # If still over limit after GC, raise error
                if get_current_memory_usage_gb() > RAM_LIMIT_GB:
                    raise MemoryError(
                        f"Memory limit exceeded ({current_ram:.2f} GB > {RAM_LIMIT_GB} GB). "
                        "Consider reducing batch size or processing in smaller chunks."
                    )
            
            yield sample
            
    except Exception as e:
        log_error("streaming_dataset_error", {
            'dataset_id': dataset_id,
            'error': str(e)
        })
        raise
    finally:
        # Clean up any temporary files
        gc.collect()
        log_event("streaming_dataset_end", {
            'dataset_id': dataset_id
        })


def download_and_process_streaming(
    dataset_id: str,
    output_dir: Path,
    split: str = 'train',
    chunk_size: int = 1000
) -> Path:
    """
    Download and process a dataset in streaming mode, writing output in chunks.
    
    This function ensures that we never load the entire dataset into memory,
    instead processing it in manageable chunks and writing results incrementally.
    
    Args:
        dataset_id: The Hugging Face dataset ID.
        output_dir: Directory where processed data will be saved.
        split: The split to process.
        chunk_size: Number of samples to process per chunk.
        
    Returns:
        Path to the final output file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{dataset_id.replace('/', '_')}_processed.csv"
    
    log_event("download_start", {
        'dataset_id': dataset_id,
        'output_file': str(output_file)
    })
    
    total_samples = 0
    chunk_data = []
    
    try:
        for sample in stream_dataset_chunks(dataset_id, split=split):
            chunk_data.append(sample)
            
            # Process chunk when it reaches the limit
            if len(chunk_data) >= chunk_size:
                # Convert chunk to DataFrame and append to file
                import pandas as pd
                chunk_df = pd.DataFrame(chunk_data)
                
                # Append to file (or create if first chunk)
                mode = 'a' if total_samples > 0 else 'w'
                header = total_samples == 0
                
                chunk_df.to_csv(output_file, mode=mode, header=header, index=False)
                
                total_samples += len(chunk_data)
                chunk_data = []
                
                # Force garbage collection after each chunk
                gc.collect()
                
                # Check memory usage
                current_ram = get_current_memory_usage_gb()
                log_event("chunk_processed", {
                    'total_samples': total_samples,
                    'current_ram_gb': current_ram
                })
        
        # Process remaining samples
        if chunk_data:
            import pandas as pd
            chunk_df = pd.DataFrame(chunk_data)
            mode = 'a' if total_samples > 0 else 'w'
            header = total_samples == 0
            chunk_df.to_csv(output_file, mode=mode, header=header, index=False)
            total_samples += len(chunk_data)
        
        log_event("download_complete", {
            'dataset_id': dataset_id,
            'total_samples': total_samples,
            'output_file': str(output_file)
        })
        
        return output_file
        
    except Exception as e:
        log_error("download_failed", {
            'dataset_id': dataset_id,
            'error': str(e)
        })
        raise


def main():
    """
    Main entry point for the ingestion module.
    
    This function demonstrates the streaming ingestion process with
    memory management.
    """
    # Example usage
    dataset_id = "openneuro:ds000001"  # Example dataset ID
    output_dir = Path("data/raw")
    
    print(f"Starting streaming download for {dataset_id}")
    print(f"Memory limit: {RAM_LIMIT_GB} GB")
    
    try:
        output_file = download_and_process_streaming(
            dataset_id=dataset_id,
            output_dir=output_dir,
            split='train',
            chunk_size=1000
        )
        print(f"Download complete: {output_file}")
    except Exception as e:
        print(f"Download failed: {e}")
        raise


if __name__ == "__main__":
    main()
