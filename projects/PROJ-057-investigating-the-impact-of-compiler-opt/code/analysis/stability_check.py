import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
import csv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StabilityResult:
    config_id: str
    kernel_type: str
    l2_error: float
    max_diff: float
    status: str  # "stable", "unstable", "nan"
    raw_log_path: Optional[str] = None

def load_raw_logs(log_dir: Path) -> List[Dict[str, Any]]:
    """Load all .jsonl files from the raw logs directory."""
    logs = []
    if not log_dir.exists():
        logger.warning(f"Raw log directory {log_dir} does not exist.")
        return logs
    
    for file_path in log_dir.glob("*.jsonl"):
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON line in {file_path}")
    return logs

def detect_nan_in_tensor(tensor_data: List[float]) -> bool:
    """Check if the tensor data contains NaN or Inf values."""
    try:
        arr = np.array(tensor_data, dtype=np.float32)
        return bool(np.any(~np.isfinite(arr)))
    except Exception as e:
        logger.error(f"Error checking tensor for NaN: {e}")
        return True # Treat as unstable if we can't check

def calculate_l2_relative_error(reference: List[float], computed: List[float]) -> float:
    """Calculate L2 relative error: ||ref - comp||_2 / ||ref||_2"""
    try:
        ref_arr = np.array(reference, dtype=np.float64)
        comp_arr = np.array(computed, dtype=np.float64)
        
        diff = ref_arr - comp_arr
        l2_diff = np.linalg.norm(diff)
        l2_ref = np.linalg.norm(ref_arr)
        
        if l2_ref == 0:
            return 0.0 if l2_diff == 0 else float('inf')
        
        return float(l2_diff / l2_ref)
    except Exception as e:
        logger.error(f"Error calculating L2 error: {e}")
        return float('inf')

def calculate_max_absolute_difference(reference: List[float], computed: List[float]) -> float:
    """Calculate Maximum Absolute Difference: max(|ref - comp|)"""
    try:
        ref_arr = np.array(reference, dtype=np.float64)
        comp_arr = np.array(computed, dtype=np.float64)
        return float(np.max(np.abs(ref_arr - comp_arr)))
    except Exception as e:
        logger.error(f"Error calculating max diff: {e}")
        return float('inf')

def process_stability(raw_logs: List[Dict[str, Any]], reference_dir: Path) -> List[StabilityResult]:
    """
    Process raw logs, compare against reference, detect NaNs, and apply threshold flagging.
    
    Threshold: error > 1e-5 is considered unstable.
    NaNs are detected and marked as 'nan' status.
    Unstable runs are excluded from statistical analysis but recorded in audit.
    """
    results = []
    
    # Load reference data assuming a mapping or structure. 
    # For this implementation, we assume reference files are named based on config_id and kernel_type
    # or we load them from a specific reference mapping if available.
    # Given the task context, we assume reference data is available or generated previously.
    # Here we simulate loading reference based on config_id if it exists in reference_dir.
    
    # In a real scenario, reference data might be pre-loaded or fetched by config_id.
    # We will attempt to find reference data.
    
    for log_entry in raw_logs:
        config_id = log_entry.get('config_id')
        kernel_type = log_entry.get('kernel_type')
        output_tensor = log_entry.get('output_tensor') # List of floats
        
        if not config_id or not kernel_type or not output_tensor:
            logger.warning(f"Skipping malformed log entry: {log_entry}")
            continue

        # Find reference data
        # Assuming reference files are stored as reference_<kernel_type>_<config_id>.bin or similar
        # For this task, we assume a helper function or existing structure provides the reference.
        # Since T006 was rejected for missing implementation, we assume reference data is now available
        # via a standard path or we must generate it if missing (but T022 depends on T006 being done).
        # We will assume reference data is in `data/raw/reference_<kernel_type>_<config_id>.npy` or similar.
        
        # Let's construct a potential reference path
        ref_path = reference_dir / f"reference_{kernel_type}_{config_id}.npy"
        if not ref_path.exists():
            # Fallback: try to load from a generic reference if available, or skip
            # For this specific task T022, we focus on the logic once data is present.
            # We will assume the reference exists for the sake of the logic implementation.
            # If not, we mark as unstable/missing.
            logger.error(f"Reference data not found for {config_id} {kernel_type}. Marking as unstable.")
            results.append(StabilityResult(
                config_id=config_id,
                kernel_type=kernel_type,
                l2_error=float('inf'),
                max_diff=float('inf'),
                status="unstable",
                raw_log_path=log_entry.get('file_path')
            ))
            continue

        try:
            ref_tensor = np.load(ref_path).tolist()
        except Exception as e:
            logger.error(f"Failed to load reference for {config_id}: {e}")
            results.append(StabilityResult(
                config_id=config_id,
                kernel_type=kernel_type,
                l2_error=float('inf'),
                max_diff=float('inf'),
                status="unstable",
                raw_log_path=log_entry.get('file_path')
            ))
            continue

        # 1. Detect NaNs
        if detect_nan_in_tensor(output_tensor):
            logger.warning(f"NaN detected in {config_id} ({kernel_type}). Marking as 'nan'.")
            results.append(StabilityResult(
                config_id=config_id,
                kernel_type=kernel_type,
                l2_error=float('inf'),
                max_diff=float('inf'),
                status="nan",
                raw_log_path=log_entry.get('file_path')
            ))
            continue

        # 2. Calculate Errors
        l2_err = calculate_l2_relative_error(ref_tensor, output_tensor)
        max_diff = calculate_max_absolute_difference(ref_tensor, output_tensor)

        # 3. Threshold Flagging (error > 1e-5)
        # Note: Using a combined check or specific metric. The task says "error > 1e-5".
        # We will treat L2 relative error > 1e-5 as unstable.
        threshold = 1e-5
        status = "stable"
        
        if l2_err > threshold:
            status = "unstable"
            logger.info(f"Threshold exceeded for {config_id} ({kernel_type}). L2 Error: {l2_err} > {threshold}")
        
        results.append(StabilityResult(
            config_id=config_id,
            kernel_type=kernel_type,
            l2_error=l2_err,
            max_diff=max_diff,
            status=status,
            raw_log_path=log_entry.get('file_path')
        ))

    return results

