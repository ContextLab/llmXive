"""
Main orchestration script for applying compression methods to validated GW events.

This script implements T022:
- Loads validated events from data/interim/valid_events.json
- Iterates through lossless and lossy compression methods defined in the project
- Computes reconstruction metrics (MSE, SNR degradation)
- Flags compression levels with SNR degradation > 5% as 'unacceptable'
- Saves results to data/processed/compression_results.json
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from project API surface
from src.compression.lossless import compress_gzip, decompress_gzip, compress_bzip2, decompress_bzip2, compress_lzma, decompress_lzma
from src.compression.lossy import compress_quantization, decompress_quantization, compress_wavelet, decompress_wavelet, compress_jpeg2000, decompress_jpeg2000
from src.compression.metrics import compute_mse, compute_snr_degradation, compute_compression_metrics
from src.compression.quality_flagger import flag_compression_quality
from src.utils.logging import get_logger, log_step_start, log_step_complete, log_step_error, log_metric
from src.utils.config import get_project_root, ensure_dir

logger = get_logger(__name__)

# Compression method configurations
LOSSLESS_METHODS = [
    {"name": "gzip", "compress": compress_gzip, "decompress": decompress_gzip, "level": 9},
    {"name": "bzip2", "compress": compress_bzip2, "decompress": decompress_bzip2, "level": 9},
    {"name": "lzma", "compress": compress_lzma, "decompress": decompress_lzma, "level": 9},
]

LOSSY_QUANTIZATION_LEVELS = [16, 8, 4]
LOSSY_WAVELET_LEVELS = ["soft", "hard"]
LOSSY_JPEG2000_QUALITIES = [50, 75, 90]

def load_validated_event(event_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a validated event from the interim directory.
    
    Args:
        event_id: The unique identifier for the event
        
    Returns:
        Dictionary containing waveform data and metadata, or None if not found
    """
    project_root = get_project_root()
    event_path = project_root / "data" / "interim" / "events" / f"{event_id}.json"
    
    if not event_path.exists():
        logger.error(f"Event file not found: {event_path}")
        return None
    
    with open(event_path, 'r') as f:
        return json.load(f)

def process_single_event(event_id: str, output_dir: Path) -> Dict[str, Any]:
    """
    Process a single event through all compression methods.
    
    Args:
        event_id: The unique identifier for the event
        output_dir: Directory to save compressed artifacts and results
        
    Returns:
        Dictionary containing compression results for this event
    """
    logger.info(f"Processing event: {event_id}")
    event_data = load_validated_event(event_id)
    
    if event_data is None:
        logger.error(f"Failed to load event: {event_id}")
        return {"event_id": event_id, "status": "failed", "error": "Event not found"}
    
    waveform = event_data.get("waveform")
    if waveform is None:
        logger.error(f"Waveform missing for event: {event_id}")
        return {"event_id": event_id, "status": "failed", "error": "Missing waveform"}
    
    original_waveform = np.array(waveform)
    results = {
        "event_id": event_id,
        "original_snrs": event_data.get("snr", 0),
        "compression_results": []
    }
    
    # Process Lossless Compression
    for method in LOSSLESS_METHODS:
        try:
            compressed = method["compress"](original_waveform, level=method["level"])
            decompressed = method["decompress"](compressed)
            
            metrics = compute_compression_metrics(original_waveform, decompressed)
            metrics["method"] = "lossless"
            metrics["algorithm"] = method["name"]
            metrics["level"] = str(method["level"])
            
            # Save compressed artifact
            artifact_path = output_dir / "lossless" / f"{event_id}_{method['name']}_l{method['level']}.npz"
            ensure_dir(artifact_path.parent)
            np.savez_compressed(artifact_path, data=decompressed)
            
            results["compression_results"].append(metrics)
            logger.info(f"  Lossless {method['name']} completed: SNR degradation = {metrics['snr_degradation']:.2f} dB")
            
        except Exception as e:
            logger.error(f"  Lossless {method['name']} failed: {str(e)}")
            results["compression_results"].append({
                "method": "lossless",
                "algorithm": method["name"],
                "status": "failed",
                "error": str(e)
            })
    
    # Process Lossy Compression - Quantization
    for bit_width in LOSSY_QUANTIZATION_LEVELS:
        try:
            compressed = compress_quantization(original_waveform, bit_width=bit_width)
            decompressed = decompress_quantization(compressed, bit_width=bit_width)
            
            metrics = compute_compression_metrics(original_waveform, decompressed)
            metrics["method"] = "lossy"
            metrics["algorithm"] = "quantization"
            metrics["level"] = f"{bit_width}-bit"
            
            artifact_path = output_dir / "lossy" / "quantization" / f"{event_id}_q{bit_width}.npz"
            ensure_dir(artifact_path.parent)
            np.savez_compressed(artifact_path, data=decompressed)
            
            results["compression_results"].append(metrics)
            logger.info(f"  Lossy Quantization {bit_width}-bit completed: SNR degradation = {metrics['snr_degradation']:.2f} dB")
            
        except Exception as e:
            logger.error(f"  Lossy Quantization {bit_width}-bit failed: {str(e)}")
            results["compression_results"].append({
                "method": "lossy",
                "algorithm": "quantization",
                "level": f"{bit_width}-bit",
                "status": "failed",
                "error": str(e)
            })
    
    # Process Lossy Compression - Wavelet
    for threshold_type in LOSSY_WAVELET_LEVELS:
        try:
            compressed = compress_wavelet(original_waveform, threshold_type=threshold_type)
            decompressed = decompress_wavelet(compressed)
            
            metrics = compute_compression_metrics(original_waveform, decompressed)
            metrics["method"] = "lossy"
            metrics["algorithm"] = "wavelet"
            metrics["level"] = threshold_type
            
            artifact_path = output_dir / "lossy" / "wavelet" / f"{event_id}_w{threshold_type}.npz"
            ensure_dir(artifact_path.parent)
            np.savez_compressed(artifact_path, data=decompressed)
            
            results["compression_results"].append(metrics)
            logger.info(f"  Lossy Wavelet {threshold_type} completed: SNR degradation = {metrics['snr_degradation']:.2f} dB")
            
        except Exception as e:
            logger.error(f"  Lossy Wavelet {threshold_type} failed: {str(e)}")
            results["compression_results"].append({
                "method": "lossy",
                "algorithm": "wavelet",
                "level": threshold_type,
                "status": "failed",
                "error": str(e)
            })
    
    # Process Lossy Compression - JPEG2000
    for quality in LOSSY_JPEG2000_QUALITIES:
        try:
            compressed = compress_jpeg2000(original_waveform, quality=quality)
            decompressed = decompress_jpeg2000(compressed)
            
            metrics = compute_compression_metrics(original_waveform, decompressed)
            metrics["method"] = "lossy"
            metrics["algorithm"] = "jpeg2000"
            metrics["level"] = f"quality_{quality}"
            
            artifact_path = output_dir / "lossy" / "jpeg2000" / f"{event_id}_j2k{quality}.npz"
            ensure_dir(artifact_path.parent)
            np.savez_compressed(artifact_path, data=decompressed)
            
            results["compression_results"].append(metrics)
            logger.info(f"  Lossy JPEG2000 quality {quality} completed: SNR degradation = {metrics['snr_degradation']:.2f} dB")
            
        except Exception as e:
            logger.error(f"  Lossy JPEG2000 quality {quality} failed: {str(e)}")
            results["compression_results"].append({
                "method": "lossy",
                "algorithm": "jpeg2000",
                "level": f"quality_{quality}",
                "status": "failed",
                "error": str(e)
            })
    
    return results

