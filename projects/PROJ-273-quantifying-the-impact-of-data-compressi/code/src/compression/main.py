"""
Main entry point for User Story 2: Compression Pipeline.
Applies all lossless and lossy compression methods to validated events from US1.

Dependencies:
- T019 (lossless.py)
- T020.1 (lossy.py - Quantization)
- T020.2 (lossy.py - Wavelet)
- T020.3 (lossy.py - JPEG2000)
- T021 (metrics.py)
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import time

# Add project root to path to allow imports from src
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logging import get_logger, log_step_start, log_step_complete, log_step_error, log_metric
from src.utils.config import get_path, ensure_dir
from src.compression.lossless import compress_data, decompress_data, verify_lossless
from src.compression.lossy import compress_quantization, decompress_quantization
from src.compression.lossy import compress_wavelet, decompress_wavelet
from src.compression.lossy import compress_jpeg2000, decompress_jpeg2000
from src.compression.metrics import compute_compression_metrics

logger = get_logger(__name__)

# Configuration for compression levels
LOSSLESS_LEVELS = {
    'gzip': [1, 5, 9],
    'bzip2': [1, 5, 9],
    'lzma': [0, 5, 9]
}

LOSSY_LEVELS = {
    'quantization': [4, 8, 12],  # bit-widths
    'wavelet': [1, 2, 3],        # threshold levels
    'jpeg2000': [0.1, 0.5, 1.0]  # quality factors
}

def load_validated_event(event_path: Path) -> Dict[str, Any]:
    """Load a validated event from US1 output."""
    try:
        with open(event_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load event {event_path}: {e}")
        raise

def process_single_event(
    event_data: Dict[str, Any],
    event_id: str,
    output_base: Path
) -> Dict[str, Any]:
    """
    Apply all compression methods to a single event.
    Returns a summary of results.
    """
    results = {
        'event_id': event_id,
        'methods': {}
    }
    
    # Extract strain data and metadata
    strain = event_data.get('strain', [])
    metadata = event_data.get('metadata', {})
    true_params = event_data.get('true_parameters', {})
    
    if not strain:
        logger.warning(f"No strain data found for event {event_id}, skipping")
        return results
    
    strain_array = np.array(strain)
    original_size = strain_array.nbytes
    
    # 1. Lossless Compression
    logger.info(f"Processing lossless compression for {event_id}")
    for method, levels in LOSSLESS_LEVELS.items():
        method_results = {}
        for level in levels:
            try:
                # Compress
                compressed = compress_data(strain_array, method, level)
                compressed_size = len(compressed)
                
                # Decompress
                decompressed = decompress_data(compressed, method, level)
                
                # Verify lossless
                is_lossless = verify_lossless(strain_array, decompressed)
                
                # Compute metrics
                metrics = compute_compression_metrics(
                    strain_array, 
                    decompressed, 
                    original_size, 
                    compressed_size
                )
                
                method_results[str(level)] = {
                    'status': 'success',
                    'is_lossless': is_lossless,
                    'compression_ratio': metrics['compression_ratio'],
                    'mse': metrics['mse'],
                    'snr_degradation_db': metrics['snr_degradation_db']
                }
                
                # Save artifacts
                artifact_dir = output_base / 'lossless' / method / str(level)
                ensure_dir(artifact_dir)
                
                with open(artifact_dir / 'compressed.bin', 'wb') as f:
                    f.write(compressed)
                with open(artifact_dir / 'decompressed.json', 'w') as f:
                    json.dump(decompressed.tolist(), f)
                
            except Exception as e:
                logger.error(f"Lossless {method} level {level} failed: {e}")
                method_results[str(level)] = {'status': 'failed', 'error': str(e)}
        
        results['methods'][method] = method_results
    
    # 2. Lossy Compression
    logger.info(f"Processing lossy compression for {event_id}")
    
    # Quantization
    for level in LOSSY_LEVELS['quantization']:
        try:
            compressed, params = compress_quantization(strain_array, bit_width=level)
            decompressed = decompress_quantization(compressed, params)
            
            metrics = compute_compression_metrics(
                strain_array, 
                decompressed, 
                original_size, 
                len(compressed)
            )
            
            results['methods']['quantization'][str(level)] = {
                'status': 'success',
                'compression_ratio': metrics['compression_ratio'],
                'mse': metrics['mse'],
                'snr_degradation_db': metrics['snr_degradation_db']
            }
            
            # Save artifacts
            artifact_dir = output_base / 'lossy' / 'quantization' / str(level)
            ensure_dir(artifact_dir)
            with open(artifact_dir / 'compressed.bin', 'wb') as f:
                f.write(compressed)
            with open(artifact_dir / 'params.json', 'w') as f:
                json.dump(params, f)
            
        except Exception as e:
            logger.error(f"Quantization level {level} failed: {e}")
            results['methods']['quantization'][str(level)] = {'status': 'failed', 'error': str(e)}
    
    # Wavelet
    for level in LOSSY_LEVELS['wavelet']:
        try:
            compressed, params = compress_wavelet(strain_array, threshold_level=level)
            decompressed = decompress_wavelet(compressed, params)
            
            metrics = compute_compression_metrics(
                strain_array, 
                decompressed, 
                original_size, 
                len(compressed)
            )
            
            results['methods']['wavelet'][str(level)] = {
                'status': 'success',
                'compression_ratio': metrics['compression_ratio'],
                'mse': metrics['mse'],
                'snr_degradation_db': metrics['snr_degradation_db']
            }
            
            # Save artifacts
            artifact_dir = output_base / 'lossy' / 'wavelet' / str(level)
            ensure_dir(artifact_dir)
            with open(artifact_dir / 'compressed.bin', 'wb') as f:
                f.write(compressed)
            with open(artifact_dir / 'params.json', 'w') as f:
                json.dump(params, f)
            
        except Exception as e:
            logger.error(f"Wavelet level {level} failed: {e}")
            results['methods']['wavelet'][str(level)] = {'status': 'failed', 'error': str(e)}
    
    # JPEG2000
    for level in LOSSY_LEVELS['jpeg2000']:
        try:
            compressed, params = compress_jpeg2000(strain_array, quality_factor=level)
            decompressed = decompress_jpeg2000(compressed, params)
            
            metrics = compute_compression_metrics(
                strain_array, 
                decompressed, 
                original_size, 
                len(compressed)
            )
            
            results['methods']['jpeg2000'][str(level)] = {
                'status': 'success',
                'compression_ratio': metrics['compression_ratio'],
                'mse': metrics['mse'],
                'snr_degradation_db': metrics['snr_degradation_db']
            }
            
            # Save artifacts
            artifact_dir = output_base / 'lossy' / 'jpeg2000' / str(level)
            ensure_dir(artifact_dir)
            with open(artifact_dir / 'compressed.bin', 'wb') as f:
                f.write(compressed)
            with open(artifact_dir / 'params.json', 'w') as f:
                json.dump(params, f)
            
        except Exception as e:
            logger.error(f"JPEG2000 level {level} failed: {e}")
            results['methods']['jpeg2000'][str(level)] = {'status': 'failed', 'error': str(e)}
    
    return results

def main():
    """
    Main pipeline execution for User Story 2.
    Reads validated events from data/processed/validated_events/
    Outputs compressed data to data/interim/compressed/
    """
    log_step_start("US2_Compression_Pipeline")
    
    # Setup paths
    input_dir = get_path('data_processed', 'validated_events')
    output_dir = get_path('data_interim', 'compressed')
    ensure_dir(output_dir)
    
    # Ensure lossy.py has the required functions
    # (These are expected to be implemented in T020.1, T020.2, T020.3)
    try:
        from src.compression.lossy import compress_quantization, decompress_quantization
        from src.compression.lossy import compress_wavelet, decompress_wavelet
        from src.compression.lossy import compress_jpeg2000, decompress_jpeg2000
    except ImportError as e:
        logger.error("Lossy compression functions not found. Ensure T020.1-T020.3 are complete.")
        log_step_error("US2_Compression_Pipeline", str(e))
        return 1
    
    # Load all validated events
    event_files = list(input_dir.glob('*.json'))
    if not event_files:
        logger.error(f"No validated events found in {input_dir}")
        log_step_error("US2_Compression_Pipeline", "No input data found")
        return 1
    
    logger.info(f"Found {len(event_files)} validated events to process")
    
    all_results = []
    success_count = 0
    failure_count = 0
    
    for event_file in event_files:
        event_id = event_file.stem
        try:
            event_data = load_validated_event(event_file)
            results = process_single_event(event_data, event_id, output_dir)
            all_results.append(results)
            success_count += 1
            logger.info(f"Completed {event_id}")
        except Exception as e:
            logger.error(f"Failed to process {event_id}: {e}")
            failure_count += 1
            all_results.append({
                'event_id': event_id,
                'status': 'failed',
                'error': str(e)
            })
    
    # Save summary report
    summary_path = output_dir / 'compression_summary.json'
    with open(summary_path, 'w') as f:
        json.dump({
            'total_events': len(event_files),
            'successful': success_count,
            'failed': failure_count,
            'results': all_results
        }, f, indent=2)
    
    logger.info(f"Compression pipeline complete. Summary saved to {summary_path}")
    log_metric("US2_Compression_Pipeline", "events_processed", success_count)
    log_metric("US2_Compression_Pipeline", "events_failed", failure_count)
    log_step_complete("US2_Compression_Pipeline")
    
    return 0 if failure_count == 0 else 1

if __name__ == '__main__':
    sys.exit(main())