def save_stable_logs(results: List[StabilityResult], output_dir: Path):
    """Save results that are 'stable' to a CSV or JSON file for statistical analysis."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "stable_results.jsonl"
    
    with open(output_file, 'w') as f:
        for res in results:
            if res.status == "stable":
                f.write(json.dumps(asdict(res)) + '\n')
    
    logger.info(f"Saved {len([r for r in results if r.status == 'stable'])} stable results to {output_file}")

def save_unstable_audit(results: List[StabilityResult], output_dir: Path):
    """Save results that are 'unstable' or 'nan' to an audit log."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "unstable_audit.jsonl"
    
    with open(output_file, 'w') as f:
        for res in results:
            if res.status in ["unstable", "nan"]:
                f.write(json.dumps(asdict(res)) + '\n')
    
    logger.info(f"Saved {len([r for r in results if r.status in ['unstable', 'nan']])} unstable/nan results to {output_file}")

def main():
    """Main entry point for stability check processing."""
    # Paths
    base_dir = Path(__file__).resolve().parent.parent
    raw_logs_dir = base_dir / "benchmarks" / ".." / "data" / "intermediates" / "raw_logs"
    reference_dir = base_dir / "data" / "raw"
    results_dir = base_dir / "data" / "results"
    
    raw_logs_dir = Path(str(raw_logs_dir).replace("/..", "")) # Normalize if needed
    if not raw_logs_dir.exists():
        logger.error(f"Raw logs directory not found: {raw_logs_dir}")
        return

    logger.info(f"Processing raw logs from {raw_logs_dir}")
    logs = load_raw_logs(raw_logs_dir)
    if not logs:
        logger.warning("No raw logs found.")
        return

    logger.info(f"Loaded {len(logs)} log entries.")
    results = process_stability(logs, reference_dir)
    
    save_stable_logs(results, results_dir)
    save_unstable_audit(results, results_dir)

    # Also generate the metrics CSV as required by T023 (pre-emptively or as part of flow)
    # T022 says "recording as stability failure", which is done in audit.
    # T023 will aggregate. We can output the full list here too for T023 to pick up.
    full_metrics_file = results_dir / "stability_metrics.csv"
    with open(full_metrics_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['config_id', 'kernel_type', 'l2_error', 'max_diff', 'status'])
        writer.writeheader()
        for res in results:
            writer.writerow({
                'config_id': res.config_id,
                'kernel_type': res.kernel_type,
                'l2_error': res.l2_error,
                'max_diff': res.max_diff,
                'status': res.status
            })
    logger.info(f"Saved full stability metrics to {full_metrics_file}")

if __name__ == "__main__":
    main()