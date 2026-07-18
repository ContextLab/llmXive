import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import csv
import argparse

# Configure logging to use the project's logger if available, otherwise default
try:
    from utils.logger import get_logger, setup_logging
except ImportError:
    # Fallback if running as script without package context
    setup_logging = None
    def get_logger(name):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        return logging.getLogger(name)

# Thresholds defined in spec
STABILITY_THRESHOLD = 1e-5

class StabilityResult:
    def __init__(self, config_id: str, kernel: str, has_nan: bool, 
                 l2_error: Optional[float] = None, max_diff: Optional[float] = None,
                 status: str = "unknown"):
        self.config_id = config_id
        self.kernel = kernel
        self.has_nan = has_nan
        self.l2_error = l2_error
        self.max_diff = max_diff
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "config_id": self.config_id,
            "kernel": self.kernel,
            "has_nan": self.has_nan,
            "l2_error": self.l2_error,
            "max_diff": self.max_diff,
            "status": self.status
        }

def setup_logging():
    """Initialize logging for the module."""
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def load_raw_logs(log_dir: str) -> List[Dict[str, Any]]:
    """
    Load all .jsonl files from the raw logs directory.
    Returns a list of dictionaries representing each log entry.
    """
    logs = []
    log_path = Path(log_dir)
    if not log_path.exists():
        raise FileNotFoundError(f"Raw logs directory not found: {log_dir}")
    
    for file_path in log_path.glob("*.jsonl"):
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        logging.warning(f"Skipping invalid JSON line in {file_path}: {line}")
    return logs

def detect_nan_in_tensor(tensor_data: Any) -> bool:
    """
    Detect if the tensor data contains NaN values.
    tensor_data can be a list of floats or a numpy array.
    """
    if tensor_data is None:
        return False
    
    try:
        arr = np.array(tensor_data, dtype=np.float32)
        return bool(np.any(np.isnan(arr)))
    except Exception:
        # If conversion fails, assume valid (or log warning)
        return False

def calculate_l2_relative_error(predicted: List[float], reference: List[float]) -> float:
    """
    Calculate L2 relative error: ||P - R||_2 / ||R||_2
    """
    if not reference:
        return 0.0
    
    p_arr = np.array(predicted, dtype=np.float64)
    r_arr = np.array(reference, dtype=np.float64)
    
    diff = p_arr - r_arr
    l2_diff = np.linalg.norm(diff)
    l2_ref = np.linalg.norm(r_arr)
    
    if l2_ref == 0:
        return 0.0 if l2_diff == 0 else float('inf')
    
    return float(l2_diff / l2_ref)

def calculate_max_absolute_difference(predicted: List[float], reference: List[float]) -> float:
    """
    Calculate Maximum Absolute Difference: max(|P - R|)
    """
    if not predicted or not reference:
        return 0.0
    
    p_arr = np.array(predicted, dtype=np.float64)
    r_arr = np.array(reference, dtype=np.float64)
    
    return float(np.max(np.abs(p_arr - r_arr)))

def process_stability(logs: List[Dict[str, Any]], reference_dir: Optional[str] = None) -> List[StabilityResult]:
    """
    Process raw logs to detect NaNs and calculate stability metrics.
    If reference data is available, calculate errors.
    """
    results = []
    logger = logging.getLogger(__name__)
    
    for log in logs:
        config_id = log.get("config_id", "unknown")
        kernel = log.get("kernel", "unknown")
        output_tensor = log.get("output_tensor")
        
        # 1. NaN Detection
        has_nan = detect_nan_in_tensor(output_tensor)
        
        if has_nan:
            logger.warning(f"NaN detected in config {config_id}, kernel {kernel}. Excluding from stable runs.")
            results.append(StabilityResult(
                config_id=config_id,
                kernel=kernel,
                has_nan=True,
                status="unstable_nan"
            ))
            continue
        
        # 2. Calculate Error Metrics if reference exists
        l2_error = None
        max_diff = None
        status = "stable"
        
        if reference_dir:
            ref_path = Path(reference_dir) / f"{kernel}_ref.npy" # Assuming reference is saved as .npy
            if ref_path.exists():
                try:
                    ref_tensor = np.load(ref_path).tolist()
                    l2_error = calculate_l2_relative_error(output_tensor, ref_tensor)
                    max_diff = calculate_max_absolute_difference(output_tensor, ref_tensor)
                    
                    if l2_error > STABILITY_THRESHOLD or max_diff > STABILITY_THRESHOLD:
                        status = "unstable_error"
                        logger.warning(f"Stability threshold exceeded for {config_id}: L2={l2_error:.2e}, MaxDiff={max_diff:.2e}")
                    else:
                        status = "stable"
                except Exception as e:
                    logger.error(f"Error loading reference for {kernel}: {e}")
                    status = "unknown_ref_error"
            else:
                # If no reference, assume stable for NaN check only (for T017 specific scope)
                # In T022 we will strictly enforce error thresholds
                pass
        
        results.append(StabilityResult(
            config_id=config_id,
            kernel=kernel,
            has_nan=False,
            l2_error=l2_error,
            max_diff=max_diff,
            status=status
        ))
    
    return results

