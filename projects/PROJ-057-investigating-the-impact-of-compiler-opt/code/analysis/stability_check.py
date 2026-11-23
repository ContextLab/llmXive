"""
Stability analysis module for comparing optimized kernel outputs against high-precision references.

Implements L2 relative error and Maximum Absolute Difference calculations.
"""
import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
import struct
import hashlib

# Setup logging
def setup_logging():
    """Configure logging for the stability analysis module."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/stability_check.log')
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

@dataclass
class StabilityResult:
    """Data class to hold stability analysis results."""
    config_id: str
    kernel_type: str
    l2_error: float
    max_diff: float
    status: str
    tensor_dim: str
    downsampled: bool
    timestamp: str

def load_raw_logs(log_dir: Path) -> List[Dict[str, Any]]:
    """
    Load raw execution logs from JSONL files.
    
    Args:
        log_dir: Path to directory containing JSONL log files
        
    Returns:
        List of log entries
    """
    logs = []
    log_files = list(log_dir.glob('*.jsonl'))
    
    if not log_files:
        logger.warning(f"No JSONL files found in {log_dir}")
        return logs
        
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))
        except Exception as e:
            logger.error(f"Error reading {log_file}: {e}")
            
    return logs

def detect_nan_in_tensor(tensor_data: np.ndarray) -> bool:
    """
    Detect NaN values in tensor data.
    
    Args:
        tensor_data: Numpy array of tensor values
        
    Returns:
        True if NaN detected, False otherwise
    """
    return np.any(np.isnan(tensor_data))

def load_tensor_from_binary(file_path: Path) -> np.ndarray:
    """
    Load tensor data from binary file.
    
    Args:
        file_path: Path to binary file containing float32 tensor
        
    Returns:
        Numpy array of tensor values
    """
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
            # Assuming float32 (4 bytes)
            num_elements = len(data) // 4
            tensor = np.frombuffer(data, dtype=np.float32)
            return tensor
    except Exception as e:
        logger.error(f"Error loading tensor from {file_path}: {e}")
        raise

def calculate_l2_relative_error(reference: np.ndarray, 
                                optimized: np.ndarray) -> float:
    """
    Calculate L2 relative error between reference and optimized tensors.
    
    L2 relative error = ||reference - optimized||_2 / ||reference||_2
    
    Args:
        reference: Reference tensor (high-precision)
        optimized: Optimized tensor output
        
    Returns:
        L2 relative error as float
    """
    if reference.shape != optimized.shape:
        raise ValueError(f"Shape mismatch: {reference.shape} vs {optimized.shape}")
        
    diff = reference - optimized
    l2_diff = np.linalg.norm(diff)
    l2_ref = np.linalg.norm(reference)
    
    # Handle case where reference norm is zero
    if l2_ref == 0:
        if l2_diff == 0:
            return 0.0
        else:
            # Infinite error if reference is zero but diff is not
            return float('inf')
            
    return float(l2_diff / l2_ref)

def calculate_max_absolute_difference(reference: np.ndarray, 
                                     optimized: np.ndarray) -> float:
    """
    Calculate maximum absolute difference between reference and optimized tensors.
    
    Max diff = max(|reference - optimized|)
    
    Args:
        reference: Reference tensor (high-precision)
        optimized: Optimized tensor output
        
    Returns:
        Maximum absolute difference as float
    """
    if reference.shape != optimized.shape:
        raise ValueError(f"Shape mismatch: {reference.shape} vs {optimized.shape}")
        
    diff = np.abs(reference - optimized)
    return float(np.max(diff))

def process_stability(logs: List[Dict[str, Any]], 
                     reference_dir: Path,
                     output_dir: Path) -> List[StabilityResult]:
    """
    Process all logs to calculate stability metrics.
    
    Args:
        logs: List of execution log entries
        reference_dir: Directory containing reference tensors
        output_dir: Directory to save results
        
    Returns:
        List of StabilityResult objects
    """
    results = []
    
    for log_entry in logs:
        try:
            config_id = log_entry.get('config_id', 'unknown')
            kernel = log_entry.get('kernel', 'unknown')
            tensor_dim = log_entry.get('tensor_dim', 'unknown')
            downsampled = log_entry.get('downsampled', False)
            
            # Load reference tensor
            ref_file = reference_dir / f"{kernel}_{tensor_dim}.bin"
            if not ref_file.exists():
                logger.warning(f"Reference file not found: {ref_file}")
                continue
                
            reference_tensor = load_tensor_from_binary(ref_file)
            
            # Load optimized tensor from binary output path in log
            # Assuming log contains 'output_tensor_path' or similar
            output_path_str = log_entry.get('output_tensor_path')
            if not output_path_str:
                logger.warning(f"No output tensor path in log for {config_id}")
                continue
                
            output_file = Path(output_path_str)
            if not output_file.exists():
                logger.warning(f"Output file not found: {output_file}")
                continue
                
            optimized_tensor = load_tensor_from_binary(output_file)
            
            # Check for NaN
            if detect_nan_in_tensor(optimized_tensor):
                logger.warning(f"NaN detected in {config_id} ({kernel})")
                continue
                
            if detect_nan_in_tensor(reference_tensor):
                logger.warning(f"NaN detected in reference for {config_id} ({kernel})")
                continue
                
            # Calculate metrics
            l2_error = calculate_l2_relative_error(reference_tensor, optimized_tensor)
            max_diff = calculate_max_absolute_difference(reference_tensor, optimized_tensor)
            
            # Determine status
            status = 'stable' if (l2_error <= 1e-5 and max_diff <= 1e-5) else 'unstable'
            
            result = StabilityResult(
                config_id=config_id,
                kernel_type=kernel,
                l2_error=l2_error,
                max_diff=max_diff,
                status=status,
                tensor_dim=tensor_dim,
                downsampled=downsampled,
                timestamp=log_entry.get('timestamp', '')
            )
            
            results.append(result)
            logger.info(f"Processed {config_id}: L2={l2_error:.2e}, MaxDiff={max_diff:.2e}, Status={status}")
            
        except Exception as e:
            logger.error(f"Error processing log entry {log_entry.get('config_id')}: {e}")
            
    return results

def save_stable_logs(results: List[StabilityResult], output_path: Path):
    """
    Save stable results to CSV.
    
    Args:
        results: List of StabilityResult objects
        output_path: Path to output CSV file
    """
    import pandas as pd
    
    stable_results = [r for r in results if r.status == 'stable']
    
    if not stable_results:
        logger.warning("No stable results to save")
        return
        
    df = pd.DataFrame([asdict(r) for r in stable_results])
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(stable_results)} stable results to {output_path}")

def save_unstable_audit(results: List[StabilityResult], output_path: Path):
    """
    Save unstable results for audit purposes.
    
    Args:
        results: List of StabilityResult objects
        output_path: Path to output CSV file
    """
    import pandas as pd
    
    unstable_results = [r for r in results if r.status == 'unstable']
    
    if not unstable_results:
        logger.info("No unstable results to audit")
        return
        
    df = pd.DataFrame([asdict(r) for r in unstable_results])
    df.to_csv(output_path, index=False)
    logger.info(f"Audited {len(unstable_results)} unstable results at {output_path}")

def main():
    """Main entry point for stability analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Stability analysis for compiler optimizations')
    parser.add_argument('--log-dir', type=str, default='data/intermediates/raw_logs',
                      help='Directory containing raw execution logs')
    parser.add_argument('--ref-dir', type=str, default='data/raw/references',
                      help='Directory containing reference tensors')
    parser.add_argument('--output-dir', type=str, default='data/results',
                      help='Directory to save results')
    parser.add_argument('--detect-nan', action='store_true',
                      help='Only perform NaN detection and filtering')
    
    args = parser.parse_args()
    
    log_dir = Path(args.log_dir)
    ref_dir = Path(args.ref_dir)
    output_dir = Path(args.output_dir)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load raw logs
    logger.info(f"Loading logs from {log_dir}")
    logs = load_raw_logs(log_dir)
    logger.info(f"Loaded {len(logs)} log entries")
    
    if not logs:
        logger.error("No logs found. Exiting.")
        return
        
    if args.detect_nan:
        # Only detect NaN and create filtered list
        stable_logs = []
        for log in logs:
            output_path_str = log.get('output_tensor_path')
            if output_path_str:
                output_file = Path(output_path_str)
                if output_file.exists():
                    tensor = load_tensor_from_binary(output_file)
                    if not detect_nan_in_tensor(tensor):
                        stable_logs.append(log)
                    
        # Save filtered stable runs
        filtered_path = output_dir / 'filtered_stable_runs.csv'
        import pandas as pd
        df = pd.DataFrame(stable_logs)
        df.to_csv(filtered_path, index=False)
        logger.info(f"Saved {len(stable_logs)} stable runs to {filtered_path}")
        return
        
    # Full stability analysis
    results = process_stability(logs, ref_dir, output_dir)
    
    # Save results
    stable_path = output_dir / 'stability_metrics.csv'
    save_stable_logs(results, stable_path)
    
    audit_path = output_dir / 'unstable_audit.csv'
    save_unstable_audit(results, audit_path)
    
    logger.info(f"Stability analysis complete. {len(results)} results processed.")

if __name__ == '__main__':
    main()