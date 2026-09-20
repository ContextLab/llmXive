import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logging import get_logger, log_step_start, log_step_complete, log_step_error
from src.utils.config import get_project_root, ensure_dir
from src.compression.lossless import compress_gzip, compress_bzip2, compress_lzma, compress_lz4
from src.compression.lossless import decompress_gzip, decompress_bzip2, decompress_lzma, decompress_lz4
from src.compression.metrics import compute_compression_metrics
from src.compression.quality_flagger import flag_compression_quality, aggregate_quality_report

logger = get_logger(__name__)

def load_validated_event(event_id: str) -> Dict[str, Any]:
    """
    Load a validated event from data/interim/valid_events.json and return its data paths.
    """
    valid_events_path = get_project_root() / "data" / "interim" / "valid_events.json"
    if not valid_events_path.exists():
        raise FileNotFoundError(f"Valid events file not found: {valid_events_path}")
    
    with open(valid_events_path, 'r') as f:
        valid_data = json.load(f)
    
    event_ids = valid_data.get("event_ids", [])
    if event_id not in event_ids:
        raise ValueError(f"Event ID {event_id} not found in valid events list.")
    
    # Construct expected paths based on project structure
    noise_path = get_project_root() / "data" / "interim" / "noise" / f"{event_id}_noise.npy"
    metadata_path = get_project_root() / "data" / "interim" / "metadata" / f"{event_id}_metadata.json"
    
    if not noise_path.exists():
        raise FileNotFoundError(f"Noise file not found for event {event_id}: {noise_path}")
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found for event {event_id}: {metadata_path}")
    
    return {
        "event_id": event_id,
        "noise_path": noise_path,
        "metadata_path": metadata_path
    }

def process_single_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply all compression methods to a single event and compute metrics.
    Returns a dictionary of results for this event.
    """
    event_id = event_data["event_id"]
    noise_path = event_data["noise_path"]
    metadata_path = event_data["metadata_path"]
    
    log_step_start(f"Processing event {event_id}")
    
    try:
        # Load original data
        import numpy as np
        original_waveform = np.load(noise_path)
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        results = {
            "event_id": event_id,
            "compression_results": []
        }
        
        # Define compression methods and parameters
        # Lossless: gzip, bzip2, lzma, lz4 at levels 1, 5, 9
        lossless_methods = [
            ("gzip", compress_gzip, decompress_gzip, [1, 5, 9]),
            ("bzip2", compress_bzip2, decompress_bzip2, [1, 5, 9]),
            ("lzma", compress_lzma, decompress_lzma, [1, 5, 9]),
            ("lz4", compress_lz4, decompress_lz4, [1, 5, 9]),
        ]
        
        # Lossy: Quantization (16, 8, 4 bit), Wavelet, JPEG2000 (50, 75, 90)
        # Note: T020.1, T020.2, T020.3 implementations assumed to be in lossy.py
        # We need to import them if they exist, otherwise we'll handle gracefully
        lossy_methods = []
        try:
            from src.compression.lossy import (
                quantize_float, unquantize_float,
                wavelet_threshold, undo_wavelet_threshold,
                compress_jpeg2000, decompress_jpeg2000
            )
            lossy_methods = [
                ("quantization_16bit", quantize_float, unquantize_float, [16]),
                ("quantization_8bit", quantize_float, unquantize_float, [8]),
                ("quantization_4bit", quantize_float, unquantize_float, [4]),
                ("wavelet", wavelet_threshold, undo_wavelet_threshold, [1]),
                ("jpeg2000", compress_jpeg2000, decompress_jpeg2000, [50, 75, 90]),
            ]
        except ImportError as e:
            logger.warning(f"Lossy compression methods not fully implemented: {e}")
            logger.info("Proceeding with lossless compression only.")
        
        all_methods = lossless_methods + lossy_methods
        
        output_dir = get_project_root() / "data" / "interim" / "compressed"
        ensure_dir(output_dir)
        
        for method_name, compress_func, decompress_func, levels in all_methods:
            for level in levels:
                try:
                    # Compress
                    compressed_data = compress_func(original_waveform, level=level)
                    
                    # Decompress
                    decompressed_data = decompress_func(compressed_data, level=level)
                    
                    # Compute metrics
                    metrics = compute_compression_metrics(original_waveform, decompressed_data)
                    
                    # Save compressed data
                    method_output_dir = output_dir / method_name / str(level)
                    ensure_dir(method_output_dir)
                    np.save(method_output_dir / f"{event_id}_compressed.npy", compressed_data)
                    
                    result_entry = {
                        "method": method_name,
                        "level": level,
                        "metrics": metrics,
                        "compressed_path": str(method_output_dir / f"{event_id}_compressed.npy")
                    }
                    
                    results["compression_results"].append(result_entry)
                    
                    # Flag quality
                    is_acceptable = flag_compression_quality(metrics)
                    result_entry["is_acceptable"] = is_acceptable
                    
                    logger.info(f"Event {event_id}: {method_name}@{level} - MSE: {metrics['mse']:.6f}, SNR Deg: {metrics['snr_degradation_db']:.2f}dB, Acceptable: {is_acceptable}")
                    
                except Exception as e:
                    logger.error(f"Error processing {event_id} with {method_name}@{level}: {e}")
                    results["compression_results"].append({
                        "method": method_name,
                        "level": level,
                        "error": str(e),
                        "is_acceptable": False
                    })
        
        # Aggregate quality flags for this event
        quality_report = aggregate_quality_report(results["compression_results"])
        results["quality_report"] = quality_report
        
        log_step_complete(f"Event {event_id} processing completed")
        return results
        
    except Exception as e:
        log_step_error(f"Event {event_id} processing failed", e)
        raise

def main():
    """
    Main entry point to apply all compression methods to validated events.
    """
    log_step_start("Compression Pipeline - Main")
    
    project_root = get_project_root()
    output_file = project_root / "data" / "processed" / "compression_results.json"
    ensure_dir(output_file.parent)
    
    # Load valid events
    valid_events_path = project_root / "data" / "interim" / "valid_events.json"
    if not valid_events_path.exists():
        logger.error(f"Valid events file not found: {valid_events_path}")
        logger.error("Please run the data pipeline (T020) first to generate valid events.")
        sys.exit(1)
    
    with open(valid_events_path, 'r') as f:
        valid_data = json.load(f)
    
    event_ids = valid_data.get("event_ids", [])
    if len(event_ids) == 0:
        logger.error("No valid events found. Please run the data pipeline first.")
        sys.exit(1)
    
    logger.info(f"Processing {len(event_ids)} valid events: {event_ids}")
    
    all_results = {
        "pipeline_version": "T022",
        "total_events": len(event_ids),
        "events": []
    }
    
    for event_id in event_ids:
        try:
            event_data = load_validated_event(event_id)
            event_results = process_single_event(event_data)
            all_results["events"].append(event_results)
        except Exception as e:
            logger.error(f"Failed to process event {event_id}: {e}")
            all_results["events"].append({
                "event_id": event_id,
                "error": str(e)
            })
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"Compression results saved to: {output_file}")
    log_step_complete("Compression Pipeline - Main")
    
    # Print summary
    total_processed = len([e for e in all_results["events"] if "compression_results" in e])
    total_failed = len([e for e in all_results["events"] if "error" in e and "compression_results" not in e])
    logger.info(f"Pipeline completed: {total_processed} events processed, {total_failed} events failed.")
    
    return all_results

if __name__ == "__main__":
    main()