def main():
    """
    Main entry point for the compression pipeline.
    
    Reads validated events from data/interim/valid_events.json,
    applies all compression methods, and saves results to data/processed/compression_results.json
    """
    log_step_start("Compression Pipeline", "T022")
    
    project_root = get_project_root()
    valid_events_path = project_root / "data" / "interim" / "valid_events.json"
    output_dir = project_root / "data" / "processed" / "compressed"
    
    if not valid_events_path.exists():
        logger.error(f"Valid events file not found: {valid_events_path}")
        log_step_error("Compression Pipeline", "Missing valid_events.json")
        sys.exit(1)
    
    # Load list of valid event IDs
    with open(valid_events_path, 'r') as f:
        valid_events_data = json.load(f)
    
    event_ids = valid_events_data.get("event_ids", [])
    if not event_ids:
        logger.error("No valid events found in valid_events.json")
        log_step_error("Compression Pipeline", "No valid events found")
        sys.exit(1)
    
    logger.info(f"Found {len(event_ids)} valid events to process")
    ensure_dir(output_dir)
    
    all_results = []
    failed_events = []
    
    for event_id in event_ids:
        try:
            result = process_single_event(event_id, output_dir)
            all_results.append(result)
            
            if result.get("status") == "failed":
                failed_events.append(event_id)
                log_metric("event_failed", 1, {"event_id": event_id})
            else:
                log_metric("event_processed", 1, {"event_id": event_id})
                
        except Exception as e:
            logger.error(f"Fatal error processing event {event_id}: {str(e)}")
            failed_events.append(event_id)
            log_step_error("Event Processing", str(e))
    
    # Aggregate results and flag unacceptable compression levels
    summary = {
        "total_events": len(event_ids),
        "processed_events": len(all_results) - len(failed_events),
        "failed_events": failed_events,
        "compression_results": all_results,
        "quality_flags": []
    }
    
    # Apply quality flagging (SNR degradation > 5% -> unacceptable)
    for event_result in all_results:
        if event_result.get("status") == "failed":
            continue
        
        flags = flag_compression_quality(event_result)
        summary["quality_flags"].append(flags)
        
        # Log unacceptable compressions
        for flag in flags.get("flags", []):
            if flag.get("status") == "unacceptable":
                log_metric("unacceptable_compression", 1, {
                    "event_id": event_result["event_id"],
                    "method": flag.get("method"),
                    "algorithm": flag.get("algorithm"),
                    "level": flag.get("level"),
                    "snr_degradation": flag.get("snr_degradation")
                })
    
    # Save final results
    results_path = output_dir / "compression_results.json"
    with open(results_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Compression pipeline completed. Results saved to {results_path}")
    log_step_complete("Compression Pipeline", f"Processed {len(all_results) - len(failed_events)}/{len(event_ids)} events")
    
    if failed_events:
        logger.warning(f"Failed to process {len(failed_events)} events: {failed_events}")
        sys.exit(1)
    
    return 0

if __name__ == "__main__":
    # Import numpy here to avoid circular imports if needed
    import numpy as np
    sys.exit(main())
