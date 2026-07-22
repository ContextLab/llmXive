import os
import sys
import time
import json
import logging
import traceback
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from data.download_libero import download_libero_subset
from data.quantize import quantize_dataset
from data.noise import inject_noise
from utils.logging import get_logger, DataFetchError, QuantizationError, log_resource_snapshot, log_metric
from utils.monitor import ResourceMonitor, get_peak_memory_mb, format_bytes
from config import DATA_DIR, OUTPUT_DIR, SUBSET_SIZE, QUANTIZATION_LEVEL, NOISE_STD, RAM_LIMIT_GB

logger = get_logger(__name__)

def validate_header_size(hdf5_path: str, limit_gb: float = RAM_LIMIT_GB) -> bool:
    """
    T040a: Validate dataset size via header-only read to ensure it fits in RAM.
    Returns True if valid, raises ResourceLimitExceeded if too large.
    """
    from utils.logging import ResourceLimitExceeded
    import h5py

    logger.info(f"Validating header size for {hdf5_path} against limit {limit_gb}GB")
    
    try:
        # Open in read-only mode, header only logic (h5py reads headers automatically)
        with h5py.File(hdf5_path, 'r') as f:
            # Estimate size roughly based on dataset attributes or just file size if available
            # For H5, we can check the file size on disk as a proxy, but strict header check
            # implies we don't load data.
            file_size_bytes = os.path.getsize(hdf5_path)
            file_size_gb = file_size_bytes / (1024 ** 3)
            
            log_metric("input_file_size_gb", file_size_gb)
            logger.info(f"Input file size: {format_bytes(file_size_bytes)} ({file_size_gb:.2f} GB)")
            
            if file_size_gb > limit_gb:
                raise ResourceLimitExceeded(
                    f"Input dataset {hdf5_path} ({file_size_gb:.2f} GB) exceeds RAM limit ({limit_gb} GB)"
                )
            
            return True
    except FileNotFoundError:
        logger.error(f"Validation failed: File not found at {hdf5_path}")
        raise
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise

def run_pipeline(
    input_path: str,
    output_path: str,
    quantization_level: str = QUANTIZATION_LEVEL,
    noise_std: float = NOISE_STD,
    subset_size: int = SUBSET_SIZE
) -> Dict[str, Any]:
    """
    T040b: Sample subset runner.
    Executes the full pipeline: Quantize -> Noise -> Save JSON.
    Includes memory monitoring and logging.
    """
    logger.info(f"Starting pipeline run for subset size {subset_size}")
    logger.info(f"Quantization: {quantization_level}, Noise Std: {noise_std}")
    
    monitor = ResourceMonitor()
    monitor.start()
    
    start_time = time.time()
    
    try:
        # 1. Quantize
        logger.info(f"Step 1: Quantizing dataset from {input_path}")
        quantized_data = quantize_dataset(
            input_path=input_path,
            quantization_level=quantization_level,
            subset_size=subset_size
        )
        log_metric("quantization_step_duration", time.time() - start_time)
        
        # 2. Inject Noise
        logger.info("Step 2: Injecting noise")
        noisy_data = inject_noise(
            data=quantized_data,
            std_dev=noise_std,
            quantization_level=quantization_level
        )
        log_metric("noise_injection_step_duration", time.time() - start_time)
        
        # 3. Save Output
        logger.info(f"Step 3: Saving output to {output_path}")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(noisy_data, f, indent=2)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        peak_ram = get_peak_memory_mb()
        log_metric("total_pipeline_duration_seconds", total_duration)
        log_metric("peak_memory_mb", peak_ram)
        log_resource_snapshot("pipeline_complete")
        
        logger.info(f"Pipeline completed successfully in {total_duration:.2f}s. Peak RAM: {peak_ram:.2f}MB")
        
        return {
            "status": "success",
            "output_path": output_path,
            "duration_seconds": total_duration,
            "peak_memory_mb": peak_ram,
            "records_processed": len(noisy_data) if isinstance(noisy_data, list) else 0
        }
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        traceback.print_exc()
        raise

def main():
    """
    Main entry point for the orchestration logic.
    """
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Define paths
    raw_data_path = os.path.join(DATA_DIR, "libero_subset.h5")
    processed_output_path = os.path.join(OUTPUT_DIR, "processed_subset.json")
    
    logger.info("Starting llmXive Data Pipeline Orchestration")
    
    try:
        # Step 1: Validate Header Size (T040a)
        # This runs AFTER download (T011)
        if not os.path.exists(raw_data_path):
            logger.warning(f"Raw data not found at {raw_data_path}. Skipping validation.")
            # In a real run, we might download here if T011 hasn't run, 
            # but per task order, we assume T011 ran.
            raise FileNotFoundError(f"Input data not found: {raw_data_path}")
        
        validate_header_size(raw_data_path)
        
        # Step 2: Run Pipeline (T040b)
        result = run_pipeline(
            input_path=raw_data_path,
            output_path=processed_output_path,
            quantization_level=QUANTIZATION_LEVEL,
            noise_std=NOISE_STD,
            subset_size=SUBSET_SIZE
        )
        
        print(json.dumps(result, indent=2))
        return 0
        
    except Exception as e:
        logger.critical(f"Orchestration failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())