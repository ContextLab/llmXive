"""
Speed Metrics Analysis Module for T036c.

Calculates the speed-up factor of the GNN model compared to the DFT benchmark.
Loads cached DFT times and measured GNN inference times to compute the ratio.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Returns the project root directory (parent of 'code')."""
    # Assuming this script is run from the project root or 'code' directory
    current = Path(__file__).resolve()
    # Navigate up to find the root where 'data' and 'src' are siblings
    # Based on the structure: code/src/analysis/speed_metrics.py
    # Project root is likely the parent of 'code'
    return current.parent.parent.parent

def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Safely loads a JSON file."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {file_path}: {e}")
        return None

def load_cached_dft_time() -> Optional[float]:
    """
    Loads the DFT reference time from the benchmark cache.
    Tries dft_benchmark_cache.json first, then falls back to speed_constraint_check.json if needed.
    """
    project_root = get_project_root()
    dft_cache_path = project_root / "data" / "results" / "dft_benchmark_cache.json"
    speed_check_path = project_root / "data" / "results" / "speed_constraint_check.json"
    
    # Priority 1: DFT Benchmark Cache (T036b)
    cache_data = load_json_file(dft_cache_path)
    if cache_data and "reference_time_seconds" in cache_data:
        logger.info(f"Loaded DFT reference time from {dft_cache_path}: {cache_data['reference_time_seconds']}s")
        return cache_data["reference_time_seconds"]
    
    # Priority 2: Speed Constraint Check (T025b) - if it contains timing info
    # Note: T025b usually contains time_per_sample, not total reference time.
    # However, if T036b was skipped due to scarcity, we might need to handle this.
    # The task description says: "Load dft_benchmark_cache.json OR speed_constraint_check.json".
    # We assume if dft_benchmark_cache exists, we use it. If not, we check if speed_constraint_check
    # has a relevant 'reference_time' or similar.
    speed_data = load_json_file(speed_check_path)
    if speed_data and "reference_time_seconds" in speed_data:
        logger.info(f"Loaded DFT reference time from {speed_check_path}: {speed_data['reference_time_seconds']}s")
        return speed_data["reference_time_seconds"]
    
    logger.warning("Could not find DFT reference time in either cache file.")
    return None

def load_gnn_inference_time() -> Optional[float]:
    """
    Loads the GNN inference time.
    The T025b task (speed constraint check) produces 'time_per_sample' and 'total_time' implicitly or explicitly.
    We look for 'total_time_seconds' in speed_constraint_check.json or calculate from per-sample if total samples known.
    For T036c, we need the total time to predict the test set to compare with the single DFT sample time?
    Actually, the spec says: "speedup_factor = reference_time_seconds / gnn_time".
    Usually, this compares single-sample DFT time vs single-sample GNN time.
    T025b calculates time_per_sample. We will use that as gnn_time.
    """
    project_root = get_project_root()
    speed_check_path = project_root / "data" / "results" / "speed_constraint_check.json"
    
    speed_data = load_json_file(speed_check_path)
    if speed_data and "time_per_sample" in speed_data:
        logger.info(f"Loaded GNN time_per_sample from {speed_check_path}: {speed_data['time_per_sample']}s")
        return speed_data["time_per_sample"]
    
    # Fallback: check if total_time and num_samples are available
    if speed_data and "total_time_seconds" in speed_data and "num_samples" in speed_data:
        if speed_data["num_samples"] > 0:
            time_per_sample = speed_data["total_time_seconds"] / speed_data["num_samples"]
            logger.info(f"Calculated GNN time_per_sample from {speed_check_path}: {time_per_sample}s")
            return time_per_sample

    logger.warning("Could not find GNN inference time in speed_constraint_check.json.")
    return None

def calculate_speedup(dft_time: float, gnn_time: float) -> float:
    """Calculates the speed-up factor."""
    if gnn_time <= 0:
        logger.error("GNN time must be positive to calculate speedup.")
        raise ValueError("GNN time must be positive.")
    return dft_time / gnn_time

def run_speed_metrics_analysis() -> Dict[str, Any]:
    """
    Main logic for T036c: Calculate speed-up factor.
    1. Load DFT reference time.
    2. Load GNN inference time.
    3. Calculate speedup.
    4. Write results.
    """
    dft_time = load_cached_dft_time()
    gnn_time = load_gnn_inference_time()
    
    result = {
        "dft_reference_time_seconds": dft_time,
        "gnn_time_per_sample_seconds": gnn_time,
        "speedup_factor": None,
        "status": "N/A"
    }
    
    if dft_time is not None and gnn_time is not None:
        try:
            speedup = calculate_speedup(dft_time, gnn_time)
            result["speedup_factor"] = speedup
            result["status"] = "PASS"
            logger.info(f"Calculated speedup factor: {speedup:.2f}x")
        except ValueError as e:
            result["status"] = "FAIL"
            result["error"] = str(e)
            logger.error(f"Failed to calculate speedup: {e}")
    else:
        result["status"] = "MISSING_DATA"
        if dft_time is None:
            result["missing"] = "dft_reference_time"
        if gnn_time is None:
            result["missing"] = result.get("missing", []) + ["gnn_inference_time"]
        logger.warning("Cannot calculate speedup due to missing data.")
    
    return result

def save_metrics(result: Dict[str, Any], output_path: Path) -> None:
    """Saves the speed metrics result to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Saved speed metrics to {output_path}")

def main() -> int:
    """Entry point for the script."""
    try:
        project_root = get_project_root()
        output_path = project_root / "data" / "results" / "speed_metrics.json"
        
        logger.info("Starting Speed Metrics Analysis (T036c)...")
        
        result = run_speed_metrics_analysis()
        save_metrics(result, output_path)
        
        logger.info("Speed Metrics Analysis completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Critical error in Speed Metrics Analysis: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