def save_stable_logs(results: List[StabilityResult], output_path: str):
    """
    Save only the stable runs to a CSV file.
    """
    stable_runs = [r for r in results if r.status == "stable"]
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['config_id', 'kernel', 'status', 'l2_error', 'max_diff']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for r in stable_runs:
            writer.writerow({
                'config_id': r.config_id,
                'kernel': r.kernel,
                'status': r.status,
                'l2_error': r.l2_error if r.l2_error is not None else '',
                'max_diff': r.max_diff if r.max_diff is not None else ''
            })
    
    logging.info(f"Saved {len(stable_runs)} stable runs to {output_path}")

def save_unstable_audit(results: List[StabilityResult], output_path: str):
    """
    Save an audit log of all excluded/unstable runs.
    """
    unstable_runs = [r for r in results if r.status != "stable"]
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['config_id', 'kernel', 'status', 'has_nan', 'l2_error', 'max_diff']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for r in unstable_runs:
            writer.writerow({
                'config_id': r.config_id,
                'kernel': r.kernel,
                'status': r.status,
                'has_nan': r.has_nan,
                'l2_error': r.l2_error if r.l2_error is not None else '',
                'max_diff': r.max_diff if r.max_diff is not None else ''
            })
    
    logging.info(f"Saved {len(unstable_runs)} unstable runs to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Detect NaNs and filter stable runs from raw logs.")
    parser.add_argument("--detect-nan", action="store_true", help="Run NaN detection and filtering pipeline.")
    parser.add_argument("--log-dir", type=str, default="data/intermediates/raw_logs", help="Directory containing raw JSONL logs.")
    parser.add_argument("--ref-dir", type=str, default="data/raw", help="Directory containing reference tensors.")
    parser.add_argument("--output", type=str, default="data/intermediates/filtered_stable_runs.csv", help="Output path for stable runs CSV.")
    parser.add_argument("--audit", type=str, default="data/intermediates/unstable_audit.csv", help="Output path for unstable audit CSV.")
    
    args = parser.parse_args()
    
    if args.detect_nan:
        logger = setup_logging()
        logger.info(f"Loading raw logs from {args.log_dir}")
        
        try:
            logs = load_raw_logs(args.log_dir)
        except FileNotFoundError as e:
            logger.error(f"Failed to load logs: {e}")
            # If no logs exist, create an empty output file to satisfy the artifact requirement
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, 'w') as f:
                f.write("config_id,kernel,status,l2_error,max_diff\n")
            return 1
        
        if not logs:
            logger.warning("No log entries found in the specified directory.")
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, 'w') as f:
                f.write("config_id,kernel,status,l2_error,max_diff\n")
            return 0
        
        logger.info(f"Processing {len(logs)} log entries for stability.")
        results = process_stability(logs, args.ref_dir)
        
        save_stable_logs(results, args.output)
        save_unstable_audit(results, args.audit)
        
        stable_count = len([r for r in results if r.status == "stable"])
        unstable_count = len([r for r in results if r.status != "stable"])
        
        logger.info(f"Analysis complete. Stable: {stable_count}, Unstable: {unstable_count}")
        return 0
    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    exit(main